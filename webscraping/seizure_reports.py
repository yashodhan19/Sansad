from lib.kirmi.kirmi import Kirmi
import shutil
import re
import os
import sys

PDF_PATH = sys.argv[0]

scraper = Kirmi()


def get_pdf():
    soup = scraper.get_soup("https://eci.gov.in/search/?q=seizure")

    links = soup.find_all("a", attrs={"href": re.compile(
        "seizure-report-as-on"), "data-linktype": "link"})[0]

    soup2 = scraper.get_soup(links["href"])
    landing_page = soup2.find("a", attrs={"href": re.compile("do=download")})
    previous_page = soup2.find("a", attrs={"title": "Previous File"})
    soup3 = scraper.get_soup(landing_page["href"])

    while previous_page != None:
        if not soup2:
            soup2 = scraper.get_soup(url=previous_page["href"])
            landing_page = soup2.find(
                "a", attrs={"href": re.compile("do=download")})
            soup3 = scraper.get_soup(landing_page["href"])

        download_page = soup3.find("a", attrs={"data-action": "download"})
        response = scraper.request(url=download_page["href"], download=True)

        pdf_name = re.search("(seizure-report-as-on-\d+)",
                             download_page["href"]).group(0)
        out_filename = os.path.join(PDF_PATH, pdf_name + ".pdf")
        print(out_filename)

        with open(out_filename, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)

        previous_page = soup2.find("a", attrs={"title": "Previous File"})
        soup2 = None


if __name__ == "__main__":
    get_pdf()
