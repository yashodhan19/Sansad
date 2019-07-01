"""
Get profiles of Sitting Members of Parliament, Members who resigned and Members who died
"""

import json
import logging
import os
import re
import uuid

import pandas as pd

from lib.kirmi.kirmi import Kirmi

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

OUTPUT_PATH = os.path.join(os.getcwd(), "MEMBER_PROFILES")

kirmi = Kirmi(caching=True, cache_path="/Users/yashodhanjoglekar/profile_cache.sqlite3")

kirmi.default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'http://164.100.47.192/Loksabha/Members/MemberAttendance.aspx'}

url_suffix = "http://164.100.47.194/Loksabha/Members/"

with open('mp_profile.json', "r") as mpp:
    _mp_profile = json.load(mpp)


def std_field_name(field):
    """
    :param field: string
    :return: Remove all alphanumeric characters and replace whitespace with _
    """
    return re.sub('[^0-9a-zA-Z ]+', '', field.lower()
                  ).strip().replace(" ", "_")


def _get_positions_held(positions, rows):
    """
    :param positions: list
    :param rows: soup object
    :return: list of positions held with  "^" element as a seperator
    """
    for row in rows.find_all('tr'):
        cells = row.find_all(
            'td',
            attrs={
                "class": re.compile(".+")},
            recursive=False)
        for field in cells:
            if field.get("width"):
                if field.get_text().lower().strip() == "":
                    pass
                else:
                    positions.append("^")
                    positions.append(
                        field.get_text().lower().strip().replace(
                            "\n", " "))
            else:
                positions.append(
                    field.get_text().lower().strip().replace(
                        "\n", " "))


def _update_mp_profile(mp_profile, rows):
    for row in rows.find_all('tr'):
        cells = row.find_all(
            'td',
            attrs={
                "class": re.compile(".+")},
            recursive=False)
        if len(cells) >= 2:
            field_name = None
            field_text = None
            for field in cells:

                if str(field["class"][0]) == "darkerb":
                    field_name = std_field_name(field.get_text())
                else:
                    field_text = "" if not field_text else field_text.strip().replace("\n", " ")
                    field_text += field.get_text().strip().replace("\n", " ")

            if field_text and field_name:
                mp_profile[field_name] = re.sub(
                    r"\s+", " ", field_text)


def parse_profile(response, profile):
    soup = kirmi.get_soup(response=response)
    mp_profile = _mp_profile.copy()
    mp_profile.update(profile)

    image_url = (soup.find("img", attrs={"src": re.compile("photo")})["src"])

    image_response = kirmi.request(image_url, download=True)

    with open(os.path.join(OUTPUT_PATH, profile["id"] + ".jpg"), 'wb') as img_file:
        for chunk in image_response:
            img_file.write(chunk)
    del image_response

    positions = dict()

    for rows in soup.find_all(
            "table", attrs={"id": re.compile("ContentPlaceHolder1.*", re.IGNORECASE)}):

        if re.search("ContentPlaceHolder.*3", rows["id"], re.IGNORECASE):
            _get_positions_held(positions, rows)

        if re.search("ContentPlaceHolder.*(1|2)", rows["id"], re.IGNORECASE):
            _update_mp_profile(mp_profile, rows)

    mp_profile["positions_held"] = json.dumps(positions)

    df = pd.DataFrame(mp_profile)

    filename = 'members_loksabha.csv'
    filename = os.path.join(OUTPUT_PATH, filename)

    if not os.path.exists(filename):
        df.to_csv(filename, index=False)

    else:
        with open(filename, 'a') as f:
            df.to_csv(f, header=False, index=False)

    with open(os.path.join(OUTPUT_PATH, profile["id"] + ".json"), 'w') as f:
        f.write(json.dumps(mp_profile))


def get_profile(profile):

    response = kirmi.request(profile["link"])
    parse_profile(response, profile)


def get_sitting_member_profiles(soup):

    profile_links = []
    for members in soup.find_all("table")[6].find_all('tr')[2:]:
        for td in members.find_all("td"):
            for a in td.find_all('a', href=True, limit=1):

                try:
                    profile = dict()
                    profile["id"] = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(a)))
                    profile["full_name"] = a["title"]
                    profile["link"] = url_suffix + a["href"]
                    profile_links.append(profile)

                    logger.info("Getting info for : %s", profile)

                    get_profile(profile)

                except Exception:
                    logger.exception("ERROR GETING PROFILE FOR MP ")


def get_former_member_profiles(soup):
    for i in range(3):
        member_profiles = soup.find_all('table')[i].find_all('tr')
        date_field = member_profiles[0].findAll(
            'td')[4].get_text().strip().lower()
        date_field = re.sub('[^0-9a-zA-Z ]+', '', date_field).strip().replace(" ",
                                                                              "_")
        for x in member_profiles[1:]:

            try:
                c = x.findAll('td')
                profile = dict()
                profile.update({'id': str(uuid.uuid5(uuid.NAMESPACE_DNS, str(c))),
                                'full_name': c[1].get_text().strip(),
                                'link': url_suffix + c[1].find("a")["href"],
                                'party_name': c[2].get_text().strip(),
                                "constituency": c[3].get_text().strip(),
                                date_field: c[4].get_text().strip()})

                if profile["full_name"] == "":
                    continue

                logger.info("Getting info for : %s", profile)

                get_profile(profile)

            except Exception:
                logger.exception("ERROR GETTING PROFILE FOR MP ")


def run_process():
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    kirmi.request("https://loksabha.nic.in/")
    soup = kirmi.get_soup(
        "http://164.100.47.194/Loksabha/Members/AlphabeticalList.aspx",
        parser="html.parser")

    get_sitting_member_profiles(soup)


if __name__ == "__main__":
    run_process()



