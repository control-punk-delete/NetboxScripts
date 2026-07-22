import requests
from bs4 import BeautifulSoup

URL = "https://youcontrol.com.ua/catalog/company_details/"

def get_info(edrpou: str = None):
    if not edrpou:
        raise "Missing require argument"

    FULL_URL = URL + edrpou + "/"

    headers = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"}

    data = requests.get(FULL_URL, headers=headers)

    if data.status_code != 200:
        raise "YoControl Error - page not found"
    
    return data.text


def parse(data):


    you_control_data = {}

    soup = BeautifulSoup(data, "html.parser")
    containers = soup.find_all("div", {"class": "seo-table-contain"})

    for container in containers:
        seo_table_head = container.find("div", {"class": "seo-table-head"})
        seo_table_name = seo_table_head.find(["div", "h2"], {"class": "seo-table-name"})
        seo_table_date = seo_table_head.find("div", {"class": "seo-table-date"})

        if seo_table_name:
            print(seo_table_name.get_text(strip=True))

            if seo_table_date:
                print(seo_table_date.find("span").get_text())

        else:
            continue

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

                if key == "Перелік засновників/учасників юридичної особи":
                    you_control_data["parent_tenant_name"] = values[0].strip()
                    you_control_data["parent_tenant_edrpou"] = values[2].strip()
                    you_control_data["parent_tenant_address"] = values[4].strip()

    return you_control_data


data = parse(get_info("37225752"))


print (data)