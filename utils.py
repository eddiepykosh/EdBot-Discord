import json
import os
import pickle
import tempfile
from common.logger import get_logger

logger = get_logger(__name__)

class _RestrictedLegacyUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        raise pickle.UnpicklingError("Global objects are not allowed in legacy state files")

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

def load_json_file(filepath, default=None):
    if default is None:
        default = {}
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Error loading JSON file {filepath}: {e}")
        return default

def save_json_atomic(filepath, data):
    directory = os.path.dirname(filepath) or "."
    os.makedirs(directory, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile('w', dir=directory, delete=False) as temp_file:
            temp_path = temp_file.name
            json.dump(data, temp_file, indent=2)
            temp_file.write("\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, filepath)
    except OSError as e:
        logger.error(f"Error saving JSON file {filepath}: {e}")
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                logger.warning(f"Failed to remove temporary file {temp_path}")
        raise

def save_bytes_atomic(filepath, data):
    directory = os.path.dirname(filepath) or "."
    os.makedirs(directory, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile('wb', dir=directory, delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(data)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, filepath)
    except OSError as e:
        logger.error(f"Error saving file {filepath}: {e}")
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                logger.warning(f"Failed to remove temporary file {temp_path}")
        raise

def load_json_state(filepath, default=None, legacy_pickle_path=None):
    if default is None:
        default = {}
    if os.path.exists(filepath):
        return load_json_file(filepath, default)
    if legacy_pickle_path and os.path.exists(legacy_pickle_path):
        try:
            with open(legacy_pickle_path, 'rb') as file:
                data = _RestrictedLegacyUnpickler(file).load()
            save_json_atomic(filepath, data)
            logger.info(f"Migrated legacy pickle state {legacy_pickle_path} to {filepath}")
            return data
        except Exception as e:
            logger.error(f"Error migrating legacy pickle state {legacy_pickle_path}: {e}")
            return default
    return default
