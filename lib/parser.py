from github import ContentFile, Repository
from lib.parsers import cloudformation_parser, terraform_parser
import logging
import collections

logger = logging.getLogger(__name__)

def process_and_analyze_file(asset: dict, file_content: ContentFile.ContentFile, repo: Repository.Repository) -> dict:
    """
    Process and analyze a given file based on the asset configurations.

    Args:
        asset: The configurations for the parse function and match type.
        file_content: Github File Content to be analyzed.
        repo: Github Repository object where the file content is from.

    Returns:
        asset_type: A string that describes the type of asset.
        analysis_result: A string representing the result from the parse function.
    """
    analysis_result = "N/A"  
    asset_type = asset["type"]
    logger.debug(f'\nasset_type: {asset_type}\n')

    raw_content = file_content.decoded_content.decode('utf-8')

    if asset.get("parse_function") == 'cloudformation':
        parse_function = cloudformation_parser.parse_cloudformation_file
    elif asset.get("parse_function") == 'terraform':
        parse_function = terraform_parser.parse_terraform_file
    else:
        logger.warning(f'Invalid parse function specified for asset type: {asset_type}')
        return asset_type, analysis_result  # Return immediately if no 'parse_function'

    if callable(parse_function): 
        logger.debug(f'\nraw_content: {raw_content}\n')
        analysis_result = parse_function(raw_content)
        logger.debug(f'\nanalysis_result: {analysis_result}\n')

    logger.info(f"  Matched file found: {file_content.path} in {repo.full_name}")

    return asset_type, analysis_result
