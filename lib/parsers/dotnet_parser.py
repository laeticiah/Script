import re
from lib.logger import setup_logger

# Set up logging
logger = setup_logger(__name__)

# Regular expression patterns for .NET code files
AWS_SERVICE_PATTERN = r'\b(?:Amazon|Aws|AWS)\.(?:Amplify|APIGateway|AppConfig|ApplicationAutoScaling|ApplicationDiscoveryService|AppMesh|AppStream|AppSync|Athena|AutoScaling|Backup|Batch|Braket|Chime|Cloud9|CloudDirectory|CloudFormation|CloudFront|CloudHSM|CloudHSMV2|CloudSearch|CloudTrail|CloudWatch(?:Events|Logs|Synthetics)?|CodeArtifact|CodeBuild|CodeCommit|CodeDeploy|CodeGuruProfiler|CodeGuruReviewer|CodePipeline|CodeStar|CodeStarConnections|CodeStarNotifications|CognitoIdentity|CognitoIdentityProvider|CognitoSync|Comprehend(?:Medical)?|ComputeOptimizer|ConfigService|Connect|CostExplorer|DAX|Detective|DevOpsGuru|DirectConnect|Directory|DLM|DocDB|DynamoDB|DynamoDBStreams|EC2(?:InstanceConnect)?|ECR(?:Public)?|ECS|EFS|EKS|ElastiCache|ElasticBeanstalk|ElasticInference|ElasticLoadBalancing|ElasticMapReduce|Elastic(?:Transcoder|BlockStore|FilesystemService|CommercePlatform)?|ElasticLoadBalancingV2|EventBridge|FIS|FMS|ForecastService|FraudDetector|FSx|GameLift|Glacier|GlobalAccelerator|Glue(?:DataBrew)?|Greengrass(?:V2)?|GroundStation|GuardDuty|HealthLake|Honeycode|IAM|InspectorV2|IoT(?:Analytics|Data|Device(?:Advisor|Defender|Management)|Events|FleetHub|JobsDataPlane|SiteWise|ThingsGraph|TwinMaker|WirelessDataPlane|WirelessNetworkingAnalytics)?|IoTWireless|Ivs|KafkaConnect|Kendra|Kinesis(?:Analytics|AnalyticsV2|Firehose|Video)?|KMS|LakeFormation|Lambda|Lex(?:ModelBuilding|Runtime)?|LicenseManager|Lightsail|Location|LookoutEquipment|LookoutMetrics|LookoutVision|MachineLearning|Macie|ManagedGrafana|MarketplaceCommerceAnalytics|MarketEntitlementService|MediaConnect|MediaConvert|MediaLive|MediaPackage(?:Vod)?|MediaStore|MediaTailor|MemoryDB|MigrationHub(?:Config|Refactor|StrategyRecommendations)?|Mobile|MQ|MWAA|Neptune|NetworkFirewall|NetworkManager|Nimble|OpenSearchServerless|OpsWorksCM|Organizations|Outposts|Panorama|Personalize|PollyRuntimeService|PrivateNetworks|Proton|QLDB|QuickSight|RAM|RDS(?:DataService)?|Redshift(?:ServerlessWorkloadPreview)?|Rekognition|ResilienceHub|ResourceGroupsTaggingAPI|RoboMaker|Route53|Route53RecoveryCluster|Route53RecoveryControlConfig|Route53RecoveryReadiness|S3|S3Control|S3Outposts|SageMaker(?:Edge|FeatureStoreRuntime|Runtime)?|SavingsPlans|Schemas|SecretsManager|SecurityHub|ServerlessApplicationRepository|ServiceCatalog(?:AppRegistry)?|ServiceDiscovery|SES(?:V2)?|SFNV2|Shield|Signer|SimSpaceWeaver|SMS|SnowDeviceManagement|Snowball|SNS|SQS|SSM(?:Contacts|Incidents)?|SSO(?:Admin|Identity|OIDC)?|StepFunctions|StorageGateway|Support|Synthetics|SyntheticsV2Beta|Textract|TimestreamQuery|TimestreamWrite|TranscribeService|Transfer|Translate|VoiceID|WAF(?:Regional)?|WAF(?:RegionalV2|V2)?|WellArchitected|WorkDocs|WorkLink|WorkMail|WorkMailMessageFlow|WorkSpaces(?:Web)?|XRay)(?:\.\w+)*'
AWS_METHOD_PATTERN = r'\.(?:Create|Delete|Describe|Get|List|Put|Update|Batch\w+|Attach|Detach)\w+'
AWS_CONFIG_PATTERN = r'(?:AWS_|AMAZON_|aws\.|amazon\.)\w+'
AWS_ANNOTATION_PATTERN = r'(?:AWS|Amazon)\w+Attribute'
AWS_USING_PATTERN = r'using\s+(?:Amazon|AWS)\.\w+;'
AWS_NAMESPACE_PATTERN = r'namespace\s+(?:Amazon|AWS)\.\w+'
AWS_IMPORTS_PATTERN = r'Imports\s+(?:Amazon|AWS)\.\w+'

# Regular expression patterns for web.config file
AWS_CONFIG_SECTION_PATTERN = r'<aws\s+.+?>.+?</aws>'
AWS_CONFIG_SETTING_PATTERN = r'<add\s+key="([^"]+)"\s+value="([^"]+)"\s*/>'

def parse_dotnet_file(file_content: str, file_path: str) -> dict:
    '''
    Searches a .NET file (C#, Visual Basic .NET, ASP.NET) or web.config file for commands manipulating AWS resources.

    Args:
        file_content (str): The content of the file to be parsed.
        file_path (str): The path of the file being parsed.

    Returns:
        dict: Matching AWS resource action events or configurations.
    '''
    if file_path.endswith('web.config'):
        return parse_web_config(file_content)
    else:
        return parse_dotnet_code(file_content)

def parse_web_config(file_content: str) -> dict:
    '''
    Parses the web.config file for AWS resource configurations.

    Args:
        file_content (str): The content of the web.config file.

    Returns:
        dict: Matching AWS resource configurations.
    '''
    result = {}

    try:
        # Find AWS configuration sections
        config_sections = re.findall(AWS_CONFIG_SECTION_PATTERN, file_content, re.DOTALL)
        for section in config_sections:
            # Find AWS configuration settings within each section
            config_settings = re.findall(AWS_CONFIG_SETTING_PATTERN, section)
            for key, value in config_settings:
                if key not in result:
                    result[key] = []
                result[key].append(value)

    except Exception as e:
        logger.error("Error parsing web.config file: %s", str(e))
        return {}

    return result

def parse_dotnet_code(file_content: str) -> dict:
    '''
    Searches a .NET code file (C#, Visual Basic .NET, ASP.NET) for commands manipulating AWS resources.

    Args:
        file_content (str): The content of the code file to be parsed.

    Returns:
        dict: Matching AWS resource action events.
    '''
    result = {}

    try:
        # Find AWS service invocations
        service_matches = re.findall(AWS_SERVICE_PATTERN, file_content)
        for service_match in service_matches:
            service_parts = service_match.split('.')
            service_name = service_parts[1]  # Extract the service name

            method_pattern = re.compile(f'{re.escape(service_match)}{AWS_METHOD_PATTERN}')
            method_matches = method_pattern.findall(file_content)

            if service_name not in result:
                result[service_name] = []

            for method_match in method_matches:
                method_name = method_match.split('.')[-1]  # Extract the method name
                result[service_name].append(method_name)

        # Find AWS configuration variables
        config_matches = re.findall(AWS_CONFIG_PATTERN, file_content)
        if config_matches:
            result['AWS_Configurations'] = config_matches

        # Find AWS annotations
        annotation_matches = re.findall(AWS_ANNOTATION_PATTERN, file_content)
        if annotation_matches:
            result['AWS_Annotations'] = annotation_matches

        # Find AWS using statements
        using_matches = re.findall(AWS_USING_PATTERN, file_content)
        if using_matches:
            result['AWS_Using_Statements'] = using_matches

        # Find AWS namespace declarations
        namespace_matches = re.findall(AWS_NAMESPACE_PATTERN, file_content)
        if namespace_matches:
            result['AWS_Namespace_Declarations'] = namespace_matches

        # Find AWS imports statements (VB.NET)
        imports_matches = re.findall(AWS_IMPORTS_PATTERN, file_content)
        if imports_matches:
            result['AWS_Imports_Statements'] = imports_matches

    except Exception as e:
        logger.error("Error parsing .NET code file: %s", str(e))
        return {}

    return result
