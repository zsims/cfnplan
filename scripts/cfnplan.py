import argparse
from cfnplan import Template

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dependencies', action='store_true',
                        help='List dependencies between resources and parameters')
    parser.add_argument('stack', nargs='?', help='Stack template')
    values = parser.parse_args()

    t = Template.parse_file(values.stack)
    t.print_dependencies()