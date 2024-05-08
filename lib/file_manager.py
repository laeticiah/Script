"""Module providing file handling utils"""

import csv
import fnmatch
from typing import Any, Callable, Dict, List

# import chardet
import yaml
from github import ContentFile, Repository

from lib.logger import setup_logger
from lib.parsers import (
    ansible_parser,
    boto3_parser,
    cloudformation_parser,
    pshell_parser,
    shell_parser,
    terraform_parser,
    js_parser,
    java_parser,
    ruby_parser,
    chef_parser,
    csharp_parser,
    springcloud_parser,
    groovy_parser,
    dotnet_parser,
    java_property_parser,
    manifest_parser,
    jupyter_parser
)

# pylint: disable=line-too-long

logger = setup_logger(__name__)


def load_config(config_path: str):
    """
    Load configuration parameters from a YAML file.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as stream:
            raw = yaml.safe_load(stream)
        return raw
    except yaml.YAMLError as e:
        logger.error("Error loading config: %s", e)
        return None


def create_csv_writer(file_path: str):
    """
    Return a CSV writer instance for the given file path.

    Args:
        file_path: Path to the CSV file.

    Returns:
        CSV writer instance.
    """
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        return writer


def format_row_data(a_repo: Repository.Repository,
                    a_type: str,
                    content: ContentFile,
                    br_metadata: dict[str, Any], analysis) -> List[str]:
    '''
    Transforms raw row data into the final output format to be written out to a file
    '''
    formatted_row: list[str] = [
        a_repo.full_name,
        a_type,
        content.path,
        content.html_url,
        br_metadata.get("created_at"),
        br_metadata.get("last_commit_on_default"),
        br_metadata.get('branch_protection_status'),
        br_metadata.get('branch_protection_enforcement_level'),
        br_metadata.get('archived'),
        analysis if analysis else "N/A"
    ]
    return formatted_row


def match_file(file_content: ContentFile.ContentFile, file_match: str, _) -> bool:  # pylint: disable=unused-argument
    """
    Checks that the file name matches a specified pattern

    Args:
        file_content: A ContentFile object containing the file content.
        file_match:   A file name pattern to match the name against.

    Returns:
        True if any match is found, False otherwise.

    """
    logger.debug("File name: %s", file_content.name)
    logger.debug("File name match pattern: %s", file_match)
    try:
        return fnmatch.fnmatch(file_content.name, file_match)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed matching file name and file_match for file %s: %s", file_content.path, e)
        return False


def match_content(file_content: ContentFile.ContentFile, file_match: str, content_match: list) -> bool:
    """
    This function checks that the file name matches a specified pattern and then
    attempts to decode the content of a ContentFile object, which is then checked
    for matches with any of the provided strings in content_match.

    Args:
        file_content  (obj): A ContentFile object containing the file content.
        file_match    (str): A file name pattern to match the name against.
        content_match (list): A list of strings to match against the decoded content.

    Returns:
        True if any match is found, False otherwise.
    """
    logger.debug("File name: %s", file_content.name)
    logger.debug("Filename match pattern: %s", file_match)
    logger.debug("Content match patterns: %s", content_match)
    try:
        if fnmatch.fnmatch(file_content.name, file_match):
            content = file_content.decoded_content.decode('utf-8')
            logger.debug("content: %s", content)
            if content is not None:
                return any(match in content for match in content_match)
        return False
    except (UnicodeDecodeError, AttributeError):
        # Handle cases where decoding fails or encoding is not available
        logger.warning("Failed to decode content for file: %s", file_content.name)
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed matching file content, file_match, content_match for file %s: %s", file_content.path, e)
        return False


def create_match_function(asset: dict):
    """
    Creates a match function for a given asset.

    Args:
        asset: The configurations for the parse function and match type.

    Returns:
        A dictionary containing the match function, its arguments, associated parser and match_type.
    """
    asset_type: str = asset.get('type')
    match_type = asset.get('matchType', None)
    parser = asset.get('parse_function', None)

    if match_type == 'file':
        file_match_fn = {'match_function': match_file, 'args': (
            asset.get('file_match'), None,), 'parser': parser, 'asset_type': asset_type}
        logger.debug("match_file file_match_fn: %s", file_match_fn)
        return file_match_fn

    if asset.get('matchType') == 'content':
        content_match_fn = {'match_function': match_content, 'args': (asset.get('file_match'),
                                                                      asset.get('content_match', []),), 'parser': parser, 'asset_type': asset_type}
        logger.debug("match_content content_match_fn: %s", content_match_fn)
        return content_match_fn

    return {'match_function': lambda file_content: False, 'args': (), 'parser': None, 'asset_type': None}


def prepare_match_functions(config: List[Dict[str, Any]]) -> List[Callable[[ContentFile.ContentFile], bool]]:
    """
    Prepares match functions from a list of asset configurations.

    This function iterates through the configurations and creates a list of
    callable match functions directly.

    Args:
        config: A list of dictionaries containing asset configurations.

    Returns:
        A list of callable match functions.
    """
    match_functions = []
    for asset in config:
        match_functions.append(create_match_function(asset))

    logger.debug("match_function: %s", match_functions)
    return match_functions


def process_and_analyze_file(parser: str,
                             asset_type: str,
                             file_content: ContentFile.ContentFile):
    """
    Process and analyze a given file based on the asset configurations.

    Args:
        parser: The parse function
        file_content: Github File Content to be analyzed.
        repo: Github Repository object where the file content is from.

    Returns:
        asset_type: A string that describes the type of asset.
        analysis_result: A string representing the result from the parse function,
                         or None if there's an error.
    """
    logger.debug("parser: %s, match_type: %s", parser, asset_type)

    # Use a dictionary for parsers
    parsers = {
        'ansible': ansible_parser.parse_ansible_file,
        'boto3': boto3_parser.parse_boto3_file,
        'cloudformation': cloudformation_parser.parse_cloudformation_file,
        'powershell': pshell_parser.parse_powershell_file,
        'shell': shell_parser.parse_shell_file,
        'terraform': terraform_parser.parse_terraform_file,
        'javascript': js_parser.parse_js_file,
        'java': java_parser.parse_java_file,
        'ruby': ruby_parser.parse_ruby_file,
        'chef': chef_parser.parse_chef_file,
        'csharp': csharp_parser.parse_csharp_file,
        'springcloud': springcloud_parser.parse_springcloud_file,
        'groovy': groovy_parser.parse_groovy_file,
        'dotnet': dotnet_parser.parse_dotnet_file,
        'manifest': manifest_parser.parse_manifest_file,
        'java_property': java_property.parse_java_property_file,
        'jupyter': jupyter_parser.parse_jupyter_file,
    }

    parse_function = parsers.get(parser)
    logger.debug("parse_function: %s", parse_function)
    if not parse_function:
        logger.warning('Invalid parse function specified for asset type: %s', asset_type)
        return None  # Or raise an exception

    if not callable(parse_function):
        logger.error('Parser for asset type %s is not callable', asset_type)
        return None  # Or raise an exception

    # logger.debug("raw_content: %s", file_content)
    decoded_content = file_content.decoded_content.decode()
    analysis_result = parse_function(decoded_content)
    logger.debug("analysis_result: %s", analysis_result)

    return analysis_result
