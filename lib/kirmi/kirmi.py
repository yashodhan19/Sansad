import logging
import requests
import time
import json
import sqlite3
import uuid

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLiteCache(object):
    """SQLite cache for request responses."""
    _columns = ['key', 'status', 'modified', 'encoding', 'data', 'headers']

    def __init__(self, cache_path, check_last_modified=False):
        self.cache_path = cache_path
        self.check_last_modified = check_last_modified
        self._conn = sqlite3.connect(cache_path)
        self._conn.text_factory = str
        self._create_table()

    def _create_table(self):
        """Create table for storing request information and response."""
        self._conn.execute("""CREATE TABLE IF NOT EXISTS cache
                (key text UNIQUE, status integer, modified text,
                 encoding text, data blob, headers blob)""")

    def set(self, key, response):
        """Set cache entry for key with contents of response."""

        print(response)
        mod = response.headers.pop('last-modified', None)
        status = int(response.status_code)
        rec = (key, status, mod, response.encoding, response.content,
               json.dumps(dict(response.headers)))
        with self._conn:
            self._conn.execute("DELETE FROM cache WHERE key=?", (key, ))
            self._conn.execute("INSERT INTO cache VALUES (?,?,?,?,?,?)", rec)

    def get(self, key):
        """Get cache entry for key, or return None."""
        query = self._conn.execute("SELECT * FROM cache WHERE key=?", (key,))
        rec = query.fetchone()
        if rec is None:
            return None
        rec = dict(zip(self._columns, rec))

        resp = requests.Response()
        resp._content = rec['data']
        resp.status_code = rec['status']
        resp.encoding = rec['encoding']
        resp.headers = json.loads(rec['headers'])
        resp.url = key
        return resp

    def clear(self):
        """Remove all records from cache."""
        with self._conn:
            self._conn.execute('DELETE FROM cache')

    def __del__(self):
        self._conn.close()


class Kirmi():
    def __init__(self, **kwargs):
        self.retry_attempts = kwargs.pop('retry_attempts', 3)
        self.retry_sleep_time = kwargs.pop('retry_sleep_time', 5)
        self.timeout = kwargs.pop('timeout', 10)
        self.parser = kwargs.pop('parser', 'html.parser')
        self.default_headers = kwargs.pop('default_headers', dict())
        self.proxies = kwargs.pop('proxies', None)
        self.session = kwargs.pop('session', None)
        if self.session is None:
            self.create_new_session()
        self.cache_path = kwargs.pop('cache_path', None)
        self.caching = kwargs.pop('caching', None)
        if self.caching:
            self.cache = SQLiteCache(cache_path=self.cache_path)

    def create_new_session(self):
        self.session = requests.Session()
        if self.proxies:
            self.session.proxies.update(self.proxies)

    def create_cache_key(self, url, headers=None, data=None):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, json.dumps({'url': url, 'headers': headers, 'data': data})))

    def make_request(self, url, headers=None, data=None):
        """
        :param url: URL to send
        :param headers: dictionary of headers to send
        :param data: the body to attach to the request
        :return:
        """

        if headers is None:
            headers = self.default_headers

        for tries in range(self.retry_attempts):
            if self.session is None:
                self.create_new_session()

            try:
                if self.caching:

                    cache_key = self.create_cache_key(
                        url, headers=headers, data=data)
                    print(cache_key)
                    cached_response = self.cache.get(cache_key)

                    if cached_response:
                        return cached_response

                if data is None:
                    response = self.session.get(
                        url=url, headers=headers, timeout=self.timeout)
                else:
                    response = self.session.post(
                        url=url, headers=headers, data=data, stream=True)

                if self.caching and response and response.status_code == 200:
                    self.cache.set(cache_key, response)

                logger.debug("Request time elapsed : %s",
                             response.elapsed.total_seconds())

                if response.status_code != 200:
                    logger.error(response.status_code)
                    if tries < self.retry_attempts - 1:
                        logger.warning(
                            "Trying again in %s seconds!", self.retry_sleep_time)
                        time.sleep(self.retry_sleep_time)
                        continue
                    logger.warning("Exhausted all retry_attempts!")

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

    kirmi = Kirmi(default_headers=headers, caching=True,
                  cache_path="/Users/yashodhanjoglekar/cameralism/data.sqlite3")

    kirmi.get_soup("http://www.reddit.com/")

    kirmi.get_soup("http://www.reddit.com/")

    print(kirmi.get_soup("http://www.reddit.com/"))
