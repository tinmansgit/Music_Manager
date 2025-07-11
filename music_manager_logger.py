import logging
from datetime import datetime

current_date = datetime.now().strftime('%Y-%m-%d')
error_log_file = f'/home/coder/bin/Python/Music_Manager/logs/log_error_music_manager_{current_date}.log'
debug_log_file = f'/home/coder/bin/Python/Music_Manager/logs/log_debug_music_manager_{current_date}.log'

logger = logging.getLogger('app_logger')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')

error_handler = logging.FileHandler(error_log_file, mode='a', encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)

debug_handler = logging.FileHandler(debug_log_file, mode='a', encoding='utf-8')
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(formatter)
logger.addHandler(debug_handler)

def log_error(message):
    try:
        logger.error(message)
    except IOError as e:
        print(f"Failed to log error to {error_log_file}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while logging: {e}")

def log_debug(message):
    try:
        logger.debug(message)
    except IOError as e:
        print(f"Failed to log debug message to {debug_log_file}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while logging: {e}")
