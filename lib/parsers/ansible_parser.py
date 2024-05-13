'''
Ansible parser
'''
import re
from collections import defaultdict
import yaml  # type: ignore
from lib.logger import setup_logger

logger = setup_logger(__name__)


def parse_ansible_file(file_content):
    ''' parse the ansible file '''
    # Load the Ansible YAML playbook
    try:
        parsed_yaml = yaml.safe_load(file_content)
    except yaml.YAMLError as e:
        logger.error("Error parsing Ansible yaml file:%s", str(e))
        return {}

    search_terms = [
        "aws", "ec2", "s3", "iam", "sts", "lambda", "rds", "dynamodb", "ecs",
        "eks", "elasticache", "cloudformation", "cloudwatch", "route53", "sns",
        "sqs", "kms", "secretsmanager", "cognito", "apigateway", "acm", "elb",
        "elbv2", "autoscaling", "cloudfront", "cloudtrail", "config", "backup",
        "guardduty", "inspector", "macie", "securityhub", "ssm", "stepfunctions",
        "waf", "wafv2", "xray"
    ]

    # Build the regex pattern from the search terms
    module_pattern = r"|".join(term for term in search_terms)
    aws_pattern = re.compile(rf"({module_pattern})", re.IGNORECASE)

    # Initialize a dictionary to count the AWS module usage
    aws_module_counts = defaultdict(int)

    # Traverse the parsed content for tasks using AWS modules
    try:  # pylint: disable=too-many-nested-blocks
        for play in parsed_yaml:
            if "tasks" in play:
                for task in play["tasks"]:
                    for key, value in task.items():
                        # Check if the task name matches any search term
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                # Check for 'module' in nested dicts
                                if sub_key == 'module' and aws_pattern.search(sub_value):
                                    aws_module_counts[sub_value] += 1
                        # Direct check on the first level of the task
                        elif key == 'module' and aws_pattern.search(value):
                            aws_module_counts[value] += 1
            else:
                name = play.pop('name')
                with_items = play.pop('with_items', None)
                when = play.pop('when', None)
                tags = play.pop('tags', None)
                sudo = play.pop('sudo', None)
                register = play.pop('register', None)
                if 'local_action' in play:
                    module = aws_pattern.search(play['local_action']['module'])
                    if module:
                        aws_module_counts[play['local_action']['module']] += 1
                play.pop('local_action', None)
                for key in play:
                    if aws_pattern.search(key):
                        aws_module_counts[key] += 1

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error parsing Ansible file: %s", str(e))
        return {}

    # Convert the defaultdict to a regular dict for return
    aws_module_counts = dict(aws_module_counts)

    return aws_module_counts


if __name__ == "__main__":
    script_path = r"resources/ec2.yml"  # your Ansible playbook file
    with open(script_path, "r") as file:  # pylint: disable=unspecified-encoding
        ansible_file_contents = file.read()
    aws_module_usage = parse_ansible_file(ansible_file_contents)
    print(f"{aws_module_usage}")