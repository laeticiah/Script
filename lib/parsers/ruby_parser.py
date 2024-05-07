'''
ruby parser
'''

import os
import re
def parse_ruby_file(content):
    # Pattern to find AWS SDK calls
    pattern = re.compile(r"(\w+)\.(\w+)\(")
    service_mapping = {
        'get_bucket_location': 's3_client',  # Example mapping for S3-specific methods
    }

    try:
        aws_calls = set(re.findall(pattern, content))
        # Filter and format the results
        formatted_calls = set()
        for client, method in aws_calls:
            if method in service_mapping and client == 'client':
                client = service_mapping[method]  # Use a more descriptive client name
            if method not in ['new', 'info', 'error']:
                formatted_calls.add(f"{client}.{method}")

        return formatted_calls
    except Exception as e:
        logging.error('Error reading or processing %s', str(e))
        return set()

def main():
    # Directory containing the Ruby files
    directory = "resources"

    # List of Ruby files to parse
    ruby_files = [
        "bucket_create.rb",
        "create_alarm.rb",
        "create_trail.rb",
        "ec2-ruby-example-create-vpc.rb"
    ]

    # Dictionary to hold results for each file
    results = {}
    # Parse each file and store the AWS functions used
    for file_name in ruby_files:
        file_path = os.path.join(directory, file_name)
        with open(file_path, 'r') as file:
            content = file.read()
            aws_calls = parse_ruby_file(content)
            results[file_name] = aws_calls

    return results

# Execute the main function and capture the results
if __name__ == "__main__":
    aws_functions_per_file_detailed_analysis = main()
    print(aws_functions_per_file_detailed_analysis)
