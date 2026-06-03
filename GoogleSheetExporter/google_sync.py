from extras.scripts import Script
from utilities.exceptions import AbortScript
from ipam.models import IPAddress

# Google Libs
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

class GoogleSyncronization(Script):
    class Meta(Script.Meta):
        name = "GoogleSheetSynch"
        description = "Google Sheet synchronizations"
        scheduling_enabled = False


    def append_rows(spreadsheet_id, token, rows):

        token_info = json.loads(token)

        creds = Credentials.from_authorized_user_info(
            token_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )

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
        

        TOKEN = data.get("google_api_token", None)

        if not TOKEN:
            raise AbortScript("Missing Google API Token.")
        
        self.log_debug(TOKEN)

        SPREADSHEET_ID = data.get("spreadsheet_id", None)

        if not SPREADSHEET_ID:
            raise AbortScript("Missing Google Sheet ID.")
            
        self.log_debug(SPREADSHEET_ID)

        CUSTOM_FIELDS = data.get("custom_fields", None)
        IP_ADDRESSES = CUSTOM_FIELDS.get("service_ndns_ips", [])

        # Якщо немає ІР адрес - нічого не робимо
        if not IP_ADDRESSES:
            self.log_debug("Missing IP Addresses that should report")
            raise AbortScript("Missing custom field 'service_ndns_ips' that represent public IP Addresses that connected to ndns.")

        ROWS = []

        for IP in IP_ADDRESSES:

            ip_address = IPAddress.objects.get(pk=IP.get("id"))

            if ip_address.tags.filter(name="reported").exists():
                self.log_warning(f"IP address {IP.get("display", None)} marked as reported. That means its already exist in table.")
                continue
            
            row = [data.get("name", "undefined"), CUSTOM_FIELDS.get("edrpou", "undefined"), IP.get("display", None), IP.get("dscription", "unknown")]
            self.log_debug(f"New row is created: {row}")

            # Помічаємо що в ми опрацювали ці ІР адреси
            ip_address.tags.add("reported")
            self.log_info(f"Tag reported added to ip address: {IP.get("display", None)}")
            if commit:
                self.log_debug("Save ip object")
                ip_address.save()

            ROWS.append(row)
             
        
        

        self.log_debug(f"Appended {len(ROWS)} rows: {ROWS}")
        self.log_debug("Start writing to Google Sheet")


        self.append_rows(SPREADSHEET_ID, token=TOKEN, rows=ROWS)
        self.log_success("Done")


        
        
        




        


              
        

