'''
Spring Cloud parser
'''

import re
from lib.logger import setup_logger

# Set up logging
logger = setup_logger(__name__)

# Regular expression patterns
AWS_SERVICE_PATTERN = r'(?:\bAmazonAWS|\bAmazon|\bAWS|\bcom\.amazonaws\.services)\.\w+\.\w+'
AWS_FUNCTION_PATTERN = r'\.(?:run|create|delete|put|modify|register|update|describe|list|get|start|stop|terminate|enable|disable|invoke|send|publish|import|export|grant|revoke)\w*'
AWS_ANNOTATION_PATTERN = r'@(?:EnableAws|EnableAwsClient|EnableAwsService|AwsClientConfig|AwsRegion|AwsEndpoint|AwsCredentials|AwsSecretKey|AwsAccessKey|DynamoDBTable|S3Bucket|SqsListener|SnsSubscription|KinesisStream|ElastiCacheCluster)\b'
AWS_CONFIG_PATTERN = r'(?:aws|amazon|dynamo|s3|sqs|sns|kinesis|elasticache)\.\w+(?:\.enabled)?'
AWS_PROPERTY_PATTERN = r'(?:cloud\.aws|aws\.)\.\w+|(?:sqs|s3|dynamodb|sns|kinesis|elasticache)\.\w+'

def parse_springcloud_file(file_content: str) -> dict:
    '''
    Parses a Spring Cloud source code file and identifies AWS resource manipulation commands.

    Args:
        file_content (str): The content of the Spring Cloud source code file.

    Returns:
        dict: A dictionary containing the identified AWS resource action events,
        where the keys are the AWS service names and the values are lists
        of corresponding function names.
    '''
    result = {}

    try:
        # Find AWS service invocations
        service_matches = re.findall(AWS_SERVICE_PATTERN, file_content)
        for match in service_matches:
            service_name = match.split('.')[-2]
            if service_name not in result:
                result[service_name] = []

            # Find AWS function invocations
            function_regex = re.compile(match + AWS_FUNCTION_PATTERN)
            function_matches = function_regex.findall(file_content)
            result[service_name].extend(function_matches)

        # Find AWS annotations
        annotation_matches = re.findall(AWS_ANNOTATION_PATTERN, file_content)
        if annotation_matches:
            result['AWS_Annotations'] = annotation_matches

        # Find AWS configuration properties
        config_matches = re.findall(AWS_CONFIG_PATTERN, file_content)
        if config_matches:
            result['AWS_Configurations'] = config_matches

        # Find AWS properties
        property_matches = re.findall(AWS_PROPERTY_PATTERN, file_content)
        if property_matches:
            result['AWS_Properties'] = property_matches

    except Exception as e:
        logger.exception("Error parsing Spring Cloud file: %s", str(e))
        return {}

    return result
