import ipinfo
import ipaddress

from extras.scripts import Script
from utilities.exceptions import AbortScript
from ipam.models import IPAddress, IPRange, Prefix
from extras.models import Tag 
from network_classifier import NetworkClassifier

class IPInfoEnrichment(Script):
    class Meta(Script.Meta):
        name = "IP Info"
        description = "Enrich IP Address objects via IPInfo"
        scheduling_enabled = False

    def run(self, data, commit):
        classifier = NetworkClassifier(auto_update=True)

        TOKEN = data.get("api_key", None)

        if not TOKEN:
            self.log_debug("API Key is not definded.")

        if data.get("url", "").startswith("/api/ipam/ip-addresses/"):
            ip_str = data.get("address", "").split("/")[0]
            ip_obj= IPAddress.objects.get(pk=data.get("id"))
            
        elif data.get("url", "").startswith("/api/ipam/prefixes/"):
            ip_str = data.get("prefix", "").split("/")[0]
            ip_obj = Prefix.objects.get(pk=data.get("id"))
            
        elif data.get("url", "").startswith("/api/ipam/ip-ranges/"):
            ip_str = data["start_address"].split("/")[0]
            ip_obj = IPRange.objects.get(pk=data.get("id"))
            
        else:
            raise AbortScript("Unexpected input data")
# Перевірка ІР чи публічна
        ip_obj_lib = ipaddress.ip_address(ip_str)

        ip_tags = []
        self.log_debug(f"Start validate {ip_obj_lib}")
                
        if ip_obj_lib.is_loopback:
            ip_tags.append("loopback-ip")
            self.log_debug("IP Address is Loopback")
                    
        elif ip_obj_lib.is_private:
            ip_tags.append("private-ip")
            self.log_debug("IP Address is Private")
                    
        elif ip_obj_lib.is_multicast:
            ip_tags.append("multicast-ip")
            self.log_debug("IP Address is multicast")
                    
        elif ip_obj_lib.is_link_local:
            ip_tags.append("link-local-ip")
            self.log_debug("IP Address is Link Local")
                        
        elif ip_obj_lib.is_reserved:
            ip_tags.append("reserved-ip")
            self.log_debug("IP Address is reserved")
                    

        self.log_debug("Create handler")
        handler = ipinfo.getHandler(TOKEN)
        self.log_debug(f"Request details for {ip_str}")
        details = handler.getDetails(ip_str)


        self.log_debug(f"Clusifier {ip_str} - class check")
        clusifier_result = classifier.lookup(ip_str)

        self.log_debug(clusifier_result)
        cf_class = [*clusifier_result.categories]
        cf_providers = [*clusifier_result.providers]

        try:
        
            if details.org:
                self.log_debug("Start object change")
                asn = details.org.split(" ")[0]
                self.log_debug(f"Edit asn: {asn}")
                ip_obj.custom_field_data['asn'] = asn

                isp = details.org.split(" ", 1)[1]
                AttributeError
                ip_obj.custom_field_data['isp'] = isp
        except AttributeError:
            self.log_debug(f"Missing org in ipinfo results")
                    
        try:
            city = details.city
            self.log_debug(f"Edit city: {city}")
            ip_obj.custom_field_data['city'] = city
        except AttributeError:
            self.log_debug(f"Missing city in ipinfo results")

        try:
            country = details.country
            self.log_debug(f"Edit country: {country}")
            ip_obj.custom_field_data['country'] = country
        except AttributeError:
            self.log_debug(f"Missing country in ipinfo results")

        if commit:
            self.log_debug("Save object")
            ip_obj.save()

            if cf_class:
                self.log_debug(f"Add a categories tags: {cf_class}")
                for t in cf_class:
                    tag, created = Tag.objects.get_or_create( name=t.lower(), defaults={'slug': t.lower()})
                    ip_obj.tags.add(tag)

                self.log_debug(f"Add a categories provides tags: {cf_providers}")
                for p in cf_providers:
                    tag, created = Tag.objects.get_or_create( name=p.lower(), defaults={'slug': p.lower()})
                    ip_obj.tags.add(tag )

            self.log_debug(f"Add verification tags: {ip_tags} ")
            for t in ip_tags:
                tag, created = Tag.objects.get_or_create( name=t.lower(), defaults={'slug': t.lower()})
                ip_obj.tags.add(tag )
        
