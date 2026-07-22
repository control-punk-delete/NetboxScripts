import requests

from bs4 import BeautifulSoup

from extras.scripts import Script
from utilities.exceptions import AbortScript
from tenancy.models import Tenant
from dcim.models import Region
from extras.models import Tag  

class YouControlEnrichment(Script):
    class Meta(Script.Meta):
        name = "YouControlEnrichment"
        description = "Збагачення інформації про організацію, шляхом запиту до YouControl"
        scheduling_enabled = False

    def youcontrol_search_by_edrpou(self, edrpou: str = None):
        """
        edrpou - uniq organization identifier
        return - html page from youcontrol
        """
        if not edrpou:
            raise AbortScript("Missing edrpou argument")

        URL = "https://youcontrol.com.ua/catalog/company_details/"
        FULL_URL = URL + edrpou + "/"

        headers = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"}
        data = requests.get(FULL_URL, headers=headers)

        if data.status_code != 200:
            raise AbortScript(f"YouControl return status code: {data.status_code}, with {data.text} error")
    
        return data.text


    def youcontrol_result_parser(self, data):
        you_control_data = {}

        soup = BeautifulSoup(data, "html.parser")
        containers = soup.find_all("div", {"class": "seo-table-contain"})

        for container in containers:

            seo_table = container.find("div", {"class": "seo-table"})
            seo_table_rows = seo_table.find_all("div", {"class": "seo-table-row"})

            for row in seo_table_rows:
                key = row.find("div", {"class": "seo-table-col-1"})
                if key:
                    key = key.get_text().strip().split('\n')[0].strip()

                values = row.find(["span", "p", "div"], {"class": "seo-table-col-2"})
                if values:
                    values = values.get_text().strip().split('\n')

                    if key == "Повне найменування юридичної особи":    
                        you_control_data["tenant_name_full"] = values[0].strip()

                    if key == "Скорочена назва":    
                        you_control_data["tenant_name"] = values[0].strip()

                    if key == "Назва англійською":
                        you_control_data["tenant_name_en"] = values[0].strip()

                    if key == "Статус юридичної особи":
                        you_control_data["tenant_status"] = values[0].strip()

                    if key == "Статус з ЄДР":
                        you_control_data["tenant_edr_status"] = values[0].strip()

                    if key == "Код ЄДРПОУ":
                        you_control_data["tenant_edrpou"] = values[0].strip()

                    if key == "Дата реєстрації":
                        you_control_data["tenant_registration_date"] = values[0][0:10]

                    if key == "Організаційно-правова форма":
                        you_control_data["tenant_loyal_form"] = values[0].strip()

                    if key == "Види діяльності":
                        you_control_data["tenant_kved_primary"] = values[2].strip()
                        you_control_data["tenant_kved_secondary"] = list( i for i in values[30:-3] if i!='')

                    if key == "Контактна інформація":
                        you_control_data["tenant_address"] = values[3].strip()
                        you_control_data["tenant_city"] = you_control_data["tenant_address"].split(",")[-3].strip()
                        you_control_data["tenant_region"] = you_control_data["tenant_address"].split(",")[2].strip()

                    if key == "Перелік засновників/учасників юридичної особи":
                        you_control_data["parent_tenant_name"] = values[0].strip()
                        you_control_data["parent_tenant_edrpou"] = values[2].strip()
                        you_control_data["parent_tenant_address"] = values[5].strip()

        return you_control_data


    def run(self, data, commit):

        self.log_debug(data)
        tenant_id = data.get('id')
        self.log_debug(f"Tenant id: {tenant_id}")

        tenant = Tenant.objects.get(pk = tenant_id)
        self.log_debug(f"Tenant object: {tenant}")

        tenant_edrpou = data.get('custom_fields', {}).get("edrpou")
        self.log_debug(f"Tenant edrpou: {tenant_edrpou}")

        youcontrol_data = self.youcontrol_search_by_edrpou(edrpou = tenant_edrpou)

        if not youcontrol_data:
            raise AbortScript("YouControl data is missing")

        youcontrol_parsed_data = self.youcontrol_result_parser(data = youcontrol_data)

        if not youcontrol_parsed_data:
            raise AbortScript("Parser does not extract any data from YouControl data")
            
        
        self.log_info(f"YouControl Data: {youcontrol_parsed_data}")


        region = Region.objects.filter(name__icontains=youcontrol_parsed_data.get("tenant_region").split(" ")[0]).first()
        region_id = region.id
        self.log_debug(f"Extract Region: {region}")
        tenant.custom_field_data["region"] = region_id

        if youcontrol_parsed_data.get("parent_tenant_edrpou"):
            self.log_debug(f"Find Parent Tenant {youcontrol_parsed_data.get("parent_tenant_name")} with edrpou {youcontrol_parsed_data.get("parent_tenant_edrpou")} in YouControl")

        
            try:  
                parent_tenant = Tenant.objects.get(  
                custom_field_data__edrpou=youcontrol_parsed_data.get("parent_tenant_edrpou")  
            )  
                self.log_debug(f"Parent Tenant exist in NetBox - {parent_tenant}")  
                tenant.custom_field_data["parent_tenant"] = parent_tenant.id

            except Tenant.DoesNotExist:  
                self.log_debug(  
                    f"Parent Tenant {youcontrol_parsed_data.get('parent_tenant_name')} "  
                    f"with edrpou {youcontrol_parsed_data.get('parent_tenant_edrpou')} not in NetBox" )

        tenant.description = youcontrol_parsed_data.get("tenant_name_full")
        tag, created = Tag.objects.get_or_create( name="youcontrol", defaults={'slug': 'youcontrol'})
        tenant.tags.add(tag)

        if commit:
            tenant.save()

        