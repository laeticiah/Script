import re
import os
from lib.logger import setup_logger

logger = setup_logger(__name__)
def parse_chef_file(file_content):
    # Regex pattern to initially capture potential AWS SDK calls
    pattern = re.compile(r'\b(\w+)\.(\w+)\(')
    #pattern = re.compile(r'\b(?:aws_|AWS::)?\w+\.(?:\w+_)?\w+')

    # List of known non-AWS calls to exclude from results
    non_aws_methods = {
        'Log.debug', 'Log.info', 'Timeout.timeout', 'URI.unescape', 'end.run_action', 'new_resource.snapshot_id'
    }

    # Dictionary to store AWS-specific results, keyed by "ServiceName.MethodName"
    resources_used = {}

    # Find all matches and filter non-AWS calls
    try:
        for _match in re.finditer(pattern, file_content):
            key = f"{_match.group(1)}.{_match.group(2)}"
            if key not in non_aws_methods:
                if key not in resources_used:
                    resources_used[key] = 0
                resources_used[key] += 1
    except Exception as e:
        logger.exception("Error parsing chef file: %s", str(e))
        return {}
    return resources_used

# Re-analyzing with the revised approach to include S3
all_resources = {}
if __name__ == '__main__':
    files = ['elastic_ip.rb','ebs_volume.rb','iam_policy.rb','instance_role.rb','s3_bucket.rb']
    for file in files:
        content = open(os.path.join('resources', 'chef', file)).read()
        resources = parse_chef_file(content)
        for key, value in resources.items():
            if key in all_resources:
                all_resources[key] += value
            else:
                all_resources[key] = value
        print(file, '==>', all_resources)
