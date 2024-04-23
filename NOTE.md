# NOTES

- config = list[Dict[str, Any]]
- asset = Dict[str, Any]

## Method Flow -

`method(signature)->return_type`

- main() -> args
- load_config(config_file) -> config
- load_env_var(github_token) -> github_token
- init_github(github_token, github_endpoint) -> github_client
- retrieve_repos(github_client, user_or_org) -> repos:List[str]
- process_repos(repos, config, args.output_file) -> csv
- - prepare_match_functions(config) -> List[Dict[str,Any]]match_functions
- - create_match_function(asset) -> lambda
- - pool.starmap(analyze_repo)(a_repo, match_functions) -> List[processed_data]
- - - get_repo_metadata(a_repo)
- - - extract_files_from_repo(a_repo) -> List[file]
- - - process_and_analyze_file() -> List[file]
- - - - parsers
- - - - - decode_content
- - - - - parse_function
- - - - - format_row_data
- - - create_csv_writer(args.output_file)
- - - writer.writerow(processed_data)
- logger.info
