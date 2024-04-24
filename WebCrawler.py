import time
# Built-in module for asyncronous programming
import asyncio
import aiohttp
# Built-in module to handle HTML
from html.parser import HTMLParser
# Built-in module to handle URLs
from urllib.parse import urljoin, urlparse
# Built-in module to parse robots.txt files
from urllib.robotparser import RobotFileParser

# Class to parse given URLs, based on the HTMLParser class built-in Python
class URLParser(HTMLParser):
    # The init method recalls the one from the superclass ...
    def __init__(self):
        super().__init__()
        self.found_urls = list()

    # Interested in finding all tags starting with 'a' (-> links)
    def handle_starttag(self, tag: str, attrs):
        if tag != "a":
            return
        
        for attr, url in attrs:
            if attr == "href":
                self.found_urls.append(url)

# Main class to crawl the web
class WebCrawler():
    def __init__(self, root_url: str, max_depth: int = 2, max_urls: int = 25):
        self.root_url = root_url
        self.max_urls = max_urls
        # self.max_depth = max_depth
        self.visited = set()
        self.session = None

        # Parser for the robots.txt (to check what URLs can be crawled)
        self.robot_parser = RobotFileParser()
        self.robot_parser.set_url(urljoin(root_url, 'robots.txt'))
        self.robot_parser.read()

    async def crawl(self):
        async with aiohttp.ClientSession() as self.session:
            await self.visit_url(self.root_url, 0)

    async def visit_url(self, url: str, depth: int):
        if url in self.visited:
            return
        if len(self.visited) >= self.max_urls:
            return
        if depth > self.max_depth:
            return
        
        allowed_robots = self.robot_parser.can_fetch("*", url)
        if not allowed_robots:
            print(f"Access denied by robots.txt to {url}")
            return
        
        # Thus the URL is okay to visit
        self.visited.add(url)
        # response = requests.get(url)
        # html_content = response.text
        # Here it could be useful to use a try except..
        async with self.session.get(url) as response:
            if response.status == 200:
                html_content = await response.text()
                await self.parse_url(url, html_content, depth)
            else:
                print(f"Failed to retrieve {url} with status: {response.status}")

    # Pass the URL, the HTML_content and the depth?
    async def parse_url(self, current_url: str, text: str, depth: int):
        parser = URLParser()
        parser.feed(text)
        for url in parser.found_urls:
            absolute_url = urljoin(current_url, url)
            if urlparse(absolute_url).netloc == urlparse(self.root_url).netloc:
                await self.visit_url(absolute_url, depth + 1)

crawler = WebCrawler("https://books.toscrape.com/")
start = time.perf_counter()
asyncio.run(crawler.crawl())
end = time.perf_counter()
seen = sorted(crawler.visited)
print("Results:")
for url in seen:
    print(url)
print(f"Found: {len(seen)} URLs")
print(f"Done in {end - start:.2f}s")

# synchronous crawler done in around 22 seconds
# asynchronous crawler done in around 4 seconds

# urls = list()
# seen_urls = set()
# limit = 25
# total = 0

# urls.append("https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")

# # while total <= limit:

# url = urls.pop(0)

# response = requests.get(url)
# # print(response.text)

# parser = URLParser(url)
# parser.feed(response.text)

# urls.extend(parser.found_urls)

# print(urls)

# When using workers, you're essentially creating multiple parallel coroutines or tasks that run in the same event loop but are dedicated to performing a specific subset of tasks repeatedly. In the context of a web crawler, each worker might continuously fetch URLs from a queue, process them, and possibly enqueue more URLs.
