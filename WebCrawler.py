# Built-in module to keep track of performances
import time
# Built-in module for asyncronous programming
import asyncio
# Async HTTP client/server for asyncio (module to handle asynchronous client requests)
import aiohttp
# Built-in module to handle HTML
from html.parser import HTMLParser
# Built-in module to handle URLs
from urllib.parse import urljoin, urlparse
# Built-in module to parse robots.txt files
from urllib.robotparser import RobotFileParser

# Class to parse given URLs, based on the built-in HTMLParser class
class URLParser(HTMLParser):
    # The init method recalls the one from the superclass and adds a list to keep track of found urls
    def __init__(self):
        super().__init__()
        self.found_urls = list()

    # Interested in finding all tags starting with 'a' (-> links)
    def handle_starttag(self, tag: str, attrs):
        if tag != "a":
            return
        # If the attribute of the tag is href it means that it is a link
        for attr, url in attrs:
            if attr == "href":
                self.found_urls.append(url)

# Main class to crawl the web
class WebCrawler():
    # The whole crawling is based on the given root url once initialising the class
    # There are two optional parameters which are the maximum number of urls crawled and the number of workers used to do so
    def __init__(self, root_url: str, max_urls: int = 50, num_workers: int = 5):
        self.root_url = root_url
        self.max_urls = max_urls
        self.num_workers = num_workers
        # Initialise a queue to keep track of the urls to analyse (to perform a breadth-first search)
        self.queue = asyncio.Queue()
        self.queue.put_nowait(self.root_url)
        # Create a list (set) to keep track of seen urls
        self.visited = set()

        # Parser for the robots.txt (to check what URLs can be crawled)
        self.robot_parser = RobotFileParser()
        self.robot_parser.set_url(urljoin(root_url, 'robots.txt'))
        self.robot_parser.read()

    # Function to start the crawling
    async def crawl(self):
        # Start the sessions through aiohttp
        async with aiohttp.ClientSession() as session:
            # Initialise the workers to handle more operations simultaneously
            workers = [asyncio.create_task(self.worker(session)) for _ in range(self.num_workers)]
            # Wait for all the items in the queue to be processed
            await self.queue.join()
            # Once there are no other items, stop each asynchronous task 
            for worker in workers:
                worker.cancel()

    # Function to handle each task
    async def worker(self, session):
        # Each task (or worker) runs in a loop until cancelled
        while True:
            try:
                await self.visit_url(session)
            except asyncio.CancelledError:
                return

    # Function to actually visit each URL and retrieve new URLs
    async def visit_url(self, session):
        # First get the first URL of the queue
        url = await self.queue.get()

        # If the URL was already visited or if the number of URLs exceeds the maximum number return (and set the task as done)
        if url in self.visited:
            self.queue.task_done()
            return
        if len(self.visited) >= self.max_urls:
            self.queue.task_done()
            return
        
        # Get if the links are crawlable or not, if not return (and set the task as done)
        allowed_robots = self.robot_parser.can_fetch("*", url)
        if not allowed_robots:
            print(f"Access denied by robots.txt to {url}")
            self.queue.task_done()
            return
        
        # Thus the URL is okay to visit
        self.visited.add(url)
        try:
            # Through the session created send a request to the URL
            async with session.get(url) as response:
                # If the status equals 200 it means that the request worked
                if response.status == 200:
                    # Get the HTML content and sent it to the function to parse it
                    html_content = await response.text()
                    await self.parse_url(url, html_content)
                else:
                    print(f"Failed to retrieve {url} with status: {response.status}")
        finally:
            self.queue.task_done()

    # Pass the URL and the HTML content
    async def parse_url(self, current_url: str, text: str):
        # Parse the HTML content
        parser = URLParser()
        parser.feed(text)
        # For each URL found, join it with the "base URL"
        for url in parser.found_urls:
            absolute_url = urljoin(current_url, url)
            # Check whether the network location part is the same and whether the URL has not been visited yet
            if urlparse(absolute_url).netloc == urlparse(self.root_url).netloc:
                if absolute_url not in self.visited:
                    # Add the new URL to the queue
                    await self.queue.put(absolute_url)

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
# asynchronous crawler DFS done in around 5 seconds
# asynchronous crawler BFS done in around 2 seconds with 5 workers

# When using workers, you're essentially creating multiple parallel coroutines or tasks 
# that run in the same event loop but are dedicated to performing a specific subset of tasks 
# repeatedly. In the context of a web crawler, each worker might continuously fetch URLs from a 
# queue, process them, and possibly enqueue more URLs.
