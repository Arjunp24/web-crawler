import re

import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError, MissingSchema

import robot_parser
from url_canonicalization import URLCanonicalization


class HTMLParser:
    __symbol_map = {'&lt;': '<', '&gt;': '>', '&amp;': '&', '&nbsp;': ' '}
    parser = robot_parser.RobotParser()

    @staticmethod
    def parse_html(url):
        """
        Parses a url for its content, outgoing links and header information.
        :param url: url to be parsed.
        :return: dictionary containing cleaned content, list of cleaned outgoing urls, title, header, raw html.
        """
        try:
            s = requests.Session()
            s.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 '+\
                                      '(KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'
            url_req = s.get(url)
            bs_object = BeautifulSoup(url_req.content, 'html5lib')
        except (ConnectionError, MissingSchema):
            return None

        outgoing_links = {}
        content = ""
        header = url_req.headers
        if 'text/html' not in header['Content-Type']:
            return None

        raw_html = bs_object.prettify()
        for links in bs_object.find_all('a', href=True):
            clean_url = URLCanonicalization.clean_url(links['href'], links.text, robot_parser.get_domain(url))
            if clean_url is None or len(clean_url) <= 1:
                continue
            outgoing_links[clean_url[0]] = clean_url[1]

        head = bs_object.find_all('title')
        head = re.sub('<[^>]*>', ' ', ''.join(str(x) for x in head))

        for links in bs_object.find_all('p'):
            no_tags = re.sub('<[^>]*>', ' ', str(links))
            HTMLParser.__replace_symbols(no_tags)
            no_tags = re.sub('[^A-Za-z0-9 \\[\\]]', ' ', no_tags)
            content += no_tags

        content = re.sub(' +', ' ', content)

        return {'content': content.strip(), 'out_links': outgoing_links, 'title': head.strip(), 'header': header,
                'raw_html': raw_html}

    @staticmethod
    def __replace_symbols(text):
        """
        Replaces certain html specific symbols with their original symbol.
        :param text: text containing the symbols to be replaced.
        :return: text with the replaced symbols
        """
        for symbol in HTMLParser.__symbol_map.keys():
            text = text.replace(symbol, HTMLParser.__symbol_map[symbol])
        return text
