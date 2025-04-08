from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterDocument
from telethon.sessions import StringSession
from datetime import datetime, timedelta
import dateutil.relativedelta
import configparser
import sqlite3
import time
import os

# Determine if running in GitHub Actions
IS_GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS', 'false').lower() == 'true'

if IS_GITHUB_ACTIONS:
    # Fetch configuration from environment variables
    API_ID = int(os.getenv('API_ID'))
    API_HASH = os.getenv('API_HASH')
    PHONE = os.getenv('PHONE')
    SESSION_STRING = os.getenv('SESSION_STRING', '')
    MY_CHAT_ID = int(os.getenv('MY_CHAT_ID'))
    
    # Split the string by comma and strip whitespace
    items = [item.strip() for item in os.getenv('GROUP_IDS', '').split(',')]

    # Convert items to their respective types
    GROUP_IDS = []
    for item in items:
        # Remove any quotes from the string
        clean_item = item.strip("'").strip('"')
        try:
            # Try converting to integer first
            GROUP_IDS.append(int(clean_item))
        except ValueError:
            # If it fails, keep it as a string
            GROUP_IDS.append(clean_item)

else:
    # Fetch configuration from config.ini
    config = configparser.ConfigParser()
    config.read('config.ini')

    API_ID = int(config['Telegram']['api_id'])
    API_HASH = config['Telegram']['api_hash']
    PHONE = config['Telegram']['phone']
    SESSION_STRING = config['Telegram'].get('session_string', '')
    MY_CHAT_ID = int(config['Telegram']['my_chat_id'])
    
    # Split the string by comma and strip whitespace
    items = [item.strip() for item in config['Telegram']['group_ids'].split(',')]

    # Convert items to their respective types
    GROUP_IDS = []
    for item in items:
        # Remove any quotes from the string
        clean_item = item.strip("'").strip('"')
        try:
            # Try converting to integer first
            GROUP_IDS.append(int(clean_item))
        except ValueError:
            # If it fails, keep it as a string
            GROUP_IDS.append(clean_item)

# Retry logic for database lock (only used if SESSION_STRING is empty)
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds

async def safe_start(client, phone):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            await client.start(phone=phone)
            # Save the new session string to config.ini
            session_string = client.session.save()
            config['Telegram']['session_string'] = session_string
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            print("New session string saved to config.ini:", session_string)
            return
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                retries += 1
                print(f"Database is locked. Retrying {retries}/{MAX_RETRIES}...")
                time.sleep(RETRY_DELAY)
            else:
                raise
    raise sqlite3.OperationalError("Failed to start client after multiple retries due to database lock.")

async def main():
    # Initialize client with StringSession
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    try:
        # If no session string, start with phone and generate one
        if not SESSION_STRING:
            await safe_start(client, PHONE)
        else:
            # Connect with existing session
            await client.connect()
            if not await client.is_user_authorized():
                print("Session invalid. Generating a new one...")
                await safe_start(client, PHONE)
        
        # Update datetime calculations to use yesterday
        yesterday = datetime.now() - timedelta(days=1)
        START_OF_DAY = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        END_OF_DAY = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Check if any files were processed
        files_processed = False

        for group in GROUP_IDS:
            async for message in client.iter_messages(
                group,
                filter=InputMessagesFilterDocument  # Only PDFs/documents
            ):
                # Manually filter messages from yesterday
                message_date = message.date.replace(tzinfo=None)  # Remove timezone
                if START_OF_DAY <= message_date <= END_OF_DAY:
                    try:
                        # Forward only the attachment to your private chat
                        if message.media:
                            # Log the group name and file name
                            group_entity = await client.get_entity(group)
                            print(f"{group_entity.title}:: {message.file.name}")
                            
                            await client.send_file(MY_CHAT_ID, message.media, caption=message.message or "")
                            print(f"Forwarded attachment: {message.file.name}")
                            files_processed = True
                    except Exception as e:
                        print(f"Failed to forward attachment from message {message.id}: {e}")

        # If no files were processed, send a message with the date range checked
        start_date = START_OF_DAY.strftime('%Y-%m-%d %H:%M:%S')
        end_date = END_OF_DAY.strftime('%Y-%m-%d %H:%M:%S')
        if not files_processed:
            await client.send_message(MY_CHAT_ID, f"No files were found for the time period: {start_date} to {end_date}.")
    
    finally:
        await client.disconnect()

# Run the script
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())