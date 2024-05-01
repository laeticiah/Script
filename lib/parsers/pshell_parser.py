'''
Powershell parser
'''
import boto3
import re

def get_aws_service_names():
    session = boto3.Session()
    available_services = session.get_available_services()
    return [service.replace(' ', '') for service in available_services]

def parse_powershell_file(file_contents: str):
    # Fetch AWS service names
    service_names = get_aws_service_names()
    service_regex_part = '|'.join(service_names)

    cmdlet_patterns = [
        rf'\b(New|Get|Set|Delete|Update|List)-(({service_regex_part})\w*)\b',
        rf'\b(Start|Stop|Restart|Remove|Enable|Disable)-(({service_regex_part})\w*)\b',
        rf'\b(Invoke|Send|Publish|Register|Unregister)-(({service_regex_part})\w*)\b',
        rf'\b(Import|Export)-(({service_regex_part})\w*)\b',
        rf'\b(Grant|Revoke)-(({service_regex_part})\w*)\b',
        rf'\bAWS-(({service_regex_part})\w*)\b',
    ]

    resources = []
    for pattern in cmdlet_patterns:
        found_cmdlets = re.findall(pattern, file_contents, re.IGNORECASE)
        for cmdlet in found_cmdlets:
            resources.append('-'.join(cmdlet[:-1]))

    return resources

if __name__ == '__main__':
    script_path = r'resources/aws.ps1'
    with open(script_path, 'r') as file:  # pylint: disable=unspecified-encoding
        script_contents = file.read()
    resources = parse_powershell_file(script_contents)
    print(f'Resources found: {resources}')
