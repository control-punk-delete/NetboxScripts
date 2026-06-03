from extras.scripts import Script
from utilities.exceptions import AbortScript



class GoogleSyncronization(Script):
    class Meta(Script.Meta):
        name = "GoogleSheetSynch"
        description = "Google Sheet synchronizations"
        scheduling_enabled = False

    def run(self, event, commit):
        

        TOKEN = data.get("google_sheet_id", None)

        if not TOKEN:
            self.log_debug("google_sheet_id is not definded. Aborted!")
            

        self.log_debug(f"google_sheet_id defined {TOKEN}")
        
        self.log_debug(data.keys())

        
        
        




        


              
        

