from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument
from tqdm.asyncio import tqdm
import os
import logging
import asyncio
import time

# Setup
api_id = 0
api_hash = ''
#group_username = ''
group_id = 
topic_id = 1

# Google Drive path
drive_folder = '/content/drive/MyDrive/PoompattaPDFs'
os.makedirs(drive_folder, exist_ok=True)

# Download log file
log_file_path = os.path.join(drive_folder, 'downloaded.txt')
if not os.path.exists(log_file_path):
    open(log_file_path, 'w').close()


# Load downloaded files
with open(log_file_path, 'r') as f:
    downloaded_files = set(line.strip() for line in f.read().splitlines() if line.strip())
print(f"Loaded {len(downloaded_files)} previously downloaded files")

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def download_file(client, message):
    base, ext = os.path.splitext(message.file.name)
    timestamp = message.date.strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{base}_{timestamp}{ext}"
    file_path = os.path.join(drive_folder, unique_filename)

    print(unique_filename)

    if unique_filename in downloaded_files:
        print(f"✅ Skipping already downloaded: {unique_filename}")
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

            #logging.info(f"✅ Downloaded: {unique_filename}")
            return
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed for {unique_filename}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                print(f"🚫 Failed to download after {max_retries} attempts: {unique_filename}")

async def main():
    client = TelegramClient('anon', api_id, api_hash)
    await client.start()

    group = await client.get_entity(group_id)
    print(f"Fetching files from group: {group.title}, topic ID: {topic_id}")

    messages = client.iter_messages(group)


    file_counter = 0
    async for message in messages:
        if message.media and isinstance(message.media, MessageMediaDocument):


            if message.file and message.file.name and message.file.name.lower().endswith('.pdf'):
                #print(file_counter, message.file.name)
                file_counter += 1
                print(f"\n🔍 Found PDF #{file_counter}: {message.file.name}")
                await download_file(client, message)

    print(f"\n🎉 Finished! Total new PDFs downloaded: {file_counter}")
    await client.disconnect()

await main()