import logging
import requests
import time
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Kirmi():
    def __init__(self, **kwargs):
        self.tries = kwargs.pop('tries', 3)
        self.sleep_time = kwargs.pop('sleep', 5)
        self.timeout = kwargs.pop('timeout', 10)
        self.parser = kwargs.pop('parser', 'html.parser')
        self.default_headers = kwargs.pop('default_headers', dict())
        self.proxies = kwargs.pop('proxies', None)
        self.session = kwargs.pop('session', None)
        if self.session is None:
            self.create_new_session()

    def create_new_session(self):
        self.session = requests.Session()
        if self.proxies:
            self.session.proxies.update(self.proxies)

    def make_request(self, url, headers=None, data=None):
        """
        :param url: URL to send
        :param headers: dictionary of headers to send
        :param data: the body to attach to the request
        :return:
        """

        if headers is None:
            headers = self.default_headers

        for i in range(self.tries):
            if self.session is None:
                self.create_new_session()

            try:
                if data is None:
                    response = self.session.get(
                        url=url, headers=headers, timeout=self.timeout)
                else:
                    response = self.session.post(
                        url=url, headers=headers, data=data, stream=True)

                logger.debug("Request time elapsed : %s",
                             response.elapsed.total_seconds())

                if response.status_code != 200:
                    logger.error(response.status_code)
                    if i < self.tries - 1:
                        logger.warning(
                            "Trying again in %s seconds!", self.sleep_time)
                        time.sleep(self.sleep_time)
                        continue
                    logger.warning("Exhausted all tries!")

                return response

            except requests.exceptions.HTTPError as errh:
                logger.error("Http Error:", errh)
            except requests.exceptions.ConnectionError as errc:
                logger.error("Error Connecting:", errc)
            except requests.exceptions.Timeout as errt:
                logger.error("Timeout Error:", errt)
            except requests.exceptions.RequestException as err:
                logger.error("OOps: Something Else", err)

    def get_soup(self, url=None, headers=None, data=None,
                 parser=None, response=None):
        """
        :param url:
        :param headers:
        :param data:
        :param parser:
        :param response:
        :return:
        """

        if parser is None:
            parser = self.parser

        if response is None:
            response = self.make_request(url, headers=headers, data=data)

        soup = BeautifulSoup(response.text, parser)

        return soup


if __name__ == "__main__":

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36',
               'Content-Type': 'application/x-www-form-urlencoded'}

    kirmi = Kirmi(default_headers=headers)

    kirmi.get_soup("http://www.reddit.com/")
