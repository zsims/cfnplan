from cfnplan import Template, ElementType
import unittest
import os


class TemplateParserTestCase(unittest.TestCase):
    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'templates')

    def test_parameters(self):
        # Arrange
        expected_parameters = {
            'KeyName',
            'InstanceType',
            'SourceCidrForRDP'
        }

        # Act
        t = Template.parse_file(os.path.join(self.test_data_dir, 'single_server.template'))
        parameters = set(e.logical_id for e in t.elements if e.element_type == ElementType.parameter)

        # Assert
        self.assertSetEqual(expected_parameters, parameters)

        # Check children
        key_name = t.get_by_logical_id('KeyName')
        self.assertEqual(3, len(key_name.children))

        expected_values = {
            'Description': 'Name of an existing EC2 KeyPair',
            'Type': 'AWS::EC2::KeyPair::KeyName',
            'ConstraintDescription': 'must be the name of an existing EC2 KeyPair.'
        }
        for c in key_name.children:
            self.assertEqual(ElementType.property, c.element_type)
            self.assertIn(c.key, expected_values)
            self.assertEqual(c.value, expected_values[c.key])

    def test_conditions_order_independent(self):
        # Arrange
        t = Template.parse_file(os.path.join(self.test_data_dir, 'conditions.template'))

        # Act
        is_ec2_classic = t.get_by_logical_id('Is-EC2-Classic')

        # Assert
        self.assertEqual(ElementType.condition, is_ec2_classic.element_type)
        dependencies = is_ec2_classic.all_dependencies()
        self.assertEqual(1, len(dependencies))
        self.assertEqual('Is-EC2-VPC', list(dependencies)[0].logical_id)

    def test_resource_dependency_tree(self):
        # Arrange
        t = Template.parse_file(os.path.join(self.test_data_dir, 'single_server.template'))
        expected_parameters = {
            'KeyName',
            'InstanceType',
            'SourceCidrForRDP'
        }
        expected_resources = {
            'SharePointFoundationSecurityGroup',
            'SharePointFoundationWaitHandle',
            'SharePointFoundation'
        }

        # Act
        instance = t.get_resource('SharePointFoundation')

        # Assert
        parameters = set()
        resources = set()

        def collect(item, level, visited):
            if item.element_type == ElementType.parameter:
                parameters.add(item.logical_id)
            elif item.element_type == ElementType.resource:
                resources.add(item.logical_id)

        instance.visit_dependencies(collect)

        self.assertSetEqual(expected_parameters, parameters)
        self.assertSetEqual(expected_resources, resources)

    def test_dependencies_resolved_through_conditions(self):
        # Arrange
        t = Template.parse_file(os.path.join(self.test_data_dir, 'WordPress_Multi_AZ.template'))
        expected_parameters = {
            'DBName',
            'MultiAZDatabase',
            'DBUser',
            'DBPassword',
            'DBClass',
            'DBAllocatedStorage'
        }

        # These resources resolve through an "If"
        expected_resources = {
            'DBEC2SecurityGroup',
            'DBSecurityGroup'
        }

        # Act
        db_instance = t.get_resource('DBInstance')

        # Assert
        dependencies = db_instance.all_dependencies()
        resources = set(r.logical_id for r in dependencies if r.element_type == ElementType.resource)
        parameters = set(p.logical_id for p in dependencies if p.element_type == ElementType.parameter)
        self.assertSetEqual(expected_parameters, parameters)
        self.assertSetEqual(expected_resources, resources)
