import boto3
import re

def get_aws_service_names():
    session = boto3.Session()
    available_services = session.get_available_services()
    return [service.replace(' ', '') for service in available_services]

def parse_powershell_file(code):
    # Fetch AWS service names
    service_names = get_aws_service_names()
    service_regex_part = '|'.join(service_names)
    cmdlet_pattern = rf'\b(New|Get|Set|Delete|Update|List)-(({service_regex_part})\w*)\b'
    # Find cmdlets using the generated regex
    found_cmdlets = re.findall(cmdlet_pattern, code, re.IGNORECASE)

    resources = []
    for cmdlet in found_cmdlets:
        resources.append('-'.join(cmdlet[:-1]))
    return resources

if __name__ == '__main__':
    ps_script = open('resources/aws.ps1').read()
    parse_powershell_file(ps_script)

