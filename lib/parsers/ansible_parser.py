import yaml # type: ignore
import re
from collections import defaultdict

def parse_ansible_file(file_content):
    # Load the Ansible YAML playbook
    try:
        parsed_yaml = yaml.safe_load(file_content)
    except yaml.YAMLError as e:
        print(f"Error parsing file: {e}")
        return None

    # Initialize a dictionary to count the AWS module usage
    aws_module_counts = defaultdict(int)

    # Traverse the parsed content for tasks using AWS modules
    for play in parsed_yaml:
        if 'tasks' in play:
            for task in play['tasks']:
                for task_name, task_details in task.items():
                    # Check if the task uses an AWS module
                    # replace 'ec2' with the AWS modules you're interested in
                    if re.search(r'^ec2', task_name):
                        aws_module_counts[task_name] += 1

    # Convert the defaultdict to a regular dict for return
    aws_module_counts = dict(aws_module_counts)

    # Prepare the output with a more descriptive content
    output = {
        "Ansible AWS Module Usage": aws_module_counts
    }

    return output

if __name__ == '__main__':
    script_path = r'resources/ec2.yml'  # your Ansible playbook file
    with open(script_path, 'r') as file:
        ansible_file_contents = file.read()
    aws_module_usage = parse_ansible_file(ansible_file_contents)
    print(f'AWS Module usage: {aws_module_usage}')