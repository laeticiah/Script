'''
Main entry point to the crawler
'''
import argparse
from multiprocessing import Pool
from github import GithubException  # type: ignore
from lib.github_manager import init_github, analyze_repo
from lib.env_manager import load_env_var
from lib.file_manager import load_config, create_csv_writer
from lib.logger import setup_logger

# pylint: disable=line-too-long

logger = setup_logger(__name__)

def process_repo(idx_repo_config):
    '''
    Processes GitHub repositories, pulling the metadata and parsing files
    for configuration matches

    Args:
        idx_repo_config (tuple): Contains the repo # being processed, the repo
        and the config file used for analysis

    Returns:
        _type_: _description_
    '''
    idx, repo, config = idx_repo_config
    try:
        logger.info("Processing repo #%s: %s", idx+1, repo.full_name)
        result_row = analyze_repo(repo, config)
        return result_row
    except Exception as e:
        logger.error('Error while processing repository: %s, %s', repo, e)
        return []


def main(user_or_org, config_file, output_file, gh_endpoint):
    """Run the script."""
    try:
        gh_token = load_env_var('GH_TOKEN')
        g = init_github(gh_token, gh_endpoint)
        repos = g.get_user(user_or_org).get_repos()
    except GithubException:
        repos = g.get_organization(user_or_org).get_repos()

    # if there are repos, proceed, otherwise exit
    if repos.totalCount > 0:
        logger.info('%s repos found for User or Org %s. Beginning processing.', repos.totalCount, user_or_org)
    else:
        logger.info('No repos found for User or Org %s. Nothing to process so ending.', user_or_org)
        return

    config = load_config(config_file)
    repos_list = enumerate(list(repos))

    # Create a Pool of subprocesses
    with Pool() as pool:
        result_rows = pool.map(process_repo, [(idx, repo, config) for idx, repo in repos_list])

    logger.debug('Pools --> # of result_rows: %s', len(result_rows) if result_rows is not None else None)
    logger.debug('Pools --> result_rows: %s', result_rows)

    # After all the multiprocessing is done, write to csv
    writer = create_csv_writer(output_file)

    # write headers to the csv file
    row_headers: list[str] = [
        "Repository", "Type", "File Path", "URL", "Created On", "Last Commit",
        "Languages", "Branch Protection", "Required Checks Enforcement Level",
        "Repo Archived", "Analysis Result"
    ]
    writer.writerow(row_headers)

    # write out the results
    for idx, result_row in enumerate(result_rows):
        if result_row is not None: # and len(result_row) == len(row_headers):
            logger.debug('result_row #%s: %s', idx+1, result_row)
            try:
                if isinstance(result_row[0], list):
                    writer.writerows(result_row)
                else:
                    writer.writerow(result_row)
            except Exception as e:
                logger.error('Error while writing to file: %s', e)
        else:
            logger.warning('ISSUE with result_row #%s, will not output to file. result_row: %s', idx+1, result_row)

    logger.info("Completed processing %s repos.", repos.totalCount)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script to identify devops assets in github')
    parser.add_argument('user_or_org', help='Name of the Github Identity to target', default='stelligent')
    parser.add_argument('config_file', help='Config file to use of assets to match', default='config.yaml')
    parser.add_argument('output_file', help='Name of the file to write out', default='identified_assets.csv')
    parser.add_argument(
        'gh_endpoint', help='Hostname for your GitHub Enterprise instance - https://github.com/api/v3', default='https://api.github.com')
    args = parser.parse_args()

    main(args.user_or_org, args.config_file, args.output_file, args.gh_endpoint)
    logger.info("devops assets written to %s!", args.output_file)
