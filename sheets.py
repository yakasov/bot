"""
Google Sheets API, 'quickstart' file
"""

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SPREADSHEET_ID = '1HKzyvfyAsrDkGRQx3_2lSsvWjPP89eLG9vSGtAz4deM'
RANGE_NAME = 'A4:E23'


async def get_excel(message):
    """Sends values from Overwatch spreadsheet to Discord."""
    creds = None
    if os.path.exists('resources/token.pickle'):
        with open('resources/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'resources/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('resources/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    final_print = ''
    for row in values:
        row_string = '{:>19}'.format(row[0])
        for data in row[1:-1]:
            row_string += ' | {:<19}'.format(data)

        try:
            if message.author.id == int(row[4]):
                row_string += '<-----'
        except ValueError:
            pass

        if any(char.isdigit() for char in row_string[13:]) or 'Tank' in row_string:
            # Include the header row, and do not include rows with no SRs in.
            final_print += f'\n{row_string}'
    await message.channel.send(f'```{final_print}```')
