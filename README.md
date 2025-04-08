# Telegram Download Channel

This project is designed to download media files (e.g., PDFs) from a specified Telegram group or channel using the Telethon library. It includes scripts for local execution (`app.py`) and Google Colab integration (`colab.py`).

## Features
- Download PDF files from a Telegram group or channel.
- Save downloaded files to a specified folder.
- Maintain a log of downloaded files to avoid duplicates.
- Configurable via `config.ini` for API credentials and paths.

## Prerequisites
- Python 3.7+
- Telethon library
- tqdm library

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd telegram-download-channel-main
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the application:
   - Copy `config.sample.ini` to `config.ini`.
   - Update `config.ini` with your Telegram API credentials and desired paths.

4. Run the script:
   - For local execution:
     ```bash
     python app.py
     ```
   - For Google Colab:
     - Open `colab.py` in Google Colab.
     - Mount your Google Drive.
     - Execute the script.

## Configuration
The `config.ini` file contains the following sections:

### Telegram
- `api_id`: Your Telegram API ID.
- `api_hash`: Your Telegram API hash.
- `group_username`: The username or link of the Telegram group/channel.

### Paths
- `download_folder`: The folder where downloaded files will be saved (for local execution).
- `drive_folder`: The folder in Google Drive where files will be saved (for Colab execution).

## File Extensions Configuration

The `config.ini` file now supports specifying allowed file extensions for downloads. This is configured under the `[General]` section with the `allowed_extensions` key. For example:

```ini
[General]
allowed_extensions = .pdf, .docx, .txt
```

This allows you to customize the types of files to download by listing their extensions as a comma-separated string.

## Logging
- Downloaded files are logged in `downloaded.txt` to prevent duplicate downloads.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
- [Telethon](https://github.com/LonamiWebs/Telethon) for the Telegram client library.
- [tqdm](https://github.com/tqdm/tqdm) for progress bars.
