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
        resources = parsed_content.get('resource', [])
        if not isinstance(resources, list):
            resources = [resources]
        for resource_group in resources:
            for resource_type, resource_instances in resource_group.items():
                if not isinstance(resource_instances, list):
                    resource_instances = [resource_instances]
                resource_counts[resource_type] += len(resource_instances)

        # Traverse the parsed content for data source declarations
        data_sources = parsed_content.get('data', [])
        if not isinstance(data_sources, list):
            data_sources = [data_sources]
        for data_group in data_sources:
            for data_type, data_instances in data_group.items():
                if not isinstance(data_instances, list):
                    data_instances = [data_instances]
                data_source_counts[data_type] += len(data_instances)

        # Traverse the parsed content for module declarations
        modules = parsed_content.get('module', [])
        if not isinstance(modules, list):
            modules = [modules]
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
