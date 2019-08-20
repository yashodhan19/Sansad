"""
The LS Bulletin - I documents the proceedings of the house
"""

import logging
import os
import re
from time import strptime

from lib.kirmi.kirmi import Kirmi

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

kirmi = Kirmi(caching=True, cache_path="./bulletin_cache.sqlite3")

kirmi.default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'http://loksabhaph.nic.in/Business/UserBulletin1.aspx',
    'Cache-Control': 'max-age=0',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive'}

OUTPUT_PATH = os.path.join(os.getcwd(), "LOKSABHA_BULLETIN")

def clean_ls_session(ls_ses):
    """
    :param ls_ses: (str) contains date range 'I (17/06/2019 To 07/08/2019)'
    :return: (str) Roman Numeral
    """
    if ls_ses is not None:
        ls_ses = re.search("([^\s]+)", ls_ses.strip()).group(0)
        return str(ls_ses).strip()

def convert_month(m=None):
    """
    :param m: str
    :return: int
    """
    logger.debug("Found Month : {} - of type : {}".format(m, type(m)))

    if len(m) > 3:
        m = m.strip()[:3].lower()
    return strptime(m, '%b').tm_mon

def get_ls_number(soup):
    """
    :param soup:
    :return: (list)
    """
    numbers = soup.find(
        "select", attrs={
            "id": "ContentPlaceHolder1_ddlLoksabha"}).find_all("option")
    return [ls.text for ls in numbers]

def get_ls_session_dates(soup):
    """
    for a given LS session, get a list of all dates
    :return:
    """
    ls_session_dates = soup.find(
        "select", attrs={
            "id": "ContentPlaceHolder1_ddlSession"}).find_all("option")
    return [ls.text for ls in ls_session_dates]

def get_ls_session_month(soup):
    """
    for a given LS session, get a list of all dates
    :return:
    """
    ls_session_month = soup.find(
        "select", attrs={
            "id": "ContentPlaceHolder1_ddlMonth"}).find_all("option")
    return [ls.text for ls in ls_session_month]

def get_PDF_links(soup):
    """
    for a given LS session, get a list of all dates
    :return:
    """
    pdf_links = soup.find("div", class_="calendar_panel time_table").find_all("a", class_="lnk")
    pdf_links_parsed = []
    for p in pdf_links:
        if re.search("http.+\.pdf", p["onclick"]):
            pdf_links_parsed.append(re.search("http.+\.pdf", p["onclick"]).group(0))

    return pdf_links_parsed

def get_form_data(soup, ls_number=None, ls_session=None, ls_month=None, event_target=None):
    """
    :param soup:
    :param ls_session:
    :param ls_date:
    :param event_target: EVENT TARGET
    :return: (dict)
    """
    form_data = dict()

    if ls_number:
        form_data['ctl00$ContentPlaceHolder1$ddlLoksabha'] = ls_number

    if ls_session:
        form_data['ctl00$ContentPlaceHolder1$ddlSession'] = ls_session

    if ls_month:
        form_data['ctl00$ContentPlaceHolder1$ddlMonth'] = ls_month

    for i in soup.find_all('input'):
        if i.attrs['name'].find("__") == 0:
            form_data.update({i.attrs['name']: i.attrs['value']})

    if event_target:
        form_data['__EVENTTARGET'] = event_target


    return form_data

def download_bulletin_pdf(PDF_LINKS, ls_number, ls_session, ls_month):
    """
    :param PDF_LINKS:
    :param ls_number:
    :param ls_session:
    :param ls_month:
    :return:
    """

    for url in PDF_LINKS:
        date = re.search("([^\/]+)\.pdf$", url).group(1).replace(".", "")

        pdf_response = kirmi.request(url, download=True)

        filename = '{0}_{1}_{2}_{3}.pdf'.format(
        ls_number,
        ls_session.strip(),
        ls_month,
        date)

        logger.debug("FILENAME : {}".format(filename))

        with open(os.path.join(OUTPUT_PATH, filename), 'wb') as pdf_file:
            for chunk in pdf_response:
                pdf_file.write(chunk)
        del pdf_response


def run_process():

    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    kirmi.request("https://loksabha.nic.in/")
    soup = kirmi.get_soup(
        "http://loksabhaph.nic.in/Business/UserBulletin1.aspx")

    ls_numbers = get_ls_number(soup)

    for ls_num in ls_numbers:

        data = get_form_data(soup,
                             ls_number=ls_num,
                             ls_session=None,
                             ls_month=None,
                             event_target="ctl00$ContentPlaceHolder1$ddlLoksabha")

        soup = kirmi.get_soup("http://loksabhaph.nic.in/Business/UserBulletin1.aspx",
                              data=data)

        ls_sessions = get_ls_session_dates(soup)

        logger.info(ls_sessions)

        for ls_ses in ls_sessions:
            ls_ses = clean_ls_session(ls_ses).ljust(10)

            data = get_form_data(soup,
                                 ls_number=ls_num,
                                 ls_session=ls_ses,
                                 ls_month=None,
                                 event_target="ctl00$ContentPlaceHolder1$ddlMonth")

            soup = kirmi.get_soup("http://loksabhaph.nic.in/Business/UserBulletin1.aspx",
                                  data=data)
            months = get_ls_session_month(soup)


            for month in months:

                month = str(convert_month(m=month))

                data = get_form_data(soup,
                             ls_number=ls_num,
                             ls_session=ls_ses,
                             ls_month=month,
                             event_target="ctl00$ContentPlaceHolder1$ddlMonth")

                soup = kirmi.get_soup("http://loksabhaph.nic.in/Business/UserBulletin1.aspx",
                                       data=data)

                PDF_LINKS = get_PDF_links(soup)

                logger.info(ls_num, "**************"*5,month, " - ", ls_ses, "\n", PDF_LINKS, "\n" )

                download_bulletin_pdf(PDF_LINKS, ls_num, ls_ses, month)

if __name__ == "__main__":
    run_process()
