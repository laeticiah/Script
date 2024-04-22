'''
JavaScript/Typescript parser
'''
import re
from lib.logger import setup_logger

logger = setup_logger(__name__)

SERVICE_PATTERN = r'(?:const|let|var)\s+(\w+)\s*=\s*new\s+AWS\.(\w+)\('
FUNCTION_PATTERN = r'%s\.(\w+)\('


def parse_js_file(file_content: str):
    '''
    Searches a javascript/typescript file for commands manipulating aws resources

    Args:
        file_contents (str): The file to be parsed

    Returns:
        list: Matching aws resource action events
    '''
    result = {}
    service_matches = re.findall(SERVICE_PATTERN, file_content)
    for service_name, service_class in service_matches:
        function_regex = re.compile(FUNCTION_PATTERN % service_name)
        function_matches = function_regex.findall(file_content)
        result[service_class] = []
        for match in function_matches:
            if match.startswith(('run', 'create', 'delete', 'put', 'modify', 'register', 'update')):
                result[service_class].append(match)

    return result
