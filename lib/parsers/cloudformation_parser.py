'''
Cloudformation parser
'''
import json
from collections import defaultdict
from cfn_flip import to_json  # type: ignore
from lib.logger import setup_logger

logger = setup_logger(__name__)

# pylint: disable=invalid-name


def parse_cloudformation_file(file_content: str):
    ''' parse cloudformation files '''
    logger.debug("type file_contents: %s", type(file_content))
    logger.debug("file_contents: %s", file_content)
    try:
        # Convert CloudFormation YAML to JSON with cfn_flip
        try:
            json_content = to_json(file_content)
        except Exception as e:   # pylint: disable=broad-exception-caught
            json_content = file_content
        # load JSON formatted CloudFormation files
        parsed_content = json.loads(json_content)
    except Exception as e:   # pylint: disable=broad-exception-caught
        logger.error("Error parsing CloudFormation file: %s", str(e))
        return {}
        # raise Exception("Error parsing CloudFormation file: %s", str(e))

    # Initialize a dictionary to count the types of resources
    resource_counts = defaultdict(int)
    # Traverse the parsed content for resource declarations
    if 'Resources' in parsed_content:
        for resource in parsed_content['Resources']:
            resource_type = parsed_content['Resources'][resource]['Type']
            resource_counts[resource_type] += 1

    # Convert the defaultdict to a regular dict for return
    resource_counts = dict(resource_counts)
    return resource_counts


if __name__ == '__main__':
    script_path = r'resources/cluster.yaml'
    with open(script_path, 'r') as file:  # pylint: disable=unspecified-encoding
        script_contents = file.read()
    resources = parse_cloudformation_file(script_contents)
    print(f'Resources being created: {resources}')
