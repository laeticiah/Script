'''
GitHub Repository analysis
'''
import collections
import csv
import inspect
from multiprocessing import Pool
from typing import Any, Dict, List, Optional, Union

from github import (Branch, ContentFile, Github,
                    GithubException, Repository)

from lib.file_manager import (format_row_data,
                              prepare_match_functions,
                              process_and_analyze_file)
from lib.logger import setup_logger

# pylint: disable=line-too-long

logger = setup_logger(__name__)


def init_github(github_token: str, github_endpoint: str) -> Github:
    """
    Initialize Github instance with the provided token and endpoint.

    Args:
        github_token: The user's Github personal access token.
        github_endpoint: The endpoint of the Github Enterprise instance.
        Please replace hostname in https://hostname/api/v3/ with your
        GitHub Enterprise instance hostname.

    Returns:
        Github instance.
    """
    return Github(base_url=github_endpoint, login_or_token=github_token)


def extract_files_from_repo(repo: Repository.Repository) -> List[ContentFile.ContentFile]:
    """
    Extracts the list of files from the repository.

    Args:
        repo: The Github Repository object

    Returns:
        A list of Github File Content objects in the repo

    Raises:
        GithubException: If there's an error accessing the Github API
    """
    matched_files = []
    queue = collections.deque([repo.get_contents("")])

    while queue:
        file_content: Union[List[ContentFile.ContentFile], ContentFile.ContentFile] = queue.popleft()

        if isinstance(file_content, list):  # multiple 'content' items are received
            for file in file_content:
                if file.type == "dir":
                    queue.extend(repo.get_contents(file.path))

                logger.debug('Adding file to all_files list: %s', f"{repo.full_name}/{file.path}")
                matched_files.append(file)
        else:  # single 'content' item
            if file_content.type == "dir":
                queue.extend(repo.get_contents(file_content.path))

            logger.debug('Adding file to all_files list: %s', f"{repo.full_name}/{file_content.path}")
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

def get_repo_metadata(a_repo: Repository.Repository) -> dict[str, Any]:
    # ...
    _gh_languages: dict[str, int] = {}
    _languages: str = ''
    try:
        _gh_languages = a_repo.get_languages()
        _languages = ' '.join(str(x) for x in _gh_languages.keys())
    except (GithubException, AttributeError):
        logger.warning("Failed to retrieve languages for repository: %s", a_repo.full_name)

    _labels: list[str] = []
    try:
        _labels = [label.name for label in a_repo.get_labels()]
    except (GithubException, AttributeError):
        logger.warning("Failed to retrieve labels for repository: %s", a_repo.full_name)

    _protection: dict[str, Any] = {}
    _project_status: Optional[str] = None
    _protection_enforcement_level: bool = None
    try:
        branch_meta: Branch.Branch = a_repo.get_branch(branch=a_repo.default_branch)
        _protection = branch_meta.raw_data.get("protection", {}) if 'protection' in branch_meta.raw_data else {}
        _project_status = _protection.get("enabled", None)
        _protection_enforcement_level = _protection.get("required_status_checks", {}).get("enforcement_level", None)
    except (GithubException, AttributeError):
        logger.warning("Failed to retrieve branch protection details for repository: %s", a_repo.full_name)   

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
        "branch_protection_status": metadata.get('branch_protection_status'),
        "branch_protection_enforcement_level": metadata.get('branch_protection_enforcement_level'),
        "archived": metadata.get('archived')
    }
    logger.debug("repo min_metadata: %s", min_metadata)

    return min_metadata


def retrieve_repos(github_client: Github, user_or_org: str, repository: Optional[str]) -> List[Repository.Repository]:
    """Retrieves repositories based on user/org (paginated)."""
    repos = []
    try:
        if "/" in user_or_org:  # Handle organization format (username/org)
            org = user_or_org.split("/")
            if repository:
                repos.append(github_client.get_organization(org).get_repo(repository))
            else:
                for repo in github_client.get_organization(org).get_repos():
                    repos.append(repo)  # Append individual repositories
        else:
            if repository:
                repos.append(github_client.get_user(user_or_org).get_repo(repository))
            else:
                for repo in github_client.get_user(user_or_org).get_repos():
                    repos.append(repo)  # Append individual repositories
    except GithubException as e:
        logger.error("Error retrieving repos for %s: %s", user_or_org, e)

    if repos:
        logger.info("Found %s repositories:", len(repos))
        for repo in repos:
            logger.info("\t- %s", repo.full_name)

    return repos


def analyze_repo(repo: Repository.Repository, match_functions: list[dict, Any], output_file):
    """ Analyzes a single Github repository based on provided match functions.

    This function iterates through all files in the repository and applies
    the provided match functions to each file. If a match is found, it
    processes and analyzes the file.
    """

    # logger.info("-----------------------------------------")
    logger.info("Processing repo: %s", repo.full_name)
    # logger.info("-----------------------------------------")

    logger.debug("match_function: %s", match_functions)

    # Extract metadata
    branch_metadata: dict[str, Any]
    try:
        branch_metadata = get_repo_metadata(a_repo=repo)
    except GithubException as e:
        logger.error("Error getting GitHub metadata. Repository '%s'. Error: %s", repo.full_name, e)
        branch_metadata = {}

    # Check if the repository is empty
    if repo.get_contents("/"):
        # Open CSV file (modify based on your CSV handling logic)
        with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # ...
    else:
        logger.warning("Repository '%s' is empty. Skipping analysis.", repo.full_name)

        # Loop over fetched files and configurations
        for file_content in extract_files_from_repo(repo)[0:]:
            # logger.info("-----------------------------------------")
            logger.info("Analyzing file --> %s", f"{repo.full_name}/{file_content.path}")
            # logger.info("-----------------------------------------")
            for function in match_functions:
                logger.debug("single match function: %s", function)

                match_function: dict = function['match_function']
                args = function.get('args', ())  # Get optional arguments
                parser = function.get('parser', None)
                asset_type = function.get('asset_type', None)

                logger.debug("inspect match_function: %s", inspect.getsource(function['match_function']))
                logger.debug("Truthy - match_function(file_content, *args): %s", match_function(file_content, *args))

                # if the file matches the file_type, process its contents for content matches
                if match_function(file_content, *args):
                    # even though there was a match, without a defined parser, can't analyze
                    if parser is None:
                        logger.error("Error analyzing matched file '%s'. No '%s' parser defined.",
                                     f"{repo.full_name}/{file_content.path}", asset_type)
                        continue

                    try:
                        analysis_result = process_and_analyze_file(
                            parser, asset_type, file_content)
                        if analysis_result is not None and analysis_result:
                            logger.info("Got Analysis Result for '%s' (%s): %s",
                                        f"{repo.full_name}/{file_content.path}", asset_type, analysis_result)
                            row_data = format_row_data(
                                repo, asset_type, file_content, branch_metadata, analysis_result)
                            writer.writerow(row_data)

                            # since the file was matched and parsed, stop looping through
                            # any remaining potential match functions
                            break

                    except Exception as e:  # pylint: disable=broad-exception-caught
                        logger.error("Failed to process file %s: %s", file_content.path, e)
                        continue


def process_repos(repos: List[Repository.Repository], config: Dict[str, Any], output_file):
    """Processes repositories in parallel."""

    match_functions = prepare_match_functions(config)
    # Use a context manager for Pool
    with Pool() as pool:
        pool.starmap(analyze_repo, [(repo, match_functions, output_file) for repo in repos])

        ## Uncomment the line below to test with a single repo (e.g. 'test-78') and comment the line above

       # pool.starmap(analyze_repo, [(repo, match_functions, output_file) for repo in repos if repo.name == 'aws-chef'])

    logger.info("Completed process_repos")
