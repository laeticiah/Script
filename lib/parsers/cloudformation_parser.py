import json
from collections import defaultdict
from cfn_flip import to_json, load


def parse_cloudformation_file(file_content):
    try:
        # Convert CloudFormation YAML to JSON with cfn_flip
        json_content = to_json(file_content)
        # load JSON formatted CloudFormation files
        parsed_content = json.loads(json_content)
    except Exception as e:
        raise Exception(f"Error parsing CloudFormation file: {str(e)}")
    
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
