from github import ContentFile, Repository # type: ignore
import csv
import fnmatch
import yaml # type: ignore

from lib.parsers import cloudformation_parser, terraform_parser, boto3_parser, pshell_parser, shell_parser, ansible_parser
from lib.logger import setup_logger


logger = setup_logger(__name__)


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


def match_file(file_name: str, file_match: str) -> bool:
    return fnmatch.fnmatch(file_name, file_match)


def match_content(file_content: ContentFile.ContentFile, content_match: list) -> bool:
    decoded_content = decode_content(file_content)
    return any(match in decoded_content for match in content_match)


def decode_content(file_content: ContentFile.ContentFile) -> str:
    """
    Decodes the file content.

    Args:
        file_content: Github File Content to decode.

    Returns:
        A string representing the decoded content of the file.
    """
    encodings = [
    'ascii', 'big5', 'big5hkscs', 'cp037', 'cp273', 'cp424', 'cp437', 'cp500', 'cp720',
    'cp737', 'cp775', 'cp850', 'cp852', 'cp855', 'cp856', 'cp857', 'cp858', 'cp860',
    'cp861', 'cp862', 'cp863', 'cp864', 'cp865', 'cp866', 'cp869', 'cp874', 'cp875',
    'cp932', 'cp949', 'cp950', 'cp1006', 'cp1026', 'cp1125', 'cp1140', 'cp1250',
    'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256', 'cp1257', 'cp1258',
    'cp65001', 'euc_jp', 'euc_jis_2004', 'euc_jisx0213', 'euc_kr', 
    'gb2312', 'gbk', 'gb18030', 'hz', 'iso2022_jp', 'iso2022_jp_1', 'iso2022_jp_2',
    'iso2022_jp_2004', 'iso2022_jp_3', 'iso2022_jp_ext', 'iso2022_kr', 
    'latin_1', 'iso8859_2', 'iso8859_3', 'iso8859_4', 'iso8859_5', 'iso8859_6',
    'iso8859_7', 'iso8859_8', 'iso8859_9', 'iso8859_10', 'iso8859_11', 'iso8859_13',
    'iso8859_14', 'iso8859_15', 'iso8859_16', 'johab', 'koi8_r', 'koi8_t', 'koi8_u',
    'kz1048', 'mac_cyrillic', 'mac_greek', 'mac_iceland', 'mac_latin2', 'mac_roman',
    'mac_turkish', 'ptcp154', 'shift_jis', 'shift_jis_2004', 'shift_jisx0213',
    'utf_32', 'utf_32_be', 'utf_32_le', 'utf_16', 'utf_16_be', 'utf_16_le', 
    'utf_7', 'utf_8', 'utf_8_sig']

    for encoding in encodings:
        if encoding is None:  # If encoding is None, continue to next encoding
            continue
        try:
            decoded_content = file_content.decoded_content.decode(encoding)
            return decoded_content
        except UnicodeDecodeError:
            continue  # Try the next encoding
        except Exception as ex:
            print(f"Exception occurred with encoding '{encoding}': {ex}")
            continue  # Skip to the next encoding
    
    # If all provided encodings failed, decode with error ignored.
    decoded_content = file_content.decoded_content.decode('utf-8', 'ignore')

    return decoded_content

def create_match_function(asset: dict):
    """
    Creates a match function for a given asset.
    
    Args:
        asset: The configurations for the parse function and match type.

    Returns:
        A callable that takes a Github File Content object and
        returns True if the file or its content matches the asset configuration.
    """
    if asset['matchType'] == 'file':
        return lambda file_content: match_file(file_content.path, asset['file_match'])
    elif asset['matchType'] == 'content':
        return lambda file_content: match_content(file_content, asset['content_match'])
    return lambda file_content: False


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
    logger.debug(f"asset_type: {asset_type}")

    if asset.get("parse_function") == 'cloudformation':
        parse_function = cloudformation_parser.parse_cloudformation_file
    elif asset.get("parse_function") == 'terraform':
        parse_function = terraform_parser.parse_terraform_file
    elif asset.get("parse_function") == 'boto3':
        parse_function = boto3_parser.parse_boto3_file
    elif asset.get("parse_function") == 'powershell':
        parse_function = pshell_parser.parse_powershell_file
    elif asset.get("parse_function") == 'shell':
        parse_function = shell_parser.parse_shell_file
    elif asset.get("parse_function") == 'ansible':
        parse_function = ansible_parser.parse_ansible_file
    else:
        logger.warning(f'Invalid parse function specified for asset type: {asset_type}')
        return asset_type, analysis_result  # Return immediately if no 'parse_function'

    if callable(parse_function): 
        logger.debug(f"raw_content: {file_content}")
        decoded_content = decode_content(file_content)
        analysis_result = parse_function(decoded_content)
        logger.debug(f"analysis_result: {analysis_result}")

    logger.info(f"Matched file found: {file_content.path} in {repo.full_name}")

    return asset_type, analysis_result
