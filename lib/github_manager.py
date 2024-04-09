from github import Github, GithubException, Repository, ContentFile, Branch # type: ignore
from typing import List, Dict, Any
import collections
import csv

from lib.file_manager import write_to_csv, process_and_analyze_file, create_match_function
from lib.logger import setup_logger


logger = setup_logger(__name__)

def init_github(github_token: str, github_endpoint: str) -> Github:
    """
    Initialize Github instance with the provided token and endpoint.

    Args:
        github_token: The user's Github personal access token.
        github_endpoint: The endpoint of the Github Enterprise instance. Please replace hostname in https://hostname/api/v3/ with your GitHub Enterprise instance hostname.

    Returns:
        Github instance.
    """
    return Github(base_url=github_endpoint, login_or_token=github_token)


def extract_files_from_repo(repo: Repository.Repository, match_function: callable = lambda file: True) -> List[ContentFile.ContentFile]:
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
                logger.info(f'processing: {file}')
                if file.type == "dir":
                    queue.extend(repo.get_contents(file.path))
                elif match_function(file):
                    matched_files.append(file)
        else:  # single 'content' item
            logger.info(f'processing: {file_content}')

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


def analyze_repo(repo: Repository.Repository, config: List[Dict[str, Any]], writer: csv.writer):
    """ Analyze a single Github repository based on a provided configuration """
    logger.info(f"Processing repo: {repo.full_name}")

    # Extract metadata
    branch_metadata = get_repo_metadata(a_repo=repo)

    # Pre-Fetch all files from repo
    all_files = extract_files_from_repo(repo)

    config_with_match_functions = []
    for asset in config:
        # Check asset structure.
        # If a certain asset is malformed in the configuration, don't break the loop, skip it.
        if "matchType" not in asset or (asset['matchType']=='file' and "file_match" not in asset):
            logger.warning(f"Asset structure is incorrect: {asset}")
            continue

        asset_with_match_function = asset.copy()
        asset_with_match_function['match_function'] = create_match_function(asset=asset)
        config_with_match_functions.append(asset_with_match_function)

    for file_content in all_files:
        for asset_with_match_function in config_with_match_functions:
            if asset_with_match_function['match_function'](file_content):
                try:
                    asset_type, analysis_result = process_and_analyze_file(asset_with_match_function, file_content, repo)
                    logger.info(f"Got Analysis Result: {asset_type}: {analysis_result}")
                    write_to_csv(writer, [repo, asset_type, file_content, branch_metadata, analysis_result])
                except GithubException as e:
                    logger.error(f"Error processing repo {repo.full_name}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Failed to process file {file_content.path}: {str(e)}")
                    continue
