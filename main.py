import argparse
import logging
from github import GithubException
from lib.github_manager import init_github, analyze_repo
from lib.env_manager import load_env_var
from lib.file_manager import load_config, create_csv_writer, write_to_csv
from lib.logger import setup_logger

logger = setup_logger()

def main(user_or_org, config_file, output_file, g):
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
    writer = create_csv_writer(output_file)
    
    # write headers to the csv file
    write_to_csv(writer, ["Repository", "Type", "File Path", "URL", "Created On", "Last Commit", "Languages", "Branch Protection", "Required Checks Enforcement Level", "Repo Archived", "Analysis Result"])

    for idx, repo in enumerate(repos[0:]):
        print(f"Processing repo #{idx+1}: {repo.full_name}")
        analyze_repo(repo, config, writer)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script to identify devops assets in github')
    parser.add_argument('user_or_org', help='Name of the Github Identity to target', default='stelligent')
    parser.add_argument('config_file', help='Config file to use of assets to match', default='parsers/config.yaml')
    parser.add_argument('output_file', help='Name of the file to write out', default='identified_assets.csv')
    args = parser.parse_args()

    gh_token = load_env_var('GH_TOKEN')
    g = init_github(gh_token)

    try:
        main(args.user_or_org, args.config_file, args.output_file, g)
    except Exception as e:
        logger.exception(f'Error while processing repositories: {e}')
