import json
from enum import Enum


class LogicalIdNotFoundError(Exception):
    def __init__(self, logical_id):
        self.logical_id = logical_id


class TypedLogicalIdNotFoundError(Exception):
    def __init__(self, logical_id, logical_type):
        self.logical_id = logical_id
        self.logical_type = logical_type


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
    metadata = 8
    mapping = 9
    condition = 10
    output = 11


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

    def add_child(self, element):
        self.children.append(element)

    def add_children(self, elements):
        self.children.extend(elements)

    def get_all_children(self):
        visited = []

        def visit(item):
            visited.append(item)
            for c in item.children:
                visit(c)

        visit(self)
        return visited

    def get_all_dependencies(self):
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
            for d in item.get_all_dependencies():
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


class Metadata(Element):
    def __init__(self, key):
        super(Metadata, self).__init__(ElementType.metadata)
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

    def __str__(self):
        return '%s' % self.logical_id


class Resource(LogicalElement):
    """
    Represents a resource per http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resources-section-structure.html
    """
    def __init__(self, logical_id):
        super(Resource, self).__init__(logical_id, ElementType.resource)
        self.resource_type = None

    def __str__(self):
        return '%s (%s)' % (self.logical_id, self.resource_type)


class Parameter(LogicalElement):
    """
    Represents a resource per http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html
    """
    def __init__(self, logical_id):
        super(Parameter, self).__init__(logical_id, ElementType.parameter)


class Condition(LogicalElement):
    def __init__(self, logical_id):
        super(Condition, self).__init__(logical_id, ElementType.condition)


class PseudoParameter(LogicalElement):
    def __init__(self, logical_id):
        super(PseudoParameter, self).__init__(logical_id, ElementType.pseudo_parameter)

    def __str__(self):
        return '%s' % self.logical_id


class Mapping(LogicalElement):
    def __init__(self, logical_id):
        super(Mapping, self).__init__(logical_id, ElementType.mapping)


class Output(LogicalElement):
    def __init__(self, logical_id):
        super(Output, self).__init__(logical_id, ElementType.output)


class Template(object):
    """
    Represents an entire template.
    """
    def __init__(self):
        self.version = None
        self.description = None
        self.elements = []

        # Logical elements by key, this is a cache for elements
        self._logical_elements = {}

    def get_by_logical_id(self, logical_id):
        """
        Returns the template item associated with the given logical id.
        """
        if logical_id not in self._logical_elements:
            raise LogicalIdNotFoundError(logical_id)
        return self._logical_elements[logical_id]

    def get_by_logical_id_typed(self, logical_id, expected_type):
        logical_item = self.get_by_logical_id(logical_id)
        if not isinstance(logical_item, expected_type):
            raise TypedLogicalIdNotFoundError(logical_id, expected_type)
        return logical_item

    def get_resource(self, logical_id):
        return self.get_by_logical_id_typed(logical_id, Resource)

    def add_element(self, element):
        if isinstance(element, LogicalElement):
            self._logical_elements[element.logical_id] = element
        self.elements.append(element)

    @staticmethod
    def parse_file(path):
        parser = TemplateParser()
        parser.parse_file(path)
        return parser.template

    @staticmethod
    def parse_string(raw_string):
        parser = TemplateParser()
        parser.parse_string(raw_string)
        return parser.template


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
            'Fn::FindInMap': self._handle_function_find_in_map,
            'Fn::GetAZs': self._handle_function_get_azs,
            'Fn::Join': self._handle_function,
            'Fn::Select': self._handle_function,
            'Fn::If': self._handle_function_if,
            'Fn::And': self._handle_function,
            'Fn::Not': self._handle_function,
            'Fn::Or': self._handle_function,
            'Fn::Equals': self._handle_function,
        }

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

    def parse_string(self, raw_string):
        """
        Parses a template from a string per http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-anatomy.html
        :param raw_string: String representing the whole template
        """
        d = json.loads(raw_string)
        self._parse_json(d)

    def parse_file(self, path):
        """
        Parses a template from a file per http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-anatomy.html
        :param path: Full path to the template file to parse
        """
        d = json.load(open(path))
        self._parse_json(d)

    def _parse_json(self, document):

        # Note that order is important here, as a resource may reference a parameter or condition
        self._parse_template(document)
        self._add_pseudo_parameters()

        # First pass so we have everything in the template, and we can setup dependencies
        self._pre_create_logical_elements(document, Parameter, 'Parameters')
        # Note metadata can't be referenced (isn't a logical element)
        self._pre_create_logical_elements(document, Mapping, 'Mappings')
        self._pre_create_logical_elements(document, Condition, 'Conditions')
        self._pre_create_logical_elements(document, Resource, 'Resources')
        self._pre_create_logical_elements(document, Output, 'Outputs')

        self._parse_top_level_dict(document, Parameter, 'Parameters')
        self._parse_metadata(document)
        self._parse_top_level_dict(document, Mapping, 'Mappings')
        self._parse_top_level_dict(document, Condition, 'Conditions')
        self._parse_resources(document)
        self._parse_top_level_dict(document, Output, 'Outputs')

    def _parse_template(self, document):
        self.template.version = document.get('AWSTemplateFormatVersion')
        self.template.description = document.get('Description')

    def _pre_create_logical_elements(self, document, logical_type, key):
        if not key in document:
            return

        elements = {}
        # First pass to ensure inter-dependencies are satisfiable
        for k, v in document[key].iteritems():
            e = logical_type(k)
            self.template.add_element(e)
            elements[k] = e

    def _parse_top_level_dict(self, document, internal_type, key):
        """
        Parses a top level dictionary, e.g. the "metadata" or properties section into the template with the given internal type
        """
        if not key in document:
            return

        for k, v in document[key].iteritems():
            e = self.template.get_by_logical_id_typed(k, internal_type)
            for ek, ev in v.iteritems():
                e.add_child(self._handle_value(ek, ev))

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
        function.add_child(self._handle_value(None, values))

    def _handle_function_find_in_map(self, function, values):
        """
        Handle FindInMap functions which can reference mappings
        """
        mapping = self.template.get_by_logical_id(values[0])
        function.add_dependency(mapping)
        function.add_child(self._handle_value(None, values))

    def _handle_function_get_azs(self, function, values):
        """
        Handle GetAZs functions which can reference a region
        """
        # Supports AWS::Region or a user-entered region
        if isinstance(values, basestring) and values == "AWS::Region":
            parameter = self.template.get_by_logical_id("AWS::Region")
            function.add_dependency(parameter)
        function.add_child(self._handle_value(None, values))

    def _handle_function_if(self, function, values):
        """
        Handle Fn::If functions which references a condition, and other things.
        See http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-conditions.html#d0e97544
        """
        condition = self.template.get_by_logical_id(values[0])
        function.add_dependency(condition)
        function.add_child(self._handle_value(None, values))

    def _handle_function(self, function, values):
        """
        Handles remaining intrinsic functions
        """
        function.add_child(self._handle_value(None, values))

    def _handle_value(self, key, value, follow_dependencies=True):
        """
        Handles a value of any type, and recurses into the children
        :param key: The key
        :param value: The value
        :param follow_dependencies: Whether or not dependencies should be followed, if false conditions and functions are ignored.
        :return: The element which key and value represent
        """
        if isinstance(value, basestring) or isinstance(value, int) or isinstance(bool, int):
            p = Property(key, value)
            # Add a dependency with the condition
            if follow_dependencies and key == "Condition":
                p.add_dependency(self.template.get_by_logical_id(value))
            return p
        elif isinstance(value, list):
            s = Element(ElementType.list)
            i = 0
            for nested_value in value:
                s.add_child(self._handle_value(i, nested_value, follow_dependencies))
                i += 1
            return s
        elif isinstance(value, dict):
            k = Key(key)
            for vk, vv in value.iteritems():
                if follow_dependencies and vk in self.known_functions:
                    f = Function(vk)
                    handler = self.known_functions[vk]
                    handler(f, vv)
                    k.add_child(f)
                else:
                    k.add_child(self._handle_value(vk, vv, follow_dependencies))
            return k

    def _parse_resource(self, resource, raw):
        resource.resource_type = raw.get('Type')

        if not 'Properties' in raw:
            return

        for pk, pv in raw.iteritems():
            children = self._handle_value(pk, pv)
            resource.add_child(children)

            # Handle a dependency on another resource
            if pk == 'DependsOn':
                r = self.template.get_resource(pv)
                resource.add_dependency(r)

    def _parse_resources(self, document):
        resources = document['Resources']

        for k, v in resources.items():
            r = self.template.get_resource(k)
            self._parse_resource(r, v)

    def _parse_metadata(self, document):
        metadata = document.get('Metadata')

        if not metadata is None:
            for k, v in metadata.iteritems():
                e = Metadata(k)
                self.template.add_element(e)
                e.add_child(self._handle_value(None, v, False))

