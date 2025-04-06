from google.colab import drive
drive.mount('/content/drive')

!pip install telethon

from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument
from tqdm.asyncio import tqdm
import os
import logging
import asyncio
import time
import configparser

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

api_id = config.get('Telegram', 'api_id', fallback='0')
api_hash = config.get('Telegram', 'api_hash', fallback='0')
group_username = config.get('Telegram', 'group_username', fallback='')

drive_folder = config.get('Paths', 'drive_folder', fallback='/content/drive/MyDrive/PoompattaPDFs')
os.makedirs(drive_folder, exist_ok=True)

log_file_path = os.path.join(drive_folder, 'downloaded.txt')
if not os.path.exists(log_file_path):
    open(log_file_path, 'w').close()

with open(log_file_path, 'r') as f:
    downloaded_files = set(f.read().splitlines())

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def download_file(client, message):
    base, ext = os.path.splitext(message.file.name)
    timestamp = message.date.strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{base}_{timestamp}{ext}"
    file_path = os.path.join(drive_folder, unique_filename)

    if unique_filename in downloaded_files:
        logging.info(f"✅ Skipping already downloaded: {unique_filename}")
        return

    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            pbar = tqdm(total=message.file.size, unit='B', unit_scale=True, desc=unique_filename)

            async def progress_callback(current, total):
                pbar.update(current - pbar.n)

            await client.download_media(message, file=file_path, progress_callback=progress_callback)
            pbar.close()

            # Log the download
            with open(log_file_path, 'a') as f:
                f.write(unique_filename + '\n')
            downloaded_files.add(unique_filename)

            logging.info(f"✅ Downloaded: {unique_filename}")
            return
        except Exception as e:
            logging.error(f"❌ Attempt {attempt + 1} failed for {unique_filename}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logging.error(f"🚫 Failed to download after {max_retries} attempts: {unique_filename}")

async def main():
    client = TelegramClient('anon', api_id, api_hash)
    await client.start()

    file_counter = 0
    async for message in client.iter_messages(group_username):
        if message.media and isinstance(message.media, MessageMediaDocument):
            if message.file and message.file.name and message.file.name.lower().endswith('.pdf'):
                file_counter += 1
                logging.info(f"\n🔍 Found PDF #{file_counter}: {message.file.name}")
                await download_file(client, message)

    logging.info(f"\n🎉 Finished! Total new PDFs downloaded: {file_counter}")
    await client.disconnect()

await main()