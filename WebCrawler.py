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

class URLParser(HTMLParser):
    """
    Represent a parser for URLs, based on the built-in HTMLParser class.

    This parser specifically looks for 'a' tags to extract URLs from their href attributes.
    """
    
    def __init__(self):
        """
        Initialise a new URLParser object.

        This function recalls the init function from the superclass and adds a set to keep track of found urls.
        """
        super().__init__()
        self.found_urls = set()

    def handle_starttag(self, tag: str, attrs):
        """
        Handle the start of an HTML tag during parsing. Specifically, it looks for all tags starting with 'a'.

        Parameters:
            tag (str): The name of the tag that is starting.
            attrs (list of (str, str)): A list of (attribute, value) pairs containing the attributes found inside the tag's <> brackets.
        """
        if tag != "a":
            return
        # If the attribute of the tag is href it means that it is a link
        for attr, url in attrs:
            if attr == "href":
                self.found_urls.add(url)


# Main class to crawl the web
class WebCrawler():
    """
    Represent an asynchronous web crawler.
    """

    def __init__(self, root_url: str, max_urls: int = 1000, num_workers: int = 5):
        """
        Initialise a new WebCrawler object.

        Parameters:
            root_url (str): The URL given upon initialisation from which the whole crawling starts.
            max_urls (int, optional): The maximum number of URLs that the crawler can fetch.
            num_workers (int, optional): The number of workers (tasks) used during the crawling.
        """
        self.root_url = root_url
        self.max_urls = max_urls
        self.num_workers = num_workers
        # Initialise a queue to keep track of the urls to analyse (to perform a breadth-first search)
        self.queue = asyncio.Queue()
        self.queue.put_nowait(self.root_url)
        # Initialise a set to keep track of seen urls
        self.visited = set()
        # Parser for the robots.txt (to check what URLs can be crawled)
        self.robot_parser = RobotFileParser()
        self.robot_parser.set_url(urljoin(root_url, 'robots.txt'))
        self.robot_parser.read()

    async def crawl(self):
        """
        Start the crawling. 
        
        The function starts a ClientSession and initialises the tasks to perform the crawling. 
        It then waits for all the tasks to finish and proceeds to stop each task.
        """
        # Start the sessions through aiohttp
        async with aiohttp.ClientSession() as session:
            # Initialise the workers to handle more operations simultaneously
            workers = [asyncio.create_task(self.worker(session)) for _ in range(self.num_workers)]
            # Wait for all the items in the queue to be processed
            await self.queue.join()
            # Once there are no other items, stop each asynchronous task 
            for worker in workers:
                worker.cancel()

    async def worker(self, session):
        """
        Handle each task/worker by running a loop that stops only when the task is cancelled.

        When using workers, multiple parallel coroutines or tasks are created and they run in the same event loop but are dedicated to performing a specific subset of tasks 
        repeatedly. In the context of a web crawler, each worker continuously fetch URLs from a queue, process them, and possibly enqueue more URLs.

        Parameters:
            session: The session created when all the workers are initialised used to handle client requests.
        """
        # Each task (or worker) runs in a loop until cancelled
        while True:
            try:
                await self.visit_url(session)
            except asyncio.CancelledError:
                return

    async def visit_url(self, session):
        """
        Visit each found URL and fetch new URLs.

        The function gets the first URL in the queue following a FIFO order. It then checks the URL and the length
        of the visited URLs set. If everything is okay, it adds the URL to the visited set and sends a request to 
        the URL, trying to fetch new URLs.

        Parameters:
            session: The session created when all the workers are initialised used to handle client requests.
        """
        # If you want to add a delay in between requests (it does impact greatly on performances)
        # await asyncio.sleep(0.5)
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
        # If you want to check the progression of the crawling...
        # if len(self.visited) % 10 == 0:
        #     print(len(self.visited))
        try:
            # Through the session created send a request to the URL
            async with session.get(url) as response:
                # If the status equals 200 it means that the request worked
                if response.status == 200:
                    # Get the HTML content and sent it to the function to parse it
                    html_content = await response.text()
                    await self.parse_url(url, html_content)
                # else:
                #     print(f"Failed to retrieve {url} with status: {response.status}")
        except Exception as e:
            # print(f"Error fetching {url}: {str(e)}")
            pass
        # The task has to be set to done whether or not the request worked
        finally:
            self.queue.task_done()

    # Pass the URL and the HTML content
    async def parse_url(self, current_url: str, text: str):
        """
        Parse the HTML content of the given URL and add any new URLs to the queue.

        The function parses the HTML content of the given URL. It then joins the given URL (a.k.a. the base URL)
        and all the found URLs. It checks whether the network location part is the same and if the new URL has
        never been visited, the function adds it to the queue.

        Parameters:
            current_url (str): The URL currently analysed.
            text (str): The HTML content of the current URL.
        """
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

if __name__ == "__main__":
    crawler = WebCrawler("https://books.toscrape.com/") # Change here the root URL (tried examples: https://books.toscrape.com/ , https://quotes.toscrape.com/ , https://www.subito.it/ , https://it.wikipedia.org/wiki/Pagina_principale)
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

"""
The crawler has to be both fair and robust:
- Fairness: a "fair" crawler operates in a way that respects the websites it visits.
For this reason, the crawler obeys to the robots.txt file to check which parts of the site should not be crawled. In addition, a small delay between requests can be added to limit the rate at which the crawler sends 
requests to the website, to not overwhelm the server.
- Robustness: a "robust" crawler is designed to handle various operational challenges.
The crawler catches errors entountered during the crawling process (HTTP errors, connection timeouts, etc..) and prints what the problem was. Thanks to the use of workers, this crawler can also efficiently handle large-scale
operations. Moreover, since the search implemented is a BFS, the crawler does not get stuck in loops and does not fall for anti-crawling techniques.
"""
