import os
import pickle
from common.logger import get_logger

logger = get_logger(__name__)

def load_list_from_file(filepath):
    try:
        with open(filepath, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return []

def load_swears(filepath):
    swears = {'not_bad': [], 'bad': [], 'really_bad': []}
    try:
        with open(filepath, 'r') as file:
            for line in file:
                if ',' in line:
                    severity, swear = line.strip().split(',', 1)
                    if severity in swears:
                        swears[severity].append(swear)
    except FileNotFoundError:
        logger.error(f"Swears file not found: {filepath}")
    return swears

def load_pickle(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'rb') as file:
            return pickle.load(file)
    return {}

def save_pickle(filepath, data):
    with open(filepath, 'wb') as file:
        pickle.dump(data, file)