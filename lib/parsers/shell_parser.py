'''
Shell parser
'''
import re


def parse_shell_file(file_content: str):
    resource_creations = []

    PATTERN = r'\baws\s+\w+\s+(\b(create|put|run|make|build|launch)\b)(-\w+)+'
    for line in file_content.split('\n'):
        search = re.search(PATTERN, line, re.IGNORECASE)
        if search:
            api_call = search.group(0).replace('aws','').strip()
            resource_creations.append('.'.join(api_call.split()))
    return resource_creations

if __name__ == '__main__':
    script_path = r'resources/test.sh'
    with open(script_path, 'r') as content:  # pylint: disable=unspecified-encoding
        script_contents = parse_shell_file(content.read())
    print(f'AWS CLI commands found: {script_contents}')
