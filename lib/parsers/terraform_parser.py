import hcl2
import hcl
from collections import defaultdict

def parse_with_hcl2(file_content):
    try:
        return hcl2.loads(file_content), 2
    except Exception:
        # HCL2 parsing failed, attempt with HCL1
        return None, None

def parse_with_hcl1(file_content):
    try:
        return hcl.loads(file_content), 1
    except Exception:
        # HCL1 parsing also failed
        return None, None

def parse_terraform_file(file_content):
    # Try parsing with HCL2 first
    parsed_content, version = parse_with_hcl2(file_content)
    if parsed_content is None:
        # If HCL2 parsing fails, try with HCL1
        parsed_content, version = parse_with_hcl1(file_content)
    
    # Initialize a dictionary to count the types of resources
    resource_counts = defaultdict(int)

    # Check if parsing was successful
    if parsed_content:
        # Traverse the parsed content for resource declarations
        if 'resource' in parsed_content:
            for resource_group in parsed_content['resource']:
                for resource_type in resource_group:
                    resource_counts[resource_type] += len(resource_group[resource_type])

    # Convert the defaultdict to a regular dict for return
    resource_counts = dict(resource_counts)
    # Prepare the output with a more descriptive key for the HCL version
    output = {
        "Resource Types and Counts": resource_counts,
        "HCL Version": f"HCLv{version}" if version else "Unknown"
    }
    return output
