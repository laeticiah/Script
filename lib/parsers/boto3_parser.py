'''
Python boto3 parser
'''
import ast

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

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if hasattr(node.func, 'attr') and any(action in node.func.attr for action in ['create', 'register', 'run']):
                if hasattr(node.func.value, 'attr'):
                    resource_creations.append(f"{node.func.value.attr}.{node.func.attr}")
                elif hasattr(node.func.value, 'id'):
                    resource_creations.append(f"{node.func.value.id}.{node.func.attr}")

    return resource_creations

if __name__ == '__main__':
    script_path = r'resources/boto3_script.py'
    with open(script_path, 'r') as file:  # pylint: disable=unspecified-encoding
        script_contents = file.read()
    resources = parse_boto3_file(script_contents)
    print(f'Resources being created: {resources}')
