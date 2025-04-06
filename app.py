from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaDocument
from tqdm import tqdm
import os
import logging
import time
import configparser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

api_id = config.get('Telegram', 'api_id', fallback='0')
api_hash = config.get('Telegram', 'api_hash', fallback='0')
group_username = config.get('Telegram', 'group_username', fallback='')
download_folder = config.get('Paths', 'download_folder', fallback='downloads')
mode = config.get('General', 'mode', fallback='download').lower()

# Update the configuration to read allowed file extensions from the config file
allowed_extensions = config.get('General', 'allowed_extensions', fallback='.pdf').split(',')
allowed_extensions = [ext.strip().lower() for ext in allowed_extensions]

if not os.path.exists(download_folder):
    os.makedirs(download_folder)

def download_file(client, message, file_path):
    max_retries = 3
    retry_delay = 5  # seconds

    # Append message datetime as a timestamp to the file
    base, ext = os.path.splitext(file_path)
    timestamp = message.date.strftime('%Y%m%d_%H%M%S')
    file_path = f"{base}_{timestamp}{ext}"

    # Check if file exists and skip if the file size matches
    if os.path.exists(file_path):
        local_file_size = os.path.getsize(file_path) / (1024 * 1024)
        msg_file_size = (message.file.size / (1024 * 1024)) if message.file else 0
        if local_file_size == msg_file_size:
            logging.info(f"Skipping (already exists): {message.file.name}")
            return

    for attempt in range(max_retries):
        try:
            local_file_size = os.path.getsize(file_path) / (1024 * 1024) if os.path.exists(file_path) else 0
            msg_file_size = (message.file.size / (1024 * 1024)) if message.file else 0
            logging.info(f"Local file size: {local_file_size:.2f} MB, Message file size: {msg_file_size:.2f} MB")

            logging.info(f"Downloading: {message.file.name} (Date: {message.date})")

            with tqdm(total=message.file.size, unit='B', unit_scale=True, desc=message.file.name) as pbar:
                def progress_callback(current, total):
                    pbar.update(current - pbar.n)

                client.download_media(message, file=file_path, progress_callback=progress_callback)
            return  # Exit the loop if download is successful
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed for {message.file.name}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logging.error(f"Failed to download {message.file.name} after {max_retries} attempts")

with TelegramClient('anon', api_id, api_hash) as client:
    file_counter = 0
    for message in client.iter_messages(group_username):
        if message.media and isinstance(message.media, MessageMediaDocument):
            if message.file and message.file.name and any(message.file.name.lower().endswith(ext) for ext in allowed_extensions):
                file_counter += 1
                #logging.info("-----------------------------------------------------")
                #logging.info(f"{file_counter}: {message.file.name}")
                if mode == 'download':
                    file_path = os.path.join(download_folder, message.file.name)
                    download_file(client, message, file_path)
    if mode == 'count':
        logging.info(f"Total files with allowed extensions in the group: {file_counter}")
    else:
        logging.info(f"Total files processed: {file_counter}")
