'''
Terraform parser
'''

from collections import defaultdict
import hcl2
import hcl  # type: ignore

# pylint: disable=invalid-name

def parse_with_hcl2(file_content: str):
    ''' parse using hcl2 '''
    try:
        return hcl2.loads(file_content), 2
    except Exception:
        # HCL2 parsing failed, attempt with HCL1
        return None, None

def parse_with_hcl1(file_content):
    ''' parse using hcl1 '''
    try:
        return hcl.loads(file_content), 1
    except Exception:
        # HCL1 parsing also failed
        return None, None

def parse_terraform_file(file_content):
    ''' parse terraform file '''
    # Try parsing with HCL2 first
    parsed_content, version = parse_with_hcl2(file_content)
    if parsed_content is None:
        # If HCL2 parsing fails, try with HCL1
        parsed_content, version = parse_with_hcl1(file_content)

    # Initialize dictionaries to count the types of resources and data sources
    resource_counts = defaultdict(int)
    data_source_counts = defaultdict(int)

    # Check if parsing was successful
    if parsed_content:
        # Traverse the parsed content for resource declarations
        if 'resource' in parsed_content:
            for resource_group in parsed_content['resource']:
                for resource_type in resource_group:
                    resource_counts[resource_type] += len(resource_group[resource_type])

        # Traverse the parsed content for data source declarations
        if 'data' in parsed_content:
            for data_group in parsed_content['data']:
                for data_type in data_group:
                    data_source_counts[data_type] += len(data_group[data_type])

        # Traverse the parsed content for module declarations
        if 'module' in parsed_content:
            modules = parsed_content['module']
            if isinstance(modules, list):
                for module in modules:
                    for module_name, module_config in module.items():
                        if 'source' in module_config:
                            module_source = module_config['source']
                            # Recursively parse the module source if it's a local file path
                            if module_source.startswith('./') or module_source.startswith('../'):
                                try:
                                    with open(module_source, 'r') as module_file:
                                        module_content = module_file.read()
                                        module_resources, module_data_sources = parse_terraform_file(module_content)
                                        resource_counts.update(module_resources)
                                        data_source_counts.update(module_data_sources)
                                except FileNotFoundError:
                                    print(f"Module file not found: {module_source}")
            else:
                for module_name, module_config in modules.items():
                    if 'source' in module_config:
                        module_source = module_config['source']
                        # Recursively parse the module source if it's a local file path
                        if module_source.startswith('./') or module_source.startswith('../'):
                            try:
                                with open(module_source, 'r') as module_file:
                                    module_content = module_file.read()
                                    module_resources, module_data_sources = parse_terraform_file(module_content)
                                    resource_counts.update(module_resources)
                                    data_source_counts.update(module_data_sources)
                            except FileNotFoundError:
                                print(f"Module file not found: {module_source}")

    # Convert the defaultdicts to regular dicts for return
    resource_counts = dict(resource_counts)
    data_source_counts = dict(data_source_counts)

    output = {}

    # If resources exist, format and return them
    if resource_counts:
        output['Resource Types and Counts'] = resource_counts

    # If data sources exist, format and return them
    if data_source_counts:
        output['Data Source Types and Counts'] = data_source_counts

    output['HCL Version'] = f"HCLv{version}" if version else "Unknown"

    return output
if __name__ == '__main__':
    script_path = r'resources/ec2.tf'
    with open(script_path, 'r') as file:  # pylint: disable=unspecified-encoding
        script_contents = file.read()
        resources = parse_terraform_file(script_contents)
        print(f'Resources and data sources being created or used: {resources}')
