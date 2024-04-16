# corebridge-github-crawler

Github crawler for identifying Infrastructure provisioning assets

## Running the Crawler

VSCode - Reopen in Container

    python main.py <github_user_or_org> <config_file> <output_file> <github_endpoint>

### Alternatively

    `make` -> run tests
    `make test` -> run tests
    `make run` -> run gh_crawler

#### Folder Structure

```yaml
- lib /
    - parsers /
        - ansible_parser.py
        - boto3_parser.py
        - cloudformation_parser.py
        - terraform_parser.py
    - env_manager.py
    - file_manager.py
    - github_manager.py
    - logger.py
- resources /
    - boto3_script.py
    - cluster.yaml
    - create-and-use-custom-resource.json
    - db-instance.config
    - ec2.tf
    - ec2.yml
    - no_boto3_calls.py
- tests /
    - lib /
        - parsers /
            - test_ansible_parser.py
            - test_boto3_parser.py
            - test_cloudformation_parser.py
            - test_terraform_parser.py
        - test_env_manager.py
        - test_file_manager.py
        - test_github_manager.phy
    - test_main.py
- config.yaml
- main.py
- Makefile
- README.md
- requirements.txt
- output.csv
```
