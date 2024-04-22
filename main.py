"""github crawler."""


import argparse
import csv
from typing import Optional
from github import GithubException, RateLimitExceededException

from lib.github_manager import init_github, retrieve_repos, process_repos
from lib.env_manager import load_env_var
from lib.file_manager import load_config
from lib.logger import setup_logger

# pylint: disable=line-too-long

logger = setup_logger(__name__)


def main(config_path: str, user_or_org: str, output_file: str, gh_endpoint: str, repository: Optional[str]):
    """Run the script."""

    try:
        # Get Github token
        gh_token = load_env_var("GH_TOKEN")
        g = init_github(gh_token, gh_endpoint)

        config = load_config(config_path)
        if not config:
            return

        headers = config.get('headers')
        config_assets = config.get('assets')

        # Retrieve repositories
        repos = retrieve_repos(g, user_or_org, repository)

        if not repos:
            logger.info("No repos found for '%s'. Exiting.", user_or_org)
            return

        logger.info("")
        logger.info("Starting to process %s repos ...", len(list(repos)))
        # Open CSV file for appending (modify based on your CSV handling logic)
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header row
            writer.writerow(headers)

        # Process the repos
        process_repos(repos, config_assets, output_file)

        logger.info("Completed processing repos.")

    except RateLimitExceededException as e:
        logger.error("Github API rate limit exceeded: %s", e)
    except GithubException as e:
        logger.error("An error occurred accessing Github: %s", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to identify DevOps assets in GitHub")
    parser.add_argument("user_or_org",
                        help="Name of the Github user or organization to target")
    parser.add_argument("config_path",
                        help="Path to the configuration file (config.yaml)")
    parser.add_argument("output_file",
                        help="Name of the file to write out the identified assets")
    parser.add_argument("gh_endpoint",
                        help="api endpoint for github",
                        default="https://api.github.com")
    parser.add_argument("-r", "--repo",
                        help="The name of a specific GitHub repository to analyze",
                        dest="repository",
                        required=False)
    args = parser.parse_args()

    main(args.config_path, args.user_or_org, args.output_file, args.gh_endpoint, args.repository)
    logger.info("Devops assets written to '%s'!", args.output_file)
