from telethon import TelegramClient, events
import os
from tqdm import tqdm
import configparser

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

group_id = int(config['Telegram']['group_id'])
topic_id = int(config['Telegram']['topic_id'])

# Load API credentials from config file
api_id = int(config['Telegram']['api_id'])
api_hash = config['Telegram']['api_hash']
phone = config['Telegram']['phone']

# Initialize the Telegram client
client = TelegramClient('session_name', api_id, api_hash)

# Directory to save downloaded files
download_dir = 'downloaded_files'
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

async def download_files_from_topic(group_id, topic_id):
    # Connect to Telegram
    await client.start(phone)

    # Resolve the group entity using the provided ID
    try:
        group = await client.get_entity(group_id)
        print(f"Resolved group: {group.title}, ID: {group.id}")
    except ValueError as e:
        print(f"Error resolving group with ID {group_id}: {e}")
        adjusted_id = int(f"-100{str(group_id)[1:]}") if group_id < 0 else group_id
        try:
            group = await client.get_entity(adjusted_id)
            print(f"Resolved group with adjusted ID: {group.title}, ID: {group.id}")
        except ValueError as e:
            print(f"Error with adjusted ID {adjusted_id}: {e}")
            return

    print(f"Fetching files from group: {group.title}, topic ID: {topic_id}")

    # Check if 'thread' parameter is supported (latest Telethon versions)
    try:
        # Attempt to use the 'thread' parameter
        messages = client.iter_messages(group, limit=1000)
    except TypeError:
        # Fallback for older versions: manually filter by topic ID
        print("Warning: 'thread' parameter not supported. Falling back to manual filtering.")
        messages = client.iter_messages(group, limit=1000)  # Adjust limit as needed

        # Filter messages manually by topic ID
        async def filtered_messages():
            async for msg in messages:
                # Check if message belongs to the topic (thread)
                if (msg.reply_to and msg.reply_to.reply_to_top_id == topic_id) or (msg.id == topic_id):
                    yield msg
        messages = filtered_messages()

    # Iterate through messages and download files
    async for message in messages:
        if message.media:
            # Define the file name
            file_name = message.file.name if message.file and message.file.name else f"file_{message.id}"

            # Check if the file is a PDF
            if file_name.lower().endswith('.pdf'):
                # Append message datetime as a timestamp to the file name
                timestamp = message.date.strftime('%Y%m%d_%H%M%S')
                file_name = f"{os.path.splitext(file_name)[0]}_{timestamp}{os.path.splitext(file_name)[1]}"

                file_path = os.path.join(download_dir, file_name)

                # Check if the file already exists and its size matches
                if os.path.exists(file_path):
                    existing_size = os.path.getsize(file_path)
                    if existing_size == message.file.size:
                        print(f"Skipping {file_name}, file already exists with matching size.")
                        continue

                # Download the file with tqdm progress bar
                print(f"Downloading {file_name}...")

                with tqdm(total=message.file.size, unit='B', unit_scale=True, desc=file_name) as pbar:
                    def progress_callback(current, total):
                        pbar.update(current - pbar.n)

                    await client.download_media(message, file_path, progress_callback=progress_callback)

                print(f"Saved to {file_path}")

    print("Download completed!")

# Run the script
with client:
    client.loop.run_until_complete(download_files_from_topic(group_id, topic_id))