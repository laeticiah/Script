from lib.parsers import cloudformation_parser, terraform_parser
from dotenv import load_dotenv
from github import Github, Branch, ContentFile, Repository, GithubException
from typing import Any, Dict, List
import argparse
import collections
import csv
import fnmatch
import logging
import os
import yaml


# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('logs.log')

# Create formatters and add it to handlers
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

class ParserNotFound(Exception):
    pass

def load_env() -> str:
    """
    Load environment variables and return Github token.

    Returns:
        Github access token string.

    Raises:
        ValueError: If Github access token is not set as an environment variable.
    """
    load_dotenv()
    gh_token = os.getenv('GH_TOKEN')

    if not gh_token:
        logger.error('GitHub token is required')
        raise ValueError('GitHub token is required')

    return gh_token


def init_github(github_token: str) -> Github:
    """
    Initialize Github instance with the provided token.

    Args:
        github_token: The user's Github personal access token.

    Returns:
        Github instance.
    """
    return Github(github_token)


def load_config(config_file: str) -> dict:
    """
    Load configuration parameters from a YAML file.

    Args:
        config_file: The path to the configuration file.

    Returns:
        Dictionary containing the configurations.
    """
    with open(config_file,'r') as conf_file:
        config = yaml.safe_load(conf_file)

    return config


def extract_files_from_repo(repo: Repository.Repository, match_function: callable) -> List[ContentFile.ContentFile]:
    """
    Extracts the list of files from the repository that match a specified condition.

    Args:
        repo: The Github Repository object
        match_function: A callable that takes a Github File Content object
            and returns True if the file should be included in the result

    Returns:
        A list of Github File Content objects in the repo that match the specified condition

    Raises:
        GithubException: If there's an error accessing the Github API
    """
    matched_files = []
    queue = collections.deque([repo.get_contents("")])

    while queue:
        file_content = queue.popleft()

        if isinstance(file_content, list):  # multiple 'content' items are received
            for file in file_content:
                logger.info(f'\nprocessing: {file} {file.type}\n')
                if file.type == "dir":
                    queue.extend(repo.get_contents(file.path))
                elif match_function(file):
                    matched_files.append(file)
        else:  # single 'content' item
            if file_content.type == "dir":
                queue.extend(repo.get_contents(file_content.path))
            elif match_function(file_content):
                matched_files.append(file_content)

    return matched_files


def get_repo_metadata(a_repo: Repository.Repository) -> dict[str, Any]:
    """
    Extracts selected metadata from a repository for further analysis.

    This function retrieves details like the full name, creation time, last commit time,
    languages in use, labels, topics, default branch details, and if the repo is archived.

    Args:
        a_repo (Repository.Repository): A Github Repository object

    Returns:
        dict[str, Any]: A dictionary containing retrieved repository metadata
    """

    _languages: dict[str, int] = a_repo.get_languages()
    _labels: list[str] = [label.name for label in a_repo.get_labels()] # Changed _labels extraction to avoid possible key errors
    branch_meta: Branch.Branch = a_repo.get_branch(branch=a_repo.default_branch)

    _protection: dict[str, Any] = branch_meta.raw_data.get("protection", {}) if 'protection' in branch_meta.raw_data else {}

    metadata: dict[str, Any] = {
        "full_name": a_repo.full_name,
        "created_at": (a_repo.created_at).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_commit_on_default": (a_repo.pushed_at).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "primary_language": a_repo.language,
        "languages": _languages,
        "labels": _labels,
        "topics": a_repo.topics,
        "branch_default": a_repo.default_branch,
        "branch_protection": _protection,
        "archived": a_repo.archived
    }

    return metadata


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
    logger.debug(f'\parser: {asset.get("parse_function")}\n')

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


def write_to_csv(writer: csv.writer, repo: Repository.Repository, asset_type: str,
                 file_content: ContentFile.ContentFile, branch_metadata: dict,
                 analysis_result: str):
    """
    Writes information into the CSV.

    Args:
        writer: CSV writer instance.
        repo: Github Repository object.
        asset_type: Type of the asset.
        file_content: Github File Content object.
        branch_metadata: Metadata of the Github repository's branch.
        analysis_result: Result from the repository file analysis.
    """
    github_languages = ' '.join(str(x) for x in (branch_metadata.get("languages",{})).keys())
    branch_protection_status = branch_metadata.get("branch_protection", {}).get("enabled", None)
    branch_protection_enforcement_level = branch_metadata.get("branch_protection", {}).get("required_status_checks", {}).get("enforcement_level", None)

    writer.writerow([
        repo.full_name,
        asset_type,
        file_content.path,
        file_content.html_url,
        branch_metadata.get("created_at"),
        branch_metadata.get("last_commit_on_default"),
        github_languages,
        branch_protection_status,
        branch_protection_enforcement_level,
        branch_metadata.get("archived"),
        analysis_result
    ])


def match_file(file_name: str, file_match: str) -> bool:
    return fnmatch.fnmatch(file_name, file_match)


def match_content(file_content: ContentFile.ContentFile, content_match: list) -> bool:
    decoded_content = file_content.decoded_content.decode('utf-8')
    return any(match in decoded_content for match in content_match)


def create_match_function(asset: dict):
    """
    Creates a match function for a given asset.
    
    Args:
        asset: The configurations for the parse function and match type.

    Returns:
        A callable that takes a Github File Content object
        and returns True if the file or its content matches the asset configuration.
    """
    # Define the match function logic based on 'matchType'
    if asset['matchType'] == 'file':
        # Use the 'match_file' function if 'matchType' is 'file'
        return lambda file_content: match_file(file_content.path, asset['file_match'])
    elif asset['matchType'] == 'content':
        # Use the 'match_content' function if 'matchType' is 'content'
        return lambda file_content: match_content(file_content, asset['content_match'])

    # Default match function in case of unsupported 'matchType'
    return lambda file_content: False


def analyze_repo(repo: Repository.Repository, config: List[Dict[str, Any]], writer: csv.writer):
    """ Analyze a single Github repository based on a provided configuration """
    logger.info(f"Processing repo: {repo.full_name}")

    # Extract metadata
    branch_metadata = get_repo_metadata(a_repo=repo)

    for asset in config:
        # Check asset structure.
        # If a certain asset is malformed in the configuration, don't break the loop, skip it.
        if "matchType" not in asset or (asset['matchType']=='file' and "file_match" not in asset):
            logger.warning(f"Asset structure is incorrect: {asset}")
            continue

        match_function = create_match_function(asset=asset)
        print(match_function)
        # Extract files based on the match_function
        files = extract_files_from_repo(repo, match_function)
        print("files",files)
        for file_content in files:
            # logger.info("Running in,", file_content.path)
            try:
                asset_type, analysis_result = process_and_analyze_file(asset, file_content, repo)
                # Write info to the CSV
                write_to_csv(writer, repo, asset_type, file_content, branch_metadata, analysis_result)
            except Exception as e: 
                logger.error(f"Failed to process file {file_content.path}: {str(e)}")
            except GithubException as e:
                logger.error(f"Error processing repo {repo.full_name}: {e}")
            except ParserNotFound as e: 
                logger.warning(f"Could not find parser for the asset {asset['file_match']}: {e}")


def main(user_or_org, config_file, output_file):
    """Run the script."""
    try:
        repos = g.get_user(user_or_org).get_repos()
    except GithubException:
        repos = g.get_organization(user_or_org).get_repos()
    
    # if there are repos, proceed, otherwise exit
    if repos.totalCount > 0:
        print(f'\n{repos.totalCount} repos found for User or Org {user_or_org}. Beginning processing.\n')
    else:        
        print(f'\nNo repos found for User or Org {user_or_org}. Nothing to process so ending.\n')
        return

    config = load_config(config_file)

    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Repository", "Type", "File Path", "URL", "Created On", "Last Commit", "Languages", "Branch Protection", "Required Checks Enforcement Level", "Repo Archived", "Analysis Result"])

        for idx, repo in enumerate(repos[0:]):
            print(f"Processing repo #{idx+1}: {repo.full_name}")
            analyze_repo(repo, config, writer)
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script to identify devops assets in github')
    parser.add_argument('user_or_org', help='Name of the Github Identity to target', default='stelligent')
    parser.add_argument('config_file', help='Config file to use of assets to match', default='parsers/config.yaml')
    parser.add_argument('output_file', help='Name of the file to write out', default='identified_assets.csv')
    args = parser.parse_args()

    gh_token = load_env()
    g = init_github(gh_token)

    try:
        main(args.user_or_org, args.config_file, args.output_file)
    except Exception as e:
        logger.exception(f'Error while processing repositories: {e}')

        #316, 278, 275,251,107, edited
