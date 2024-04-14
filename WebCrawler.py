import time
import requests
from html.parser import HTMLParser

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
    def __init__(self):
        super().__init__()
        self.found_urls = list()

    def handle_starttag(self, tag: str, attrs):
        if tag != "a":
            return
        
        for attr, url in attrs:
            if attr == "href":

                print(url)
                
                # Here check if the URL is okay (-> FILTER)
                self.found_urls.append(url)

urls = list()
seen_urls = set()
limit = 25
total = 0

urls.append("https://books.toscrape.com")

# while total <= limit:

url = urls.pop(0)

time.sleep(.1)

response = requests.get(url)
# print(response.text)

parser = URLParser()
parser.feed(response.text)

urls.extend(parser.found_urls)

# print(urls)
