import requests
import asyncio
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

# class WebCrawler():
#     def __init__(self, urls, workers: int = 10, limit: int = 25):
#         self.urls = set(urls)
#         self.seen_urls = {}
#         self.workers = workers # used for asyncronous work
#         self.limit = limit 

class URLFilterer():
    def __init__(self):
        pass

    def filter_url(self):
        pass


class URLParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.found_urls = list()

    def handle_starttag(self, tag: str, attrs):
        if tag != "a":
            return
        
        for attr, url in attrs:
            if attr == "href":
                absolute_url = urljoin(self.base_url, url)

                # Here check if the URL is okay (-> FILTER) ?
                self.found_urls.append(absolute_url)

class WebCrawler():
    def __init__(self, root_url, max_depth = 2, max_pages = 10):
        self.root_url = root_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited = set()

        self.robot_parser = RobotFileParser()
        self.robot_parser.set_url(urljoin(root_url, 'robots.txt'))
        self.robot_parser.read()

    def crawl(self):
        pass

urls = list()
seen_urls = set()
limit = 25
total = 0

urls.append("https://books.toscrape.com")

# while total <= limit:

url = urls.pop(0)

response = requests.get(url)
# print(response.text)

parser = URLParser(url)
parser.feed(response.text)

urls.extend(parser.found_urls)

# print(urls)
