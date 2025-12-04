import os
import datetime
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from src.utils import setup_logger

logger = setup_logger(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarManager:
    def __init__(self, credentials_path="credentials.json"):
        self.creds = None
        self.service = None
        self.credentials_path = credentials_path
        self.token_path = "token.pickle"

    def authenticate(self):
        """
        Authenticates the user using OAuth 2.0.
        """
        try:
            if os.path.exists(self.token_path):
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)
            
            # If there are no (valid) credentials available, let the user log in.
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        logger.error(f"Credentials file not found at {self.credentials_path}")
                        return False
                        
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.creds, token)

            self.service = build('calendar', 'v3', credentials=self.creds)
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False

    def create_event(self, summary, start_time_iso, duration_minutes=30, description=""):
        """
        Creates an event in the user's calendar.
        """
        if not self.service:
            if not self.authenticate():
                return None

        try:
            start_dt = datetime.datetime.fromisoformat(start_time_iso)
            end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'UTC', # Adjust as needed or use user's local timezone
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'UTC',
                },
            }

            event = self.service.events().insert(calendarId='primary', body=event).execute()
            logger.info(f"Event created: {event.get('htmlLink')}")
            return event.get('htmlLink')
        except Exception as e:
            logger.error(f"Failed to create event: {str(e)}")
            return None
