"""
As per practice, members who are Ministers/having Ministers Rank, Leader of the Opposition, Deputy Speaker
do not sign the Attendance Register.
Salary and allowances of Ministers are governed by Salary and Allowances of Ministers of Parliament Act, 1952,
its amendments made from time to time and rules made there under and are provided by the concerned Ministry.
Salary and allowances of the Leader of Opposition is governed by the Salary and Allowances of the
Leaders of Opposition in Parliament Act, 1977 and rules made there under.
"""

import logging
import os
import re

import pandas as pd

from lib.kirmi.kirmi import Kirmi
from utils.roman import from_roman

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LS_NUMBER = '16'
OUTPUT_PATH = os.path.join(os.getcwd(), ("LOKSABHA_ATTENDANCE_" + str(LS_NUMBER)))

kirmi = Kirmi()

kirmi.default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'http://164.100.47.192/Loksabha/Members/MemberAttendance.aspx'}


def parse_data(soup, ls_session, ls_date):
    """
    :param soup:
    :param ls_session: LS session number
    :param ls_date: LS date
    :return: data dictionary
    """
    data = []

    for x in soup.findAll('table')[3].findAll('tr')[2:-1]:
        c = x.findAll('td')
        z = {}
        z.update({'divNo': c[0].get_text().strip(),
                  'MemberName': c[1].get_text().strip(),
                  'AttendanceStatus': c[2].get_text().strip(),
                  "ls_session": ls_session,
                  "ls_date": ls_date})

        data.append(z)

    filename = 'members-loksabha{0}-session{1}-{2}.csv'.format(
        LS_NUMBER,
        ls_session,
        ls_date)

    filename = os.path.join(OUTPUT_PATH, filename)

    df = pd.DataFrame(data)
    df.to_csv(filename, sep="|")

    return filename


def get_form_data(soup, ls_session, ls_date, event_target):
    """
    :param soup:
    :param ls_session:
    :param ls_date:
    :param event_target: EVENT TARGET FOR PRINT
    :return:
    """
    form_data = {'ctl00$ContentPlaceHolder1$DropDownListLoksabha': LS_NUMBER,
                 'ctl00$ContentPlaceHolder1$DropDownListSession': ls_session,
                 'ctl00$ContentPlaceHolder1$DropDownListDate': ls_date}

    for i in soup.find_all('input'):
        if i.attrs['name'].find("__") == 0 and i.attrs['name'] not in [
            'ctl00$ContentPlaceHolder1$DropDownListLoksabha',
            'ctl00$ContentPlaceHolder1$DropDownListSession',
                'ctl00$ContentPlaceHolder1$DropDownListDate']:
            form_data.update({i.attrs['name']: i.attrs['value']})

    form_data['__EVENTTARGET'] = event_target

    return form_data


def get_ls_number(soup):
    """
    Get Lok Sabha Number
    :param soup:
    :return:
    """
    numbers = soup.find(
        "select", attrs={
            "id": "ContentPlaceHolder1_DropDownListLoksabha"}).find_all("option")
    return [ls.text for ls in numbers]


def get_all_ls_sessions(soup):
    """
    From the landing page, get a list of all Lok Sabha sessions for a given Lok Sabha Number
    :return:
    """
    ls_sessions_list = []
    ls_sessions = soup.find(
        "select", attrs={
            "id": "ContentPlaceHolder1_DropDownListSession"}).find_all("option")
    print(ls_sessions)
    for ls in ls_sessions:
        # The site has Roman Numerals
        session_number = re.search(r"^[IVXLCDM]+(?:\s)", ls.text)
        if session_number is not None:
            ls_sessions_list.append(from_roman(
                session_number.group(0).strip()))

    return ls_sessions_list


def get_ls_session_dates(soup):
    """
    for a given LS session, get a list of all dates
    :return:
    """
    ls_session_dates = soup.find(
        "select", attrs={
            "id": "ContentPlaceHolder1_DropDownListDate"}).find_all("option")
    return [ls.text for ls in ls_session_dates]


def get_mp_attendance(soup):

    ls_session_dates = get_ls_session_dates(soup)
    ls_date_prev = None

    for ls_session in get_all_ls_sessions(soup):

        logger.debug("STARTING SESSION >> >> >> >> %s >>> \n ", ls_session)

        for ls_date in ls_session_dates:
            logger.info("STARTING DATE : %s ", ls_date)
            ls_date_prev = ls_date

            # event_target for "PRINT"
            # This gives access to all Data Points for a given date
            event_target = "ctl00$ContentPlaceHolder1$LinkButton1"
            data = get_form_data(
                soup, ls_session, ls_date, event_target)

            all_soup = kirmi.get_soup("http://164.100.47.194/Loksabha/Members/MemberAttendance.aspx",
                                      data=data)

            outputfile = parse_data(all_soup, ls_session, ls_date)

            logger.debug("File saved to : %s", outputfile)

        data = get_form_data(soup, ls_session - 1, ls_date_prev,
                             "ctl00$ContentPlaceHolder1$DropDownListSession")

        soup = kirmi.get_soup("http://164.100.47.194/Loksabha/Members/MemberAttendance.aspx",
                              data=data)
        ls_session_dates = get_ls_session_dates(soup)


def run_process():

    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    kirmi.request("https://loksabha.nic.in/")
    soup = kirmi.get_soup(
        "http://164.100.47.194/Loksabha/Members/MemberAttendance.aspx",
        parser="html.parser")

    if LS_NUMBER != '17':
        soup = kirmi.get_soup(
            "http://164.100.47.194/Loksabha/Members/MemberAttendance.aspx",
            parser="html.parser",
            data={'__EVENTTARGET': 'ctl00$ContentPlaceHolder1$DropDownListLoksabha',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
                '__VIEWSTATE': soup.find('input',{'id':'__VIEWSTATE'}).attrs['value'],
                '__VIEWSTATEGENERATOR': soup.find('input',{'id':'__VIEWSTATEGENERATOR'}).attrs['value'],
                '__VIEWSTATEENCRYPTED':'',
                '__EVENTVALIDATION': soup.find('input', {'id': '__EVENTVALIDATION'}).attrs['value'],
                'ctl00$txtSearchGlobal':'',
               'ctl00$ContentPlaceHolder1$DropDownListLoksabha': str(LS_NUMBER)
        })

    get_mp_attendance(soup)


if __name__ == "__main__":
    run_process()
