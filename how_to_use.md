# How to use tg_json_parser

- [How to use tg\_json\_parser](#how-to-use-tg_json_parser)
  - [Overview](#overview)
  - [Getting telegram chat data](#getting-telegram-chat-data)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Python Library](#python-library)
      - [1. Loading JSON Data](#1-loading-json-data)
      - [2. Parsing Messages](#2-parsing-messages)
      - [3. Saving to CSV](#3-saving-to-csv)
      - [Complete Example](#complete-example)
    - [Command Line Interface](#command-line-interface)
  - [Output Structure](#output-structure)

## Overview

This module parses JSON files exported from Telegram Desktop and converts chat messages into a structured format for analysis. **Zero external dependencies** - uses only Python standard library.

## Getting telegram chat data

1. Open the channel you want to download, clock on three dots in right top korner of the chat
2. Choose export chat history
3. Change the format from HTML to machine-readable JSON

## Installation

**Prerequisites**
- Python 3.8 or higher
- Git (for cloning the repository)

**Cloning the repository**

```bash
git clone https://github.com/our_new_public_git/tg_json_parser.git #TODO change it to the real git 
cd tg_api_parser
```

**No dependencies needed**

## Usage

### Python Library

The `TgJsonParser` class processes Telegram JSON exports and converts them into structured CSV files suitable for analysis.

#### 1. Loading JSON Data

```python
from tg_json_parser import TgJsonParser

# Initialize the parser
parser = TgJsonParser()

# Load JSON export file (replace with your file path)
chat_path = 'data/raw/Sample_ChatExport/result.json'
parser.load_json(chat_path)
```

The `load_json()` method reads and validates the Telegram export file. The file must have a `.json` extension and contain valid JSON data.

#### 2. Parsing Messages

```python
# Extract only content messages
parser.extract_messages()

# Access the structured data
print(f"Chat name: {parser.name}")
```
The method `.extract_messages()` stores and processes the raw JSON data, extracts chat name and converts all messages to structured dictionaries.

- **`parser.messages`** - raw data as a list of dictionaries;
- **`parser.content_messages`**: Regular user messages converted to dictionaries with standardized keys like `msg_id`, `posting_time`, `sender`, `media_type`, `content`, etc;
- **`parser.member_actions`**: Service messages (member joins, leaves, and other chat events) organized as structured data


```python
print(f"Raw message: {parser.messages[0]}")
print(f"Content message: {parser.content_messages[0]}")
if hasattr(parser, 'member_actions'):
   print(f"Service message: {len(parser.member_actions)}")
```

For more convenient analysis, the data can be converted to DataFrame format. In that case, pandas should be installed and imported.

```python
import pandas as pd 

df_messages = pd.DataFrame(tg_parcer.content_messages)
df_messages
```

#### 3. Saving to CSV

```python
# Save to CSV files in specified directory
parcer.save_chat(output_path='data/processed/Sample_Chat', save_actions=True)
```

This creates CSV files in the output directory:
- `content_messages.csv` - All regular messages
- `member_actions.csv` - Service messages (if `save_actions=True` was used)

#### Complete Example

```python
from tg_json_parser import TgJsonParser

# Initialize and process
parser = TgJsonParser()
parser.load_json('path/to/result.json')
parser.extract_messages(save_actions=True)
parser.save_chat('./exported_data')

print(f"Exported {len(parser.content_messages)} messages from {parser.name}")
```

### Command Line Interface

For quick processing without writing Python code:

```bash
python tg_json_parser.py input.json output_directory [--save_actions]
```

**Arguments:**
- `input.json` - Path to Telegram JSON export file
- `output_directory` - Directory where CSV files will be saved
- `--save_actions` - Optional flag to include service messages

**Examples:**

```bash
# Basic export
python tg_json_parser.py data/raw/Sample_ChatExport/result.json data/processed/Sample_Chat

# Include service messages
python tg_json_parser.py data/raw/Sample_ChatExport/result.json data/processed/Sample_Chat --save_actions
```

## Output Structure

The parser creates CSV files with the following structure:

**content_messages.csv:**
- `msg_id` - Unique message identifier
- `sender` - Message sender name
- `sender_id` - Sender's unique ID
- `posting_time` - When message was sent
- `edited` - When message was last edited
- `media_type` - Type of content (text, photo, video_file, etc.)
- `content` - Message text or media caption
- `file` - Path to media file (if any)
- `reply_to_msg_id` - ID of replied message
- `forwarded_from` - Original sender for forwarded messages
- `reactions` - Message reactions data
- `chat_name` - Name of the chat/channel

**member_actions.csv** (when `save_actions=True`):
- Service messages like member joins, leaves, and other chat events




