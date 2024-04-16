'''
GitHub Repository analysis
'''
from typing import List, Dict, Any, Optional
import collections
from github import Github, GithubException, Repository, ContentFile, Branch  # type: ignore

from lib.file_manager import process_and_analyze_file, create_match_function
from lib.logger import setup_logger

# pylint: disable=line-too-long

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
                logger.info('processing: %s', file)
                if file.type == "dir":
                    queue.extend(repo.get_contents(file.path))
                elif match_function(file):
                    matched_files.append(file)
        else:  # single 'content' item
            logger.info('processing: %s', file_content)

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

    _gh_languages: dict[str, int] = a_repo.get_languages()
    _languages: str = ' '.join(str(x) for x in _gh_languages.keys())
    _labels: list[str] = [label.name for label in a_repo.get_labels()] # Changed _labels extraction to avoid possible key errors
    branch_meta: Branch.Branch = a_repo.get_branch(branch=a_repo.default_branch)

    _protection: dict[str, Any] = branch_meta.raw_data.get("protection", {}) if 'protection' in branch_meta.raw_data else {}
    _project_status: Optional[str] = _protection.get("enabled", None)
    _protection_enforcement_level: bool = _protection.get("required_status_checks", {}).get("enforcement_level", None)

    # creating a more complete capture of the available repo's metadata
    # since some of it will probably be used later
    metadata: dict[str, Any] = {
        "full_name": a_repo.full_name,
        "created_at": (a_repo.created_at).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_commit_on_default": (a_repo.pushed_at).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "primary_language": a_repo.language,
        "gh_languages": _gh_languages,
        "languages": _languages,
        "labels": _labels,
        "topics": a_repo.topics,
        "branch_default": a_repo.default_branch,
        "branch_protection": _protection,
        "branch_protection_status": _project_status,
        "branch_protection_enforcement_level": _protection_enforcement_level,
        "archived": a_repo.archived
    }
    logger.debug("repo metadata: %s", metadata)

    # this is a minimized repo's metadata object containing all that
    # is being consumed for now
    min_metadata: dict[str, Any] = {
        "created_at": metadata.get('created_at'),
        "last_commit_on_default": metadata.get('last_commit_on_default'),
        "languages": metadata.get('languages'),
        "branch_protection_status": metadata.get('branch_protection_status'),
        "branch_protection_enforcement_level": metadata.get('branch_protection_enforcement_level'),
        "archived": metadata.get('archived')
    }
    logger.debug("repo min_metadata: %s", min_metadata)

    return min_metadata


def format_row_data(a_repo: Repository.Repository, a_type: str, content: ContentFile, br_metadata: dict[str, Any], analysis) -> List[str]:
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
        br_metadata.get('languages'),
        br_metadata.get('branch_protection_status'),
        br_metadata.get('branch_protection_enforcement_level'),
        br_metadata.get('archived'),
        analysis if analysis else "N/A"
    ]
    return formatted_row


def analyze_repo(repo: Repository.Repository, config: List[Dict[str, Any]]):
    """ Analyze a single Github repository based on a provided configuration """
    logger.info("Processing repo: %s", repo.full_name)

    # Extract metadata
    branch_metadata: dict[str, Any] = get_repo_metadata(a_repo=repo)

    # Pre-Fetch all files from repo
    all_files = extract_files_from_repo(repo)

    config_with_match_functions = []
    for asset in config:
        # Check asset structure.
        # If a certain asset is malformed in the configuration, don't break the loop, skip it.
        if "matchType" not in asset or (asset['matchType']=='file' and "file_match" not in asset):
            logger.warning("Asset structure is incorrect: %s", asset)
            continue

        asset_with_match_function = asset.copy()
        asset_with_match_function['match_function'] = create_match_function(asset=asset)
        config_with_match_functions.append(asset_with_match_function)

    full_data = []
    for file_content in all_files:
        for asset_with_match_function in config_with_match_functions:
            if asset_with_match_function['match_function'](file_content):
                try:
                    # row_data = []
                    asset_type, analysis_result = process_and_analyze_file(asset_with_match_function, file_content, repo)
                    logger.info("Got Analysis Result: %s: %s", asset_type, analysis_result)
                    row_data: List[str] = format_row_data(
                        repo, asset_type, file_content, branch_metadata, analysis_result)
                    full_data.append(row_data)
                except GithubException as e:
                    logger.error("Error processing repo %s: %s", repo.full_name, e)
                    continue
                except Exception as e:
                    logger.error("Failed to process file %s: %s", file_content.path, str(e))
                    continue
    return full_data
