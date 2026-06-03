import ipinfo
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
            self.log_debug("google_sheet_id is not definded.")
        
        self.log_debug(data)

        
        
        




        


              
        

