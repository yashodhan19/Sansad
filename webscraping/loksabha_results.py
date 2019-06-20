import logging
import os
import sys

from bs4 import BeautifulSoup
import pandas as pd

from lib.kirmi.kirmi import Kirmi

scraper = Kirmi()
scraper.sleep_time = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


OUTPUT_PATH = sys.argv[0]


def get_url(state_code, ac_code):
    """
    :param state_code: 3 digit alphanumeric code
    :param ac_code: numeric
    :return:
    """
    url = f"http://results.eci.gov.in/pc/en/constituencywise/Constituencywise{state_code}{ac_code}.htm?ac={ac_code}"
    return url


def get_state_list(xml_path=None):
    """
    :param xml_path: path to xml with the state and assembly constituency mappings
    :return:
    """
    with open(xml_path) as f:
        soup = BeautifulSoup(f.read(), 'lxml')

    return soup.find_all('option'), soup.find_all('input')


def get_jk_results(c, state_code, state_name, ac_code, ac_name):
    # J & K has migrant votes
    # We combine them with Postal votes
    jk_dict = {'OSN': c[0].get_text().strip(),
               'Candidate': c[1].get_text().strip(),
               'Party': c[2].get_text().strip(),
               "EVM Votes": c[3].get_text().strip(),
               "Postal Votes": int(c[4].get_text().strip()) + int(c[5].get_text().strip()),
               "Total of Votes": c[6].get_text().strip(),
               "Percent of Votes": c[7].get_text().strip(),
               "State": state_name,
               "State_Code": state_code,
               "AC_Code": ac_code,
               "Constituency": ac_name
               }

    return jk_dict


def get_constituency_results(url, state_code, state_name, ac_code, ac_name):
    """
    :param url: str, url
    :param state_code: str, state code (alphanumeric)
    :param state_name: str, state name
    :param ac_code: str, assembly constituency code (alphanumeric)
    :param ac_name: str, assembly constituency name (alphanumeric)
    :return:
    """
    logger.debug("getting data from : %s", url)
    soup = scraper.get_soup(url)

    data = []

    for candidate in soup.findAll('table')[10].findAll('tr')[3:-1]:
        c = candidate.findAll('td')
        candidate_dict = dict()

        if state_code == "S09":
            candidate_dict.update(get_jk_results(
                c, state_code, state_name, ac_code, ac_name))
        else:
            candidate_dict.update({'OSN': c[0].get_text().strip(),
                                   'Candidate': c[1].get_text().strip(),
                                   'Party': c[2].get_text().strip(),
                                   "EVM Votes": c[3].get_text().strip(),
                                   "Postal Votes": c[4].get_text().strip(),
                                   "Total of Votes": c[5].get_text().strip(),
                                   "Percent of Votes": c[6].get_text().strip(),
                                   "State": state_name,
                                   "State_Code": state_code,
                                   "AC_Code": ac_code,
                                   "Constituency": ac_name
                                   })

        data.append(candidate_dict)

    filename = f"loksabha2019_results_state-{state_code}_ac-{ac_code}.csv"

    filename = os.path.join(OUTPUT_PATH, filename)

    df = pd.DataFrame(data)
    logger.debug("found %s records", len(df))
    df.to_csv(filename, sep="|", index=False)


def process():

    state_codes, states = get_state_list(xml_path='./constituencies.xml')
    state_codes = {s["value"]: s.get_text() for s in state_codes}
    for state in states:
        state_code = state["id"]
        state_name = state_codes[state_code]
        logger.info("=====> %s ", state_name)
        ac_list = state["value"].split(";")[:-1]
        for ac in ac_list:
            ac_details = ac.split(",")
            ac_code = ac_details[0]
            ac_name = ac_details[1]
            logger.info("Constituency:  %s ", ac_name)
            url = get_url(state_code=state_code, ac_code=str(ac_code))
            get_constituency_results(
                url, state_code, state_name, ac_code, ac_name)


if __name__ == "__main__":
    process()
