import ast

def parse_boto3_file(script_path):
    with open(script_path, 'r') as file:
        script = file.read()

    tree = ast.parse(script)
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
    script_path = r'resources/boto3-script.py'
    resources = parse_boto3_file(script_path)
    print(f'Resources being created: {resources}')
