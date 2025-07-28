import os
import base64
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILES = ['creds/credentials(trinidium.1).json', 'creds/credentials(trinidium01).json']

class EmailManager:
    def __init__(self):
        try:
            self.services = [self.authenticate_gmail(f, f"token{i+1}.json") for i, f in enumerate(CREDENTIALS_FILES)]
            self.profiles = [self.get_profile(s) for s in self.services]
            self.senders = [p['emailAddress'] for p in self.profiles]
            self.sent_cache = self.load_sent_emails()
        except Exception as e:
            raise Exception(f"Failed to initialize EmailManager: {str(e)}")

    def get_profile(self, service):
        try:
            return service.users().getProfile(userId='me').execute()
        except Exception as e:
            raise Exception(f"Failed to fetch profile: {str(e)}")

    def authenticate_gmail(self, creds_file, token_file):
        creds = None
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Token refresh failed: {str(e)}")
                    creds = None
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        return build('gmail', 'v1', credentials=creds)

    def already_sent(self, lead):
        # Only checks for main email, not follow-ups
        return lead['email'] in self.sent_cache

    def load_sent_emails(self):
        sent_emails = set()
        if os.path.exists('logs/sent_logs.txt'):
            try:
                with open('logs/sent_logs.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split('|')
                        if len(parts) >= 4 and "Main Email" in line:
                            sent_emails.add(parts[3].strip())
            except Exception as e:
                print(f"Warning: Failed to load sent emails cache: {str(e)}")
        return sent_emails

    def create_message(self, sender, to, subject, html):
        try:
            msg = MIMEMultipart('alternative')
            msg['To'] = to
            msg['From'] = sender
            msg['Subject'] = subject
            mime_html = MIMEText(html, 'html')
            msg.attach(mime_html)
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            return {'raw': raw}
        except Exception as e:
            raise Exception(f"Failed to create message: {str(e)}")

    def send_email(self, lead, subject, html):
        try:
            i = hash(lead['email']) % len(self.services)
            sender = self.senders[i]
            service = self.services[i]
            message = self.create_message(sender, lead['email'], subject, html)
            service.users().messages().send(userId='me', body=message).execute()
        except Exception as e:
            raise Exception(f"Failed to send email to {lead.get('email', 'unknown')}: {str(e)}")

    def has_replied(self, lead_email):
        for service in self.services:
            try:
                query = f"from:{lead_email} to:me"
                results = service.users().messages().list(
                    userId='me', 
                    q=query, 
                    maxResults=5
                ).execute()
                if results.get('messages', []):
                    return True
            except Exception:
                continue
        return False