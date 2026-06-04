from extras.scripts import Script
from utilities.exceptions import AbortScript
from ipam.models import IPAddress

# Google Libs
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

class GoogleExporter(Script):
    class Meta(Script.Meta):
        name = "GoogleExporter"
        description = "Google Sheet Exporter"
        scheduling_enabled = False


    def append_rows(self, spreadsheet_id, token, rows):

        token_info = json.loads(token)

        creds = Credentials.from_authorized_user_info(
            token_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )

        service = build("sheets", "v4", credentials=creds)

        body = { "values": rows }


        try:
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range="Sheet1!A1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()

            print(f"{result.get('updates').get('updatedRows')} rows added")
        except HttpError as error:
            print(f"An error occurred: {error}")


    def run(self, data, commit):
        

        TOKEN = json.dumps(data.get("google_api_token", None))
        if not TOKEN:
            raise AbortScript("Missing Google API Token.")

        SPREADSHEET_ID = data.get("spreadsheet_id", None)
        if not SPREADSHEET_ID:
            raise AbortScript("Missing Google Sheet ID.")

        EXPORT_FIELDS = data.get("export_fields", None)
        if not EXPORT_FIELDS:
            raise AbortScript("No fields that should be exported")

        self.log_debug(f"Fields to export: {EXPORT_FIELDS}")

        CUSTOM_FIELDS = data.get("custom_fields", None)

        ROWS = [[]]

        for field_name in EXPORT_FIELDS:

            if "." in field_name:
                row[0].append(data.get(field_name.split(".")[0], None).get(field_name.split(".")[1], None))

            else:
                row[0].append(data.get(field_name, None))

        ip_address = IPAddress.objects.get(pk=data.get("id"))

        self.log_debug(row)

        self.log_debug("Start writing to Google Sheet")
        self.append_rows(spreadsheet_id=SPREADSHEET_ID, token=TOKEN, rows=ROWS)

        ip_address.tags.add("reported")
        if commit:
            self.log_debug("IP address marked as reported")
            ip_address.save()

        




        


              
        

