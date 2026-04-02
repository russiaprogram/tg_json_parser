import datetime
import json
import csv
import argparse


class TgJsonParser():
    """
    Parser for Telegram JSON export files.
   
    Processes Telegram chat exports to extract and structure message data
    for analysis and export. Handles text messages, media, polls, forwards,
    and service messages.
   
    Attributes
    ----------
    data : dict or None
        Raw JSON data from Telegram export
    name : str or None
        Chat/channel name
    messages : list
        All messages from export
    member_actions : list of dict
        Service messages (joins, leaves, etc.)
    content_messages : list of dict
        Parsed content messages
   
    Examples
    --------
    >>> parser = TgJsonParser()
    >>> parser.load_json('/path/to/export')
    >>> parser.parse_chat()
    >>> parser.save_to_csv('output.csv')
    """

    
    def __init__(self):
        """
        Initialize the TgJsonParser instance.
    
        Sets up the initial state of the parser with empty containers for:
        - data: Raw JSON data loaded from the Telegram export file
        - name: Chat/channel name extracted from the JSON
        - messages: List of all messages (both content and service messages)
        - member_actions: List of service messages only
        - content_messages: List of parsed content messages
        
        This constructor prepares the parser for loading and processing 
        Telegram chat export data in JSON format.
        """

        self.data = None
        self.name = None
        self.messages = []
        self.member_actions = []
        self.content_messages = []
    
    def load_json(self, json_path, encoding='utf-8'):
        """
        Load Telegram JSON export file into memory.

        Validates file extension and loads JSON data for processing.

        Parameters
        ----------
        json_path : str
        Path to the JSON export file
        encoding : str, optional
        File encoding, by default 'utf-8'

        Raises
        ------
        ValueError
            If file doesn't have '.json' extension
        FileNotFoundError
            If file doesn't exist
        json.JSONDecodeError
            If file contains invalid JSON
        """
        if not json_path.endswith('.json'):
            raise ValueError("File must be a JSON file with '.json' extension.")
        else:
            self.file_dir = json_path
            with open(json_path, 'r', encoding=encoding) as file:
                self.data = json.load(file)
        
    def extract_messages(self):
        """
        Extract and categorize messages from loaded JSON data.

        Extracts chat name and converts all messages to structured dictionaries.
        Optionally extracts service messages (member join/leave events) when 
        save_actions is enabled.

        Raises
        ------
        AttributeError
            If load_json() hasn't been called (self.data is None)

        Notes
        -----
        Always populates self.name and self.content_messages.
        If save_actions=True, also populates self.member_actions with service messages.
        Must be called after load_json().
        """
        self.name = self.data.get('name')
        self.messages = self.data.get("messages", [])
        self.content_messages = [
            {**self._parse_content_message(msg), 'chat_name': self.name}  
            for msg in self.messages if msg.get('type') == 'message'
            ]
        
        self.member_actions = [
            {**msg, 'chat_name': self.name} 
            for msg in self.messages if msg.get('type') == 'service'
            ]

    def _parse_content_message(self, message):
        """
        Extracts and standardizes key information from a Telegram message,
        including metadata, sender information, timestamps, and content.
        Only processes messages of type 'message', ignoring service messages.

        Parameters
        ----------
        message : dict
        Raw message object from Telegram JSON export

        Returns
        -------
        dict or None
        Structured message dictionary with standardized fields:
        - msg_id: Message unique identifier
        - sender: Sender's display name  
        - sender_id: Sender's unique ID
        - reply_to_msg_id: ID of replied message (if any)
        - forwarded_from: Original sender for forwarded messages
        - reactions: Message reactions data
        - reactions_count: Counting reactions to the message
        - posting_time: When message was sent (datetime object)
        - edited: When message was last edited (datetime object)
        - Additional fields from _get_content() (media_type, content, etc.)
        
        Returns None if message type is not 'message'.

        Notes
        -----
        This method delegates content parsing to _get_content() for handling
        different media types and text formatting. Timestamps are converted
        to datetime objects using _get_datetime().
        """
        message_dict = {}
        
        if message['type'] == 'message':
            message_dict['msg_id'] = message.get('id')
            message_dict['sender'] = message.get('from')
            message_dict['sender_id'] = message.get('from_id')
            message_dict['reply_to_msg_id'] = message.get('reply_to_message_id')
            message_dict['forwarded_from'] = message.get('forwarded_from')
            message_dict['reactions'] = self._get_reactions(message.get('reactions'))[0]
            message_dict['reactions_count'] = self._get_reactions(message.get('reactions'))[1]
            
            message_dict['posting_time'] = self._get_datetime(message.get('date_unixtime'))
            message_dict['edited'] = self._get_datetime(message.get('edited_unixtime'))

            message_dict.update(self._get_content(message))
                        
            return message_dict
        
        else:
            return None
    
    def save_chat(self, output_path, save_actions=False):
        """       
        Exports content messages and optionally member actions to separate
        csv files in the specified directory. 
        
        Parameters
        ----------
        result_path : str
            Directory path where csv files will be saved

        save_actions : bool, optional
            If True, saves service messages in a separate file. By default False since
            for the most cases the service messages are removed from the chat by admins.
        
        Raises
        ------
        AttributeError
            If extract_messages() hasn't been called (missing content_messages)
        FileNotFoundError
            If the result_path directory doesn't exist
        PermissionError
            If unable to write to the specified directory
        
        Notes
        -----
        Always saves content_messages.csv.
        Saves member_actions.csv only if save_actions was True du.
        Requires _save_to_csv() helper method to be implemented.
        """
        
        if save_actions:
            self._save_to_csv(output_path + '/member_actions.csv', self.member_actions)
        self._save_to_csv(output_path + '/content_messages.csv', self.content_messages)

    def _save_to_csv(self, csv_path, messages, encoding='utf-8'):
        """        
        Saves all parsed content messages to a CSV file with headers.        

        Parameters
        ----------
        csv_path : str
            Full path for the output CSV file
        messages : list
            List of message dictionaries to save
        encoding : str, optional
            File encoding, by default 'utf-8'
        
        Raises
        ------
        IndexError
            If no content messages exist (empty messages list)
        PermissionError
            If unable to write to the specified location
        IOError
            If disk space insufficient or other I/O error occurs
        
        Notes
        -----
        Requires extract_messages() to be called first to populate messages.
        CSV columns include all unique keys found across all messages.
        """
        if not messages:
            raise IndexError("No messages to save.")
        
        # Collect all unique keys from all messages
        all_keys = set()
        for message in messages:
            all_keys.update(message.keys())
        
        fieldnames = sorted(all_keys)  # Sort for consistent column order

        with open(csv_path, 'w', newline='', encoding=encoding) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
            # Writing headers.
            writer.writeheader()
        
            # Writing rows.
            for row in messages:
                writer.writerow(row)

    def _get_content(self, message):
        """
        Extract content and media information from a message.

        Analyzes message structure to determine content type and extracts
        relevant data including text, media files, polls, and location info.
        Handles various Telegram message formats and media types.

        Parameters
        ----------
        message : dict
        Raw message object from Telegram JSON export

        Returns
        -------
        dict
        Content dictionary with standardized fields:
        - media_type : str
            Type of content ('text', 'photo', 'video_file', 'poll', etc.)
        - content : str, dict, or None
            Parsed content (text, poll data, location info, etc.)
        - file : str or None
            File path for media attachments
        - file_name : str or None
            Original filename for media files

        Notes
        -----
        Delegates text parsing to _parse_text() for handling formatting
        and links. Different media types are processed according to their
        specific structure in the Telegram export format.
        """

        media_type = 'text'
        content = None
        file = None
        file_name = None
        
        if 'media_type' in message: 
            media_type = message['media_type']
            file = message.get('file', None)
            file_name = message.get('file_name', None)

            #Parcing media types that can't go with text.    
            if media_type in ['sticker', 'voice_message']:
                content = message.get('sticker_emoji', None)

            #Parcing media types that can go with text.
            if media_type in ['video_file', 'animation', 'audio_file', ]:
                content = self._parse_text(message.get('text_entities', None))

        # Parcing polls.
        elif 'poll' in message:
            media_type = 'poll'
            content = message.get('poll', None)

        # Parcing messages with photos.
        elif 'photo' in message:
            media_type = 'photo'
            file = message.get('photo', None)
            content = self._parse_text(message.get('text_entities', None))
            
        # Parcing geolocation.
        elif 'location_information' in message:
            media_type = 'location_information'
            content  = {
                'place_name': message.get('place_name', None), 
                'address': message.get('address', None), 
                'location_information': message.get('location_information', None)}
                
        else:
            # Passing text content.
            media_type = 'text'
            content = self._parse_text(message.get('text_entities', None))
        
        return {
                'media_type': media_type, 
                'content': content, 
                'file': file,
                'file_name': file_name
                }

        
    def _parse_text(self, text_entities):
        """
        Combine text entities into a formatted string.

        Processes Telegram text entities and combines them into one string,
        appending URLs in parentheses for links.

        Parameters
        ----------
        text_entities : list or None
        List of text entity objects from Telegram export

        Returns
        -------
        str
        Combined text with links formatted as "text (url)".
        Empty string if input is None or empty.
        """
        if text_entities and len(text_entities) > 0:
            text_list = []
            for element in text_entities:
                if 'href' in element.keys():
                    text_list.append(f'{element['text']} ({element['href']} )')
                else:
                    text_list.append(element['text'] + ' ')
            return ''.join(text_list)
        
        else:
            return ''
        
    def _get_datetime(self, unixtime):
        """
        Convert Unix timestamp to datetime object.

        Parameters
        ----------
        unixtime : int, float, or None
        Unix timestamp (seconds since epoch)

        Returns
        -------
        datetime.datetime or None
        Datetime object or None if input is None
        """
        if unixtime is not None:
            timestamp = int(unixtime)
            dt = datetime.datetime.fromtimestamp(timestamp)
            return dt
        
    def _get_reactions(self, reactions):
        """
        Parses reaction information from a message.

        Parameters
        ----------
        reactions: string or None

        Returns
        -------
        tuple of (str or None, int)
            A tuple containing:
            - reactions_list : str or None
                Comma-separated string of reactions in format 'emoji: count', or None if no reactions.
            - reactions_count : int
                Total number of reactions across all emoji types, or 0 if no reactions.

        Notes
        -----
        - Aggregates all reaction types and their counts into a single string.
        - Returns (None, 0) if the message has no reactions.
        """

        
        if reactions:
            reactions_list = ', '.join([f'{reaction['emoji']}: {reaction['count']}' for reaction in reactions])
            reactions_count = sum([reaction['count'] for reaction in reactions])
            return (reactions_list, reactions_count)
        else:
            return (None, 0)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse Telegram JSON export and save to CSV.")
    parser.add_argument("json_path", help="Path to the Telegram JSON export file.")
    parser.add_argument("output_dir", help="Directory to save the output CSV files.")
    parser.add_argument("--save_actions", action="store_true", help="Save member actions to a separate file.")
    args = parser.parse_args()

    tg_parser = TgJsonParser()
    tg_parser.load_json(args.json_path)
    tg_parser.extract_messages()
    tg_parser.save_chat(args.output_dir, save_actions=args.save_actions)