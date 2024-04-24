# Asynchronous Web Crawler

The goal of this project was to implement a web crawler in Python without using external libraries such as BeautifulSoup, Scrapy or Selenium.
The only external library used is *aiohttp*, used to handle client requests.  
Since the objective was to create a web crawler both fair and robust, the crawler is subject to the rules of the *robots.txt* file and to avoid overloading a website it is possible to add a delay to the requests.  
As said, this crawler is asynchronous, which means that it can handle multiple requests at a time, improving the performances and going from over 20 seconds in the synchronous crawler to around 2 seconds in this case (same environment: same website and same URLs crawled).  
Lastly, this crawler only crawls URLs that are within the same domain of the *root URL* to avoid problems leaving said domain and possible new rules, etc...