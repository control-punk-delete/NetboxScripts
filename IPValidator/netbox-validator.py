import json
import ipaddress

from extras.scripts import Script, StringVar
from utilities.exceptions import AbortScript
from ipam.models import IPAddress, IPRange, Prefix

class IPAddressValidator(Script):  
  
    def run(self, data, commit):  
        self.log_debug(data)  
  
        if data.get("url", "").startswith("/api/ipam/ip-addresses/"):  
            ip_str = data.get("address", "").split("/")[0]  
            input_type = "IP Address"  
            ip_obj = IPAddress.objects.get(pk=data.get("id"))  
  
        elif data.get("url", "").startswith("/api/ipam/prefixes/"):  
            ip_str = data.get("prefix", "").split("/")[0]  
            input_type = "Prefix"  
            ip_obj = Prefix.objects.get(pk=data.get("id"))  
  
        elif data.get("url", "").startswith("/api/ipam/ip-ranges/"):  
            ip_str = data["start_address"].split("/")[0]  
            input_type = "IP Range"  
            ip_obj = IPRange.objects.get(pk=data.get("id"))  
  
        else:  
            raise AbortScript("Unexpected input data")  
  
        self.log_info(f"Deleting {input_type}: {ip_str}")  
        ip_obj.delete()  
        self.log_success(f"{input_type} {ip_str} deleted")