import dns.resolver
import ipaddress

from extras.scripts import *
from ipam.models import IPAddress
from netbox_dns.models import (Record)
from utilities.exceptions import AbortScript
from tenancy.models import Tenant  

 
class DnsResolve(Script):

    class Meta(Script.Meta):
        name = "DNS Resolver"
        description = "Make an resolve an DNS Record object"
        scheduling_enabled = False

    def resolve_dns_record(self, record):
        try:
            return [answer.to_text() for answer in dns.resolver.resolve(record, 'A')]
        except Exception as e:
            self.log_debug(f"Python DNS raise error: {e}")
            return []


    def run(self, data, commit):

        self.log_info(data)
        
        # Отримуємо обʼєкт ДНС запису для подальшого його зміни
        dns_record_object = Record.objects.get(pk=data.get('id', None))

        # Отримуємо рядок ДНС для виконання резолву
        dns_record_str = data.get('fqdn')[:-1]
        
        # Отримуємо Ідентифікатор Тенанта, щоб використатит його при створені ІР адрес які не існують
        tenant = None  
        if data['tenant']:  
            tenant = Tenant.objects.get(pk=data['tenant']['id'])

        # Виконання резолву домена в ІР
        resolved_ips = self.resolve_dns_record(dns_record_str)

        # Ініціалізація переліку ІД ІР обєктів, які необхідно привʼязати до ДНС запису 
        resolved_ips_id = []

        self.log_debug(f"Find {len(resolved_ips)} ip addresses: {resolved_ips}")

        # # Якщо резолв не вийшов - змінюємо статус домена на - inactive.
        if resolved_ips == []:
            dns_record_object.status = "inactive"
            dns_record_object.save()
            self.log_success(f"DNS Record {dns_record_str} has no resolved IP Address")
        
        else:
            # Перевірка чи створені обʼєкти ІР, якщо ні - створюємо 
            for ip in resolved_ips:
                ipaddr, created = IPAddress.objects.get_or_create(address= ip ,  
                                                                  defaults={ 'status': 'active',
                                                                             'tenant':  tenant} )
                # Якщо обʼєкт був створений - встановлюємо відповідний source 
                if created:
                  ipaddr.custom_field_data['source'] = "scanner"
                 
                resolved_ips_id.append(ipaddr.id)
                # Для кожного ІР привʼязуємо домен який виконав резолв
                # Отримуємо перелік вже привʼязаних доменів
                exist_domains = ipaddr.custom_field_data.get('domains')

                # Якщо привʼязані домени відсутні перевизначаємо (чомусь .get [])
                if not exist_domains:
                    exist_domains = []

                self.log_debug(f"Existed domains: {exist_domains}, type: {type(exist_domains)}")

                # Якщо даниого обʼєкта немає в вже наявному переліку додаємо його
                if not dns_record_object.id in exist_domains:
                    self.log_debug(f"Append domain to list of links {dns_record_object.id}")
                    exist_domains.append(dns_record_object.id)

                # Перевизначаємо обʼєкт та зберігаємо його
                ipaddr.custom_field_data['domains'] = exist_domains
                ipaddr.save()

        
        # Отримуємо перелік існуючих повʼязаних обʼєктів ІР адрес
        existed_ips = dns_record_object.custom_field_data.get('ip_address', [])
        self.log_debug(f"Existed IP Address: {existed_ips}")
        
        # Якщо такі обʼєкти відсутні перевизначаємо тип змінної 
        if not existed_ips:
            existed_ips = []

        # Формуємо актуальни перелік ІР адресів (Існуючі + Ті які зарезолвились). Перевизначаємо та зберігаємо обʼєкт
        dns_record_object.custom_field_data['ip_address'] = list(set( existed_ips + resolved_ips_id))
        self.log_debug(f"Update DNS Record : {existed_ips}")
        dns_record_object.save()
