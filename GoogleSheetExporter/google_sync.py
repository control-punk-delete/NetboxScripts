from extras.scripts import Script
from utilities.exceptions import AbortScript
from ipam.models import IPAddress



class GoogleSyncronization(Script):
    class Meta(Script.Meta):
        name = "GoogleSheetSynch"
        description = "Google Sheet synchronizations"
        scheduling_enabled = False

    def run(self, data, commit):
        

        TOKEN = data.get("google_sheet_id", None)

        if not TOKEN:
            self.log_debug("google_sheet_id is not definded. Aborted!")
            raise AbortScript("Missing Google Sheet ID.")
            

        self.log_debug(f"google_sheet_id defined {TOKEN}")
        

        CUSTOM_FIELDS = data.get("custom_fields", None)
        IP_ADDRESSES = CUSTOM_FIELDS.get("service_ndns_ips", [])

        # Якщо немає ІР адрес - нічого не робимо
        if not IP_ADDRESSES:
            self.log_debug("Missing IP Addresses that should report")
            raise AbortScript("Missing custom field 'service_ndns_ips' that represent public IP Addresses that connected to ndns.")

        rows = []

        for IP in IP_ADDRESSES:

            ip_address = IPAddress.objects.get(pk=IP.get("id"))

            if ip_address.tags.filter(name="reported").exists():
                self.log_info(f"IP address {IP.get("display", None)} marked as reported. That means its already exist in table.")
                continue
            
            row = [data.get("name", "undefined"), CUSTOM_FIELDS.get("edrpou", "undefined"), IP.get("display", None), IP.get("device", "unknown"), list(ip_address.tags.values_list('name', flat=True))]
            self.log_debug(f"New row is created: {row}")

            # Помічаємо що в ми опрацювали ці ІР адреси
            ip_address.tags.add("reported")
            self.log_info(f"Tag reported added to ip address: {IP.get("display", None)}")
            if commit:
                self.log_debug("Save ip object")
                ip_address.save()

            rows.append(row)
             
        
        

        self.log_debug(f"Appended {len(rows)} rows: {rows}")
        


        
        
        




        


              
        

