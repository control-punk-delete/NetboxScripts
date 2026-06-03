from extras.scripts import Script
from utilities.exceptions import AbortScript



class GoogleSyncronization(Script):
    class Meta(Script.Meta):
        name = "GoogleSheetSynch"
        description = "Google Sheet synchronizations"
        scheduling_enabled = False

    def run(self, data, commit):
        

        TOKEN = data.get("google_sheet_id", None)

        if not TOKEN:
            self.log_debug("google_sheet_id is not definded. Aborted!")
            

        self.log_debug(f"google_sheet_id defined {TOKEN}")
        
        # Для легшого використання отримуємо customs_fields
        CUSTOM_FIELDS = data.get("custom_fields", None)

        

        IP_ADDRESSES = CUSTOM_FIELDS.get("service_ndns_ips", [])

        # Якщо немає ІР адрес - нічого не робимо
        IF not IP_ADDRESSES:
            self.log_debug("Missing IP Addresses that should report - ABORT")


        rows = []

        GS_DATA = 
        for IP in IP_ADDRESSES:
            
            row = [data.get("name", "undefined"), CUSTOM_FIELDS.get("edrpou", "undefined"), "moniker", IP]
            self.log_debug(f"New row is created: {row}")
            rows.append(row)
             
        
        

        self.log_debug(f"Appended {len(rows)} rows: {rows}")

        
        
        




        


              
        

