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
    soup = BeautifulSoup(data, "html.parser")
    seo_table = soup.find("div", {"class": "seo-table"})

    results = {} 
    for row in seo_table.find_all("div", {"class": "seo-table-row"}):
        key = row.find("div", {"class": "seo-table-col-1"})
        if key:
            key = key.get_text().strip().split('\n')[0].strip()

        v= row.find(["span", "p", "div"], {"class": "seo-table-col-2"})
        if v:
            if key in ("Уповноважені особи", "Відомості про осіб, які можуть вчиняти дії від імені юридичної особи, у тому числі підписувати договори, подавати документи для державної реєстрації тощо: прізвище, ім’я, по батькові, дані про наявність обмежень щодо представництва юридичної особи"):
                continue
            elif key == "Види діяльності":
                v = v.get_text().strip().split('\n')[2].strip()

            elif key == "Контактна інформація":
                v = v.get_text().strip().split('\n')[3].strip()

            elif key == "Дата реєстрації":
                v = v.get_text().strip().split('\n')[0][0:10]

            else:
                v = v.get_text().strip().split('\n')[0].strip()

        if key and v:
            results.update({key: v})

    return(results)



print(parse(get_info("23250933")))
