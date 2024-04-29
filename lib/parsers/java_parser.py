'''
Java parser
'''
import re
from lib.logger import setup_logger

# Set up logging
logger = setup_logger(__name__)

# Regular expression patterns
SERVICE_PATTERN = r'(\w+)\s+(\w+)\s*=\s*(\w+)\.(\w+)\(\);'
FUNCTION_PATTERN = r'%s\.(\w+)\('
AWS_COMMENT_PATTERN = r'//\s*AWS:\s*(.+)'

def parse_java_file(file_content: str) -> dict:
    '''
    Parses a Java source code file and identifies AWS resource manipulation commands.

    Args:
        file_content (str): The content of the Java source code file.

    Returns:
        dict: A dictionary containing the identified AWS resource action events,
              where the keys are the AWS service names and the values are lists
              of corresponding function names.
    '''
    result = {}
    service_matches = re.findall(SERVICE_PATTERN, file_content)

    # try:
    #     for service_name, service_class in service_matches:
    #         function_regex = re.compile(FUNCTION_PATTERN % service_name)
    #         function_matches = function_regex.findall(file_content)
    #         result[service_class] = []
    #         for match in function_matches:
    #             if match.startswith(('run', 'create', 'delete', 'put', 'modify', 'register', 'update')):
    #                 result[service_class].append(match)
    # except Exception as e:   # pylint: disable=broad-exception-caught
    #     logger.error("Error parsing Javas file: %s", str(e))
    #     return {}
    
    try:
        for match in service_matches:
            service_type, service_name, builder, build_method = match
            if service_type.startswith('Amazon'):
                aws_service = service_type[6:]  # Remove the 'Amazon' prefix
                function_regex = re.compile(FUNCTION_PATTERN % service_name)
                function_matches = function_regex.findall(file_content)
                result[aws_service] = []
                for func_match in function_matches:
                    if func_match.startswith(('run', 'create', 'delete', 'put', 'modify', 'register', 'update')):
                        result[aws_service].append(func_match)
    except Exception as e:
        logger.exception("Error parsing Java file: %s", str(e))
        return {}

    return result

# Example usage
# java_code = '''
#     AmazonS3 s3 = AmazonS3ClientBuilder.defaultClient();
#     s3.createBucket("bucketName");
#     s3.putObject("bucketName", "key", "content");

#     AmazonEC2 ec2 = AmazonEC2ClientBuilder.defaultClient();
#     ec2.runInstances(new RunInstancesRequest());
# '''

# result = parse_java_file(java_code)
# print(result)
