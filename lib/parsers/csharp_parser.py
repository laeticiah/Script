import re
from lib.logger import setup_logger

logger = setup_logger(__name__)

SERVICE_PATTERN = r'\b(?:Amazon|Aws|AWS)\.(?:Amplify|APIGateway|AppConfig|ApplicationAutoScaling|ApplicationDiscoveryService|AppMesh|AppStream|AppSync|Athena|AutoScaling|Backup|Batch|Braket|Chime|Cloud9|CloudDirectory|CloudFormation|CloudFront|CloudHSM|CloudHSMV2|CloudSearch|CloudTrail|CloudWatch(?:Events|Logs|Synthetics)?|CodeArtifact|CodeBuild|CodeCommit|CodeDeploy|CodeGuruProfiler|CodeGuruReviewer|CodePipeline|CodeStar|CodeStarConnections|CodeStarNotifications|CognitoIdentity|CognitoIdentityProvider|CognitoSync|Comprehend(?:Medical)?|ComputeOptimizer|ConfigService|Connect|CostExplorer|DAX|Detective|DevOpsGuru|DirectConnect|Directory|DLM|DocDB|DynamoDB|DynamoDBStreams|EC2(?:InstanceConnect)?|ECR(?:Public)?|ECS|EFS|EKS|ElastiCache|ElasticBeanstalk|ElasticInference|ElasticLoadBalancing|ElasticMapReduce|Elastic(?:Transcoder|BlockStore|FilesystemService|CommercePlatform)?|ElasticLoadBalancingV2|EventBridge|FIS|FMS|ForecastService|FraudDetector|FSx|GameLift|Glacier|GlobalAccelerator|Glue(?:DataBrew)?|Greengrass(?:V2)?|GroundStation|GuardDuty|HealthLake|Honeycode|IAM|InspectorV2|IoT(?:Analytics|Data|Device(?:Advisor|Defender|Management)|Events|FleetHub|JobsDataPlane|SiteWise|ThingsGraph|TwinMaker|WirelessDataPlane|WirelessNetworkingAnalytics)?|IoTWireless|Ivs|KafkaConnect|Kendra|Kinesis(?:Analytics|AnalyticsV2|Firehose|Video)?|KMS|LakeFormation|Lambda|Lex(?:ModelBuilding|Runtime)?|LicenseManager|Lightsail|Location|LookoutEquipment|LookoutMetrics|LookoutVision|MachineLearning|Macie|ManagedGrafana|MarketplaceCommerceAnalytics|MarketEntitlementService|MediaConnect|MediaConvert|MediaLive|MediaPackage(?:Vod)?|MediaStore|MediaTailor|MemoryDB|MigrationHub(?:Config|Refactor|StrategyRecommendations)?|Mobile|MQ|MWAA|Neptune|NetworkFirewall|NetworkManager|Nimble|OpenSearchServerless|OpsWorksCM|Organizations|Outposts|Panorama|Personalize|PollyRuntimeService|PrivateNetworks|Proton|QLDB|QuickSight|RAM|RDS(?:DataService)?|Redshift(?:ServerlessWorkloadPreview)?|Rekognition|ResilienceHub|ResourceGroupsTaggingAPI|RoboMaker|Route53|Route53RecoveryCluster|Route53RecoveryControlConfig|Route53RecoveryReadiness|S3|S3Control|S3Outposts|SageMaker(?:Edge|FeatureStoreRuntime|Runtime)?|SavingsPlans|Schemas|SecretsManager|SecurityHub|ServerlessApplicationRepository|ServiceCatalog(?:AppRegistry)?|ServiceDiscovery|SES(?:V2)?|SFNV2|Shield|Signer|SimSpaceWeaver|SMS|SnowDeviceManagement|Snowball|SNS|SQS|SSM(?:Contacts|Incidents)?|SSO(?:Admin|Identity|OIDC)?|StepFunctions|StorageGateway|Support|Synthetics|SyntheticsV2Beta|Textract|TimestreamQuery|TimestreamWrite|TranscribeService|Transfer|Translate|VoiceID|WAF(?:Regional)?|WAF(?:RegionalV2|V2)?|WellArchitected|WorkDocs|WorkLink|WorkMail|WorkMailMessageFlow|WorkSpaces(?:Web)?|XRay)(?:\.\w+)*'
METHOD_PATTERN = r'\.(?:Create|Delete|Describe|Get|List|Put|Update|Batch\w+|Attach|Detach)\w+'

def parse_csharp_file(file_content: str) -> dict:
    '''
    Searches a C# file for commands manipulating AWS resources

    Args:
        file_contents (str): The file to be parsed

    Returns:
        dict: Matching AWS resource action events
    '''
    result = {}

    try:
        service_matches = re.findall(SERVICE_PATTERN, file_content)
        for service_match in service_matches:
            service_parts = service_match.split('.')
            service_name = service_parts[1]  # Extract the service name

            method_pattern = re.compile(f'{re.escape(service_match)}{METHOD_PATTERN}')
            method_matches = method_pattern.findall(file_content)

            if service_name not in result:
                result[service_name] = []

            for method_match in method_matches:
                method_name = method_match.split('.')[-1]  # Extract the method name
                result[service_name].append(method_name)

    except Exception as e:
        logger.error("Error parsing C# file: %s", str(e))
        return {}

    return result
