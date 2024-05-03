'''
Shell parser
'''
import re

def parse_shell_file(file_content: str):
    resource_creations = []

    PATTERNS = [
        r'\baws\s+\w+\s+(\b(create|put|run|make|build|launch)\b)(-\w+)+',
        r'\baws\s+(\b(ec2|ecs|eks|lambda|s3|rds|dynamodb|cloudformation|iam)\b)\s+\w+(-\w+)*',
        r'\baws\s+(\b(ec2|ecs|eks|lambda|s3|rds|dynamodb|cloudformation|iam)\b)\s+(\b(describe|get|list)\b)(-\w+)*',
        r'\baws\s+(\b(ec2|ecs|eks|lambda|s3|rds|dynamodb|cloudformation|iam)\b)\s+(\b(start|stop|terminate|delete|remove)\b)(-\w+)*',
        r'\baws\s+(\b(ec2|ecs|eks|lambda|s3|rds|dynamodb|cloudformation|iam)\b)\s+(\b(update|modify|attach|detach)\b)(-\w+)*',
        r'\baws\s+(\b(ec2|ecs|eks|lambda|s3|rds|dynamodb|cloudformation|iam)\b)\s+(\b(create|put|run|make|build|launch)\b)(-\w+)*'
        r'\baws\s+ec2-instance-connect\s+send-ssh-public-key\s+.+'
    ]

    for pattern in PATTERNS:
        for line in file_content.split('\n'):
            search = re.search(pattern, line, re.IGNORECASE)
            if search:
                api_call = search.group(0).replace('aws', '').strip()
                resource_creations.append('.'.join(api_call.split()))

    return resource_creations

if __name__ == '__main__':
    script_path = r'resources/test.sh'
    with open(script_path, 'r') as content:  # pylint: disable=unspecified-encoding
        script_contents = parse_shell_file(content.read())
    print(f'AWS CLI commands found: {script_contents}')
