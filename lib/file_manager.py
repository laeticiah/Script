import csv
import yaml

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

def write_to_csv(writer: csv.writer, repo_row_data: list):
    """
    Writes information into the CSV.

    Args:
        writer: CSV writer instance.
        repo_row_data: List with repository information to write.

    """
    writer.writerow(repo_row_data)

def create_csv_writer(file_path: str):
    """
    Return a CSV writer instance for the given file path.
    
    Args:
        file_path: Path to the CSV file.

    Returns:
        CSV writer instance.
    """
    file = open(file_path, mode='w', newline='', encoding='utf-8')
    writer = csv.writer(file)
    return writer
