from cfnplan import Template, ElementType
import unittest
import os


class TemplateParserTestCase(unittest.TestCase):
    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'templates')

    def test_resources_order_independent(self):
        # Arrange
        raw = '''
            {
                "Resources": {
                    "EIP" : {
                        "Type" : "AWS::EC2::EIP",
                        "Properties" : {
                            "InstanceId" : { "Ref" : "Instance" }
                        }
                    },

                    "Instance": {
                        "Type" : "AWS::EC2::Instance"
                    }
                }
            }
        '''

        # Act
        t = Template.parse_string(raw)

        # Assert
        eip = t.get_resource("EIP")
        dependencies = eip.get_all_dependencies()
        self.assertEqual(1, len(dependencies))
        self.assertEqual('Instance', list(dependencies)[0].logical_id)

    def test_resource_depends_on(self):
        # Arrange
        raw = '''
            {
                "Resources": {
                    "Instance": {
                        "Type" : "AWS::EC2::Instance",
                        "DependsOn": "OtherInstance"
                    },

                    "OtherInstance": {
                        "Type" : "AWS::EC2::Instance"
                    }
                }
            }
        '''

        # Act
        t = Template.parse_string(raw)

        # Assert
        eip = t.get_resource("Instance")
        dependencies = eip.get_all_dependencies()
        self.assertEqual(1, len(dependencies))
        self.assertEqual('OtherInstance', list(dependencies)[0].logical_id)

    def test_parameters(self):
        # Arrange
        raw = r'''
        {
            "Resources": {
                "Instance": {
                    "Type" : "AWS::EC2::Instance"
                }
            },
            "Parameters": {
                "KeyName" : {
                    "Description" : "Name of an existing EC2 KeyPair",
                    "Type" : "AWS::EC2::KeyPair::KeyName",
                    "ConstraintDescription" : "must be the name of an existing EC2 KeyPair."
                },

                "InstanceType" : {
                    "Description" : "Amazon EC2 instance type",
                    "Type" : "String",
                    "Default" : "m1.large",
                    "AllowedValues" : [ "t1.micro", "t2.micro", "t2.small"],
                    "ConstraintDescription" : "must be a valid EC2 instance type."
                },

                "SourceCidrForRDP" : {
                    "Description" : "IP Cidr from which you are likely to RDP into the instances.",
                    "Type" : "String",
                    "MinLength" : "9",
                    "MaxLength" : "18",
                    "AllowedPattern" : "^([0-9]+\\.){3}[0-9]+\\/[0-9]+$"
                }
            }
        }
        '''
        expected_parameters = {
            'KeyName',
            'InstanceType',
            'SourceCidrForRDP'
        }

        # Act
        t = Template.parse_string(raw)

        # Assert
        parameters = set(e.logical_id for e in t.elements if e.element_type == ElementType.parameter)
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
        raw = '''
        {
            "Conditions" : {
                "Is-EC2-Classic" : { "Fn::Not" : [{ "Condition" : "Is-EC2-VPC"}]},
                "Is-EC2-VPC"     : { "Fn::Or" : [ {"Fn::Equals" : [{"Ref" : "AWS::Region"}, "eu-central-1" ]},
                                      {"Fn::Equals" : [{"Ref" : "AWS::Region"}, "cn-north-1" ]}]},
                "Reference-Resource" : { "Fn::If" : [{ "Ref" : "ElasticLoadBalancer"}, "y", "n"]}
            },

            "Resources" : {
                "ElasticLoadBalancer" : {
                    "Type" : "AWS::ElasticLoadBalancing::LoadBalancer"
                }
            }
        }
        '''

        # Act
        t = Template.parse_string(raw)

        # Assert
        is_ec2_classic = t.get_by_logical_id('Is-EC2-Classic')
        self.assertEqual(ElementType.condition, is_ec2_classic.element_type)
        dependencies = is_ec2_classic.get_all_dependencies()
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
        dependencies = db_instance.get_all_dependencies()
        resources = set(r.logical_id for r in dependencies if r.element_type == ElementType.resource)
        parameters = set(p.logical_id for p in dependencies if p.element_type == ElementType.parameter)
        self.assertSetEqual(expected_parameters, parameters)
        self.assertSetEqual(expected_resources, resources)

    def test_function_fn_base64(self):
        # Arrange
        raw = '''
        {
            "Resources": {
                "Instance": {
                    "Type": "AWS::EC2::Instance",
                    "Properties": {
                        "Tags": [
                            {
                                "Key": "one",
                                "Value": {"Fn::Base64": "hello"}
                            }
                        ]
                    }
                }
            }
        }
        '''

        # Act
        t = Template.parse_string(raw)

        # Assert
        instance = t.get_resource("Instance")
        function = next(c for c in instance.get_all_children() if c.element_type == ElementType.function)
        self.assertEqual("Fn::Base64", function.name)

    def test_function_fn_find_in_map(self):
        # Arrange
        raw = '''
        {
            "Mappings": {
                "AWSRegion2AMI" : {
                  "us-east-1": {"Windows2008r2" : "ami-dc1f56b6", "Windows2012r2" : "ami-e4034a8e"}
                }
            },
            "Resources": {
                "Instance": {
                    "Type": "AWS::EC2::Instance",
                    "Properties": {
                        "Tags": [
                            {
                                "Key": "one",
                                "Value": {"Fn::FindInMap": ["AWSRegion2AMI", "us-east-1", "Windows2008r2"]}
                            }
                        ]
                    }
                }
            }
        }
        '''

        # Act
        t = Template.parse_string(raw)

        # Assert
        instance = t.get_resource("Instance")
        function = next(c for c in instance.get_all_children() if c.element_type == ElementType.function)
        dependencies = list(function.get_all_dependencies())
        self.assertEqual("Fn::FindInMap", function.name)
        self.assertEqual(1, len(dependencies))
        self.assertEqual("AWSRegion2AMI", dependencies[0].logical_id)
        self.assertEqual(ElementType.mapping, dependencies[0].element_type)

    def test_function_fn_get_att(self):
        # Arrange
        raw = '''
        {
            "Resources": {
                "EIP" : {
                    "Type" : "AWS::EC2::EIP",
                    "Properties" : {
                        "InstanceId" : { "Ref" : "Instance" }
                    }
                },

                "Instance": {
                    "Type" : "AWS::EC2::Instance",
                    "Properties": {
                        "Tags": [
                            {
                                "Key": "ip-allocation",
                                "Value": {"Fn::GetAtt": ["EIP", "AllocationId"]}
                            }
                        ]
                    }
                }
            }
        }
        '''

        # Act
        t = Template.parse_string(raw)

        # Assert
        instance = t.get_resource("Instance")
        function = next(c for c in instance.get_all_children() if c.element_type == ElementType.function)
        dependencies = list(function.get_all_dependencies())
        self.assertEqual("Fn::GetAtt", function.name)
        self.assertEqual(1, len(dependencies))
        self.assertEqual("EIP", dependencies[0].logical_id)
        self.assertEqual(ElementType.resource, dependencies[0].element_type)

    def test_function_fn_get_azs(self):
        # Arrange
        raw = '''
        {
            "Resources": {
                "Instance": {
                    "Type" : "AWS::EC2::Instance",
                    "Properties": {
                        "Tags": [
                            {
                                "Key": "azs",
                                "Value": {"Fn::GetAZs": "AWS::Region"}
                            }
                        ]
                    }
                }
            }
        }
        '''

        # Act
        t = Template.parse_string(raw)

        # Assert
        instance = t.get_resource("Instance")
        function = next(c for c in instance.get_all_children() if c.element_type == ElementType.function)
        dependencies = list(function.get_all_dependencies())
        self.assertEqual("Fn::GetAZs", function.name)
        self.assertEqual(1, len(dependencies))
        self.assertEqual("AWS::Region", dependencies[0].logical_id)
        self.assertEqual(ElementType.pseudo_parameter, dependencies[0].element_type)

    def test_function_fn_join(self):
        # Arrange
        raw = '''
        {
            "Resources": {
                "EIP" : {
                    "Type" : "AWS::EC2::EIP",
                    "Properties" : {
                        "InstanceId" : { "Ref" : "Instance" }
                    }
                },

                "Instance": {
                    "Type" : "AWS::EC2::Instance",
                    "Properties": {
                        "Tags": [
                            {
                                "Key": "ip-allocation",
                                "Value": {
                                    "Fn::Join": [
                                        "The EIP allocation id is: ",
                                        {"Fn::GetAtt": ["EIP", "AllocationId"]}
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }
        '''

        # Act
        t = Template.parse_string(raw)

        # Assert
        instance = t.get_resource("Instance")
        join_function = next(c for c in instance.get_all_children() if c.element_type == ElementType.function and c.name == 'Fn::Join')
        dependencies = list(join_function.get_all_dependencies())
        self.assertEqual(1, len(dependencies))
        self.assertEqual("EIP", dependencies[0].logical_id)
        self.assertEqual(ElementType.resource, dependencies[0].element_type)
        self.assertEqual(1, len(join_function.children))
        grand_children = join_function.children[0]
        self.assertEqual(ElementType.list, grand_children.element_type)
