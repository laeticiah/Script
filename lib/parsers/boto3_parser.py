'''
Python boto3 parser
'''
import ast
from lib.logger import setup_logger

logger = setup_logger(__name__)

# pylint: disable=invalid-name,line-too-long


def parse_boto3_file(file_contents: str):
    '''
    Searches a python file for boto3 commands manipulating aws resources

    Args:
        file_contents (str): The file to be parsed

    Returns:
        list: Matching aws resource action events
    '''

    tree = ast.parse(file_contents)
    resource_creations = []
    boto3_instances = {}

    try:
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Check for boto3 client or resource creation
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                    if node.value.func.attr in ['client', 'resource'] and getattr(node.value.func.value, 'id', '') == 'boto3':
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                boto3_instances[target.id] = node.value.func.attr

            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                instance_name = getattr(node.func.value, 'id', None)
                if instance_name in boto3_instances:
                    # Check method calls on boto3 instances
                    action = node.func.attr
                    resource_creations.append(f"{instance_name}.{action}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error parsing Python file: %s", str(e))
        return []
        # raise Exception("Error parsing Python file: %s", str(e))

    return resource_creations


if __name__ == '__main__':
    script_path = r'resources/boto3_script.py'
    with open(script_path, 'r') as file:  # pylint: disable=unspecified-encoding
        script_contents = file.read()
    resources = parse_boto3_file(script_contents)
    print(f'Resources being created: {resources}')