from extras.scripts import Script
from utilities.exceptions import AbortScript
from tenancy.models import Tenant, Contact
from ipam.models import IPAddress
from tenancy.choices import ContactPriorityChoices 

# Google Libs
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

class GoogleSyncronization(Script):
    class Meta(Script.Meta):
        name = "Google Sheet Integration"
        description = "Автоматичне відправлення інформації про НДНС в відповідні таблиці"
        scheduling_enabled = False

    # Функція запису в Google Sheet
    def append_rows(self, spreadsheet_id, rows, token, page_name):
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
                range=f"{page_name}!A1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()

            self.log_success(f"{result.get('updates').get('updatedRows')} rows added")
        except HttpError as error:
            raise AbortScript(f"An error occurred: {error}")


    def run(self, data, commit):
        
        # Отримання необхідних статичних даних про гугл таблицю.

        # Токен автентифікації
        TOKEN = data.get("google_api_token", None)
        if not TOKEN:
            raise AbortScript('Missing required attribute: {"google_api_token": "page_name"}')
        self.log_debug(TOKEN)
        TOKEN = json.dumps(TOKEN)

        # ID таблиці
        SPREADSHEET_ID = data.get("gs_table_id", None)
        if not SPREADSHEET_ID:
            raise AbortScript('Missing required attribute: {"gs_table_id": ""}')
        self.log_debug(SPREADSHEET_ID)

        # Назва сторінки (Page) на яку потрібно записати дані
        PAGE_NAME = data.get("gs_page_name", None)
        if not PAGE_NAME:
            raise AbortScript('Missing required attribute: {"gs_page_name": ""}')
        self.log_debug(PAGE_NAME)


        # Data - стрінга з ІР адресою, яка позначена tag=ndns, та про яку ще не повідомлено
        # Отримання даних обʼєкту IP Address

        ip_id = data.get('id')

        if data.get('tenant'):
            tenant_id = data.get('tenant').get('id')
        else:
            raise AbortScript(f"IP Address {data.get("display")} not assign to any Tenant.s")

        # Отримання даних про IP Address який необхідно передати
        IP_ADDRESS_OBJECT = IPAddress.objects.get(pk=ip_id)

        # Отримання даних про Tenant якому належить цей актив
        TENANT_OBJECT = Tenant.objects.get(pk=tenant_id)
        
        # Отримання даних про контактну особу даного тенанта
        CONTACT_ASSIGMENT_OBJECT = TENANT_OBJECT.contacts.filter(priority=ContactPriorityChoices.PRIORITY_PRIMARY).first()
        
        if not CONTACT_ASSIGMENT_OBJECT:
            contact_name = None
            contact_phone = None
            contact_email = None
            
        else:
            CONTACT_OBJECT = Contact.objects.get(pk=CONTACT_ASSIGMENT_OBJECT.contact_id)

            if not CONTACT_OBJECT:
                contact_name = None
                contact_phone = None
                contact_email = None
                
            else:
                contact_name = CONTACT_OBJECT.name
                contact_phone = CONTACT_OBJECT.phone
                contact_email = CONTACT_OBJECT.email
            

        # Формування рядку, який необхідно записати в таблицю
        ROWS = []
        if IP_ADDRESS_OBJECT.cf.get("ndns_configured", None):
            ndns_configured = "1"
        else:
            ndns_configured = "0"
        
        if IP_ADDRESS_OBJECT.cf.get("misp_configured", None): 
            misp_configured = "1"
        else:
            misp_configured = "0"
            
        if IP_ADDRESS_OBJECT.cf.get("syslog_configured", None):
            syslog_configured = "1"
        else: 
            syslog_configured = "0"

        tenant_name = TENANT_OBJECT.description
        if not tenant_name:
            tenant_name= TENANT_OBJECT.name

        # Mapping NetBox Data to  Google Table Columns
        row = [ 
                None, # n
                tenant_name, # org
                TENANT_OBJECT.cf.get("edrpou", None), # edrpou
                TENANT_OBJECT.cf.get("region", {}).name, # region
                None, #city
                IP_ADDRESS_OBJECT.cf.get("device_full", None),  # device full
                IP_ADDRESS_OBJECT.cf.get("device_vendor", None), # device vendor
                None, # domain
                TENANT_OBJECT.slug, # moniker
                None, # M_moniker
                None, # moniker_final
                str(IP_ADDRESS_OBJECT.address).split("/")[0], # ip
                None, # kontrol
                None, # comment
                ndns_configured, # natdns
                misp_configured, # mispioc
                None, # log-firewall
                syslog_configured, # log-dns
                None, # edr
                IP_ADDRESS_OBJECT.cf.get("isp", None), # isp_org
                IP_ADDRESS_OBJECT.cf.get("asn", None).lstrip("AS"), # isp_asn
                contact_name, # person
                contact_phone, # contact 
                contact_email, # email
                None, # kpx
                None  # ko.gov.ua
            ]

        ROWS.append(row)
        self.log_info(f"Row that created: {row}")

        # Помічаємо що в ми опрацювали цей ІР
        IP_ADDRESS_OBJECT.tags.add("reported")
        if commit:
            IP_ADDRESS_OBJECT.save()
            self.log_info(f"Tag reported added to ip address: {IP_ADDRESS_OBJECT.address}")

        # Запуск функції запису в Google Sheet
        self.append_rows(spreadsheet_id=SPREADSHEET_ID, rows=ROWS, token=TOKEN, page_name=PAGE_NAME)



        
             
        
        



        
        
        




        


              
        

