'''
Groovy parser
'''

import re
from lib.logger import setup_logger

# Set up logging
logger = setup_logger(__name__)

# Regular expression patterns
AWS_PATTERN = r'(?:aws|AWS|Amazon|com\.amazonaws)\S*'
AWS_CLI_PATTERN = r'(?:aws|AWS)\s+\S+(?:\s+--\S+)*'
AWS_METHOD_PATTERN = r'(?:\w+\.)?(?:create|delete|get|put|update|describe|list|batch)(?:Bucket|Instance|Volume|SecurityGroup|Subnet|VPC|Queue|Topic|Function|Rule|Policy|Certificate|HostedZone|Stack|Table|User|Group|Role|Policy|Trail|Alarm|Dashboard|Repository|Pipeline|Project|Build|Deployment|Cluster|Service|TaskDefinition|ContainerInstance|Target|LoadBalancer|LaunchConfiguration|ScalingPolicy|ScalingGroup|DBInstance|DBCluster|Cache|Stream|Domain|Application|Environment|Layer|Method|Stage|RestApi|Deployment|Model|Job|MLModel|BatchPrediction|DataSource|Evaluation|Training|Transcription|Collection|Entity|Vocabulary|LanguageModel|Backup|RecoveryPoint|VaultLock|Archive|Channel|Input|ImageVersion|ConfigurationTemplate|Distribution|Invalidation|CloudFrontOriginAccessIdentity|StreamingDistribution|OriginAccessControl|MilestoneState|WebACL|RateBasedRule|Regex|Pattern|MatchSet|ByteMatchSet|IPSet|RegexPatternSet|SizeConstraintSet|SqlInjectionMatchSet|XssMatchSet|Image|LifecyclePolicy|LifecycleHook|Registry|LayerVersion|Project|CodeReview)\s*\([^)]*\)'
AWS_SDK_PATTERN = r'(?:AmazonAWS|AWS|com\.amazonaws)\.\w+\.\w+\([^)]*\)'
AWS_CONFIG_PATTERN = r'(?:AWS\.|AMAZON\.)[A-Z0-9_]+'
AWS_BUILDER_PATTERN = r'(?:AmazonAWS|AWS|com\.amazonaws)\.\w+\.\w+Builder\([^)]*\)'
AWS_CLIENT_PATTERN = r'(?:AmazonAWS|AWS|com\.amazonaws)\.\w+\.\w+Client\([^)]*\)'
AWS_CLOSURE_PATTERN = r'(?:AmazonAWS|AWS|com\.amazonaws)\.\w+\.\w+\s*\{[^}]*}\s*\.\w+\([^)]*\)'

def parse_groovy_file(file_content: str) -> dict:
    '''
    Parses a Groovy script file and identifies AWS resource manipulation commands.

    Args:
        file_content (str): The content of the Groovy script file.

    Returns:
        dict: A dictionary containing the identified AWS resource action events.
    '''
    result = {}

    try:
        # Find AWS-related patterns
        aws_matches = re.findall(AWS_PATTERN, file_content)
        if aws_matches:
            result['AWS_Related'] = list(set(aws_matches))

        # Find AWS CLI commands
        cli_matches = re.findall(AWS_CLI_PATTERN, file_content)
        if cli_matches:
            result['AWS_CLI_Commands'] = [cmd.strip() for cmd in cli_matches]

        # Find AWS-specific method invocations
        method_matches = re.findall(AWS_METHOD_PATTERN, file_content)
        if method_matches:
            result['AWS_Method_Invocations'] = list(set(method_matches))

        # Find AWS SDK invocations
        sdk_matches = re.findall(AWS_SDK_PATTERN, file_content)
        if sdk_matches:
            result['AWS_SDK_Invocations'] = list(set(sdk_matches))

        # Find AWS configuration variables
        config_matches = re.findall(AWS_CONFIG_PATTERN, file_content)
        if config_matches:
            result['AWS_Configurations'] = list(set(config_matches))

        # Find AWS builder invocations
        builder_matches = re.findall(AWS_BUILDER_PATTERN, file_content)
        if builder_matches:
            result['AWS_Builder_Invocations'] = list(set(builder_matches))

        # Find AWS client invocations
        client_matches = re.findall(AWS_CLIENT_PATTERN, file_content)
        if client_matches:
            result['AWS_Client_Invocations'] = list(set(client_matches))

        # Find AWS closure invocations
        closure_matches = re.findall(AWS_CLOSURE_PATTERN, file_content)
        if closure_matches:
            result['AWS_Closure_Invocations'] = list(set(closure_matches))

    except Exception as e:
        logger.exception("Error parsing Groovy file: %s", str(e))
        return {}

    return result
    
