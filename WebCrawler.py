import requests
# Built-in module for asyncronous programming
import asyncio
# Built-in module to handle HTML
from html.parser import HTMLParser
# Built-in module to handle URLs
from urllib.parse import urljoin, urlparse
# Built-in module to parse robots.txt files
from urllib.robotparser import RobotFileParser

# class WebCrawler():
#     def __init__(self, urls, workers: int = 10, limit: int = 25):
#         self.urls = set(urls)
#         self.seen_urls = {}
#         self.workers = workers # used for asyncronous work
#         self.limit = limit

# Class to parse given URLs, based on the HTMLParser class built-in Python
class URLParser(HTMLParser):
    # The init method recalls the one from the superclass ...
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.found_urls = list()

    # Interested in finding all tags starting with 'a' (-> links)
    def handle_starttag(self, tag: str, attrs):
        if tag != "a":
            return
        
        for attr, url in attrs:
            if attr == "href":
                absolute_url = urljoin(self.base_url, url)

                # Here check if the URL is okay (-> FILTER) ?
                self.found_urls.append(absolute_url)

# Main class to crawl the web
class WebCrawler():
    def __init__(self, root_url, max_depth = 2, max_urls = 25):
        self.root_url = root_url
        self.max_urls = max_urls
        self.max_depth = max_depth
        self.visited = set()

        # Parser for the robots.txt (to check what URLs can be crawled)
        self.robot_parser = RobotFileParser()
        self.robot_parser.set_url(urljoin(root_url, 'robots.txt'))
        self.robot_parser.read()

    def crawl(self):
        pass

    def visit_url(self, url, depth):
        if url in self.visited:
            return
        if len(self.visited) > self.max_urls:
            return
        if depth > self.max_depth:
            return
        
        allowed_robots = self.robot_parser.can_fetch("*", url)
        if not allowed_robots:
            print(f"Access denied by robots.txt to {url}")
            return
        
        # Thus the URL is okay to visit
        # ...

    def parse_url(self):
        parser = URLParser()

crawler = WebCrawler("https://books.toscrape.com/")

urls = list()
seen_urls = set()
limit = 25
total = 0

urls.append("https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")

# while total <= limit:

url = urls.pop(0)

response = requests.get(url)
# print(response.text)

parser = URLParser(url)
parser.feed(response.text)

urls.extend(parser.found_urls)

print(urls)
