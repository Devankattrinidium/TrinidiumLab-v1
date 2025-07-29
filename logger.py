import os
import datetime
from dotenv import load_dotenv
try:
    from notion_client import Client
except ImportError:
    Client = None

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

class Logger:
    def __init__(self):
        os.makedirs('logs', exist_ok=True)
        self.notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN and Client else None
        self.setup_file_logging()
        
    def setup_file_logging(self):
        self.sent_log = self._get_log_writer('logs/sent_logs.txt')
        self.error_log = self._get_log_writer('logs/error_logs.txt')
        
    def _get_log_writer(self, filename):
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                if 'sent' in filename:
                    f.write("timestamp | type | details | email\n")
                else:
                    f.write("timestamp | type | details | email\n")
        return open(filename, 'a', encoding='utf-8')
    
    def log_sent(self, email, msg_type):
        log_entry = f"{datetime.datetime.now()} | SENT | {msg_type} | {email}\n"
        self.sent_log.write(log_entry)
        self.sent_log.flush()
        
    def log_error(self, email, error_msg):
        log_entry = f"{datetime.datetime.now()} | ERROR | {error_msg} | {email}\n"
        self.error_log.write(log_entry)
        self.error_log.flush()

    def log_to_notion(self, subject, leads_sent, replies, errors, followups):
        if not self.notion:
            return
        try:
            self.notion.pages.create(
                parent={"database_id": NOTION_DATABASE_ID},
                properties={
                    "Subject": {"title": [{"text": {"content": subject}}]},
                    "Leads Sent": {"number": leads_sent},
                    "Replies": {"number": replies},
                    "Errors": {"number": errors},
                    "Followups": {"number": followups},
                }
            )
        except Exception as e:
            self.log_error("notion", f"Failed to log to Notion: {str(e)}")

    def __del__(self):
        if hasattr(self, 'sent_log'):
            self.sent_log.close()
        if hasattr(self, 'error_log'):
            self.error_log.close()