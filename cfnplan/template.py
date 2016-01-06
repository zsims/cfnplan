import json
from enum import Enum


class LogicalIdNotFoundError(Exception):
    def __init__(self, logical_id):
        self.logical_id = logical_id


class ResourceNotFoundError(Exception):
    def __init__(self, logical_id):
        self.logical_id = logical_id


class ElementType(Enum):
    """
    Types of cloud formation elements, includes resources, parameters, simple types and functions
    """
    raw = 0
    resource = 1
    function = 2
    list = 3
    key = 4
    property = 5
    parameter = 6
    pseudo_parameter = 7


class Element(object):
    """
    Represents a value in cloud formation, may be simple or complex like a function
    """
    def __init__(self, element_type):
        self.element_type = element_type
        self.children = []
        self.dependencies = []

    def add_dependency(self, element):
        self.dependencies.append(element)

    def add_children(self, elements):
        self.children.extend(elements)

    def all_dependencies(self):
        """
        Returns a list of all the dependencies, including those children have.
        """
        visited = set()

        def visit(level, item):
            for d in item.dependencies:
                visited.add(d)
            for c in item.children:
                visit(level + 1, c)

        visit(0, self)
        return visited

    def visit_dependencies(self, callback):
        visited = set()

        def visit(level, item):
            is_visited = item in visited
            visited.add(item)
            callback(item, level, is_visited)
            for d in item.all_dependencies():
                visit(level + 1, d)

        visit(0, self)


class Property(Element):
    """
    Represents a property, e.g. key = value
    """
    def __init__(self, key, value):
        super(Property, self).__init__(ElementType.property)
        self.key = key
        self.value = value


class Key(Element):
    """
    Represents a key, e.g. "key": {"child_property": "property_value"}
    """
    def __init__(self, key):
        super(Key, self).__init__(ElementType.key)
        self.key = key


class Function(Element):
    """
    Represents an intrinsic function per http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html
    """
    def __init__(self, name):
        super(Function, self).__init__(ElementType.function)
        self.name = name


class LogicalElement(Element):
    """
    A logical element that can be referenced by its logical id (or name), e.g a parameter, pseduo parameter or resource
    """
    def __init__(self, logical_id, element_type):
        super(LogicalElement, self).__init__(element_type)
        self.logical_id = logical_id


class Resource(LogicalElement):
    """
    Represents a resource per http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resources-section-structure.html
    """
    def __init__(self, logical_id, resource_type):
        super(Resource, self).__init__(logical_id, ElementType.resource)
        self.resource_type = resource_type

    def __str__(self):
        return '%s (%s)' % (self.logical_id, self.resource_type)


class Parameter(LogicalElement):
    """
    Represents a resource per http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html
    """
    def __init__(self, logical_id):
        super(Parameter, self).__init__(logical_id, ElementType.parameter)
        self.logical_id = logical_id

    def __str__(self):
        return '%s' % self.logical_id


class PseudoParameter(LogicalElement):
    def __init__(self, logical_id):
        super(PseudoParameter, self).__init__(logical_id, ElementType.pseudo_parameter)
        self.logical_id = logical_id

    def __str__(self):
        return '%s' % self.logical_id


class Template(object):
    """
    Represents an entire template.
    """
    def __init__(self):
        self.elements = []

    def get_by_logical_id(self, logical_name):
        """
        Returns the template item associated with the given logical name.
        """
        # Only resources or parameters
        matching = [e for e in self.elements if isinstance(e, LogicalElement) and e.logical_id == logical_name]
        if not matching:
            raise LogicalIdNotFoundError(logical_name)
        return matching[0]

    def get_resource(self, logical_id):
        logical_item = self.get_by_logical_id(logical_id)
        if not isinstance(logical_item, Resource):
            raise ResourceNotFoundError(logical_id)
        return logical_item

    def add_element(self, element):
        self.elements.append(element)

    @staticmethod
    def parse_file(path):
        parser = TemplateParser()
        parser.parse_file(path)
        return parser.template

    def print_dependencies(self):
        def log_element(element, level, visited):
            if not visited:
                indent = ' ' * (level * 2)
                print '%s<== %s' % (indent, element)

        for e in self.elements:
            e.visit_dependencies(log_element)


class TemplateParser(object):
    """
    Parses template JSON into a template
    """
    def __init__(self):
        self.template = Template()
        self.known_functions = {
            'Ref': self._handle_function_ref,
            'Fn::GetAtt': self._handle_function_get_att,
            'Fn::Base64': self._handle_function,
            'Fn::FindInMap': self._handle_function,
            'Fn::GetAZs': self._handle_function,
            'Fn::Join': self._handle_function,
            'Fn::Select': self._handle_function,
        }

    def _parse_parameters(self, document):
        for k, v in document['Parameters'].iteritems():
            self.template.add_element(Parameter(k))

    def _add_pseudo_parameters(self):
        parameters = [
            'AWS::AccountId',
            'AWS::NotificationARNs',
            'AWS::NoValue',
            'AWS::Region',
            'AWS::StackId',
            'AWS::StackName'
        ]
        for p in parameters:
            self.template.add_element(PseudoParameter(p))

    def parse_file(self, path):
        d = json.load(open(path))
        self._add_pseudo_parameters()
        self._parse_parameters(d)
        self._parse_resources(d)

    def _handle_function_ref(self, function, logical_name):
        """
        Handles Ref: ...
        """
        # Ref can be to a parameter, resource or pseudo parameter
        item = self.template.get_by_logical_id(logical_name)
        function.add_dependency(item)

    def _handle_function_get_att(self, function, values):
        """
        Handle GetAtt functions which can reference other logical items
        """
        item = self.template.get_by_logical_id(values[0])
        function.add_dependency(item)
        function.add_children(self._handle_value(None, values))

    def _handle_function(self, function, values):
        """
        Handles remaining intrinsic functions
        """
        function.add_children(self._handle_value(None, values))

    def _handle_value(self, key, value):
        if isinstance(value, basestring) or isinstance(value, int) or isinstance(bool, int):
            return [Property(key, value)]
        elif isinstance(value, list):
            s = Element(ElementType.list)
            i = 0
            for nested_value in value:
                children = self._handle_value(i, nested_value)
                s.add_children(children)
                i += 1
            return [s]
        elif isinstance(value, dict):
            d = Key(key)
            for vk, vv in value.iteritems():
                if vk in self.known_functions:
                    f = Function(vk)
                    handler = self.known_functions[vk]
                    handler(f, vv)
                    d.add_children([f])
                else:
                    d.add_children(self._handle_value(vk, vv))
            return [d]

    def _parse_resource(self, resource, raw):
        if not 'Properties' in raw:
            return

        for pk, pv in raw.iteritems():
            children = self._handle_value(pk, pv)
            resource.add_children(children)

            # Handle a dependency on another resource
            if pk == 'DependsOn':
                r = self.template.get_resource(pv)
                resource.add_dependency(r)

    def _parse_resources(self, document):
        resources = document['Resources']
        # resources can depend on each other so create the resources ahead of time
        for logical_id, raw in resources.iteritems():
            self.template.add_element(Resource(logical_id, raw['Type']))

        for k, v in resources.items():
            r = self.template.get_resource(k)
            self._parse_resource(r, v)

