from dotenv import load_dotenv # type: ignore
import os
from lib.logger import setup_logger


logger = setup_logger(__name__)

def load_env_var(var_name:str):
    """
    Load an environment variable and return its value.

    Args:
        var_name : Name of environment variable to load.

    Returns:
        Environment variable value

    Raises:
        ValueError: If no environment variable exists with the given name.
    """
    load_dotenv()
    var_value = os.getenv(var_name)

    if not var_value:
        logger.error(f'Environment variable {var_name} is required')
        raise ValueError(f'Environment variable {var_name} is required')

    return var_value