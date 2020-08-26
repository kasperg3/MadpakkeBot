from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from apiclient import errors

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def listMessagesMatchingQuery(service, user_id, query=''):

  try:
    response = service.users().messages().list(userId=user_id,
                                               q=query).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except:
    print('An error occurred')


def getAttachments(service, user_id, msg_id, filename):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()

        for part in message['payload']['parts']:
            if part['filename']:
                if 'data' in part['body']:
                    data = part['body']['data']
                else:
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id,id=att_id).execute()
                    data = att['data']
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                path = filename

                with open(path, 'wb') as f:
                    f.write(file_data)
    except:
        print("An error occurred")

def save_menus():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    # Call the G
    # mail API to fetch INBOX
    messages = listMessagesMatchingQuery(service=service, user_id='me', query='from:(kag@a2isystems.com) Kokken & Co has:attachment')
    getAttachments(service=service, user_id='me', msg_id=messages[0]['id'], filename="next_menu.pdf")
    getAttachments(service=service, user_id='me', msg_id=messages[1]['id'], filename="current_menu.pdf")