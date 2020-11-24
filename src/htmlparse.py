from bs4 import BeautifulSoup
from urllib.request import urlopen, urlretrieve, Request
from urllib.error import HTTPError
from time import sleep
from enum import Enum
import re

USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'

WIKI_HOST_URL = "https://en.wikipedia.org"
SOF_HOST_URL = "https://stackoverflow.com"
MEWE_HOST_URL = "https://www.merriam-webster.com"

class Host(Enum):
    UNK = 0
    WP = 1
    ADB = 2
    IMDB = 3
    SOF = 4
    MW = 5

## ========= ##
## Wikipedia ##
## ========= ##

def getPageNameFromURL(url: str, host: Host):
    if host == Host.WP:
        return url.split("/")[-1]
    elif host == Host.ADB:
        return url.split("/")[-1]
    elif host == Host.IMDB:
        return url.split("/")[-2]
    elif host == Host.SOF:
        dirs = url.split("/")
        return f"{dirs[-2]}-{dirs[-1]}"
    elif host == Host.MW:
        return url.split("/")[-1]
    else:
        raise NotImplementedError

def getFileNameFromPageName(name: str, host: Host):
    if host == Host.WP:
        return f"wikipedia-{name}.html"
    elif host == Host.ADB:
        return f"anidb-{name}.html"
    elif host == Host.IMDB:
        return f"imdb-{name}.html"
    elif host == Host.SOF:
        return f"stackoverflow-{name}.html"
    elif host == Host.MW:
        return f"merriamwebster-{name}.html"
    else:
        raise NotImplementedError

def getURLAndHostFromFileName(pagename: str):
    
    # Determine the weburl from the name
    webUrl = ""
    host = Host.UNK
    if pagename.startswith("wiki"): # wikipedia-title_of_article
        webUrl = f"{WIKI_HOST_URL}/wiki/{pagename[len('wikipedia-'):]}"
        host = Host.WP
    elif pagename.startswith("stackover"):  # stackoverflow-12345123-title-of-question-asdw
        pageidntitle = pagename[len('stackoverflow-'):]
        ii = pageidntitle.find('-')
        pageid = pageidntitle[:ii]
        pagetitle = pageidntitle[ii+1:]
        webUrl = f"{SOF_HOST_URL}/questions/{pageid}/{pagetitle}"
        host = Host.SOF
    elif pagename.startswith("merriam"):  # merriamwebster-title-of-page-asdw
        webUrl = f"{MEWE_HOST_URL}/dictionary/{pagename[len('merriamwebster-'):]}"
        host = Host.MW
    else:
        print(f"\tERROR! No way to determine url for page: \"{pagename}\".")
        raise NotImplementedError

    return webUrl, host

def isValidWikiLink(linkPath: str):
    #          only wiki articles            : denotes special articles        skip these pages
    return linkPath.startswith("/wiki/") and ':' not in linkPath and not linkPath.endswith("(identifier)") and not linkPath.endswith("(disambiguation)")

def isValidSOFLink(linkPath: str):
    return re.match(r"https:\/\/stackoverflow\.com\/questions\/\d+\/[\w\d-]+", linkPath) or re.match(r"\/questions\/\d+\/[\w\d-]+", linkPath)

def isValidMeWeLink(linkPath: str):
    return re.match(r"https:\/\/www\.merriam\-webster\.com\/dictionary\/[\d\w \%]+", linkPath) or re.match(r"\/dictionary\/[\d \w%]+", linkPath)

## ============== ##
## Beautiful Soup ##
## ============== ##

def getSoup(url: str, delay=3.0):
    """
        Gets a accessable datastructure for the given webpage. 
        Returns None on failure.
    """
    print(f"Making request from \"{url}\".")
    sleep(delay)    # Force a delay between downloads

    try:
        req = Request(url, headers={'User-Agent':USER_AGENT})
        html = urlopen(req).read()
        soup = BeautifulSoup(html, 'html.parser')
        return soup, html
    except HTTPError:
        print(f"HTTP connection was denied to '{url}'.")
    except:
        print(f"Unknown Error in accessing '{url}'.")

    return None, None

def getSoupLocal(addr: str):
    """
        Gets a accessable datastructure for the given local webpage. 
        Used for debugging.
        Returns None on failure.
    """

    fp = open(addr, mode='r', encoding='utf-8')
    soup = BeautifulSoup(fp.read(), 'html.parser')
    fp.close()

    return soup

def getLinksFromSoup(soup, host: Host):

    # Determine information based on host
    hostURL = ""
    if host == Host.WP:
        hostURL = WIKI_HOST_URL
        fLinkValid = isValidWikiLink
    elif host == Host.SOF:
        hostURL = SOF_HOST_URL
        fLinkValid = isValidSOFLink
    elif host == Host.MW:
        hostURL = MEWE_HOST_URL
        fLinkValid = isValidMeWeLink
    else: 
        raise NotImplementedError

    # Read the links from the soup
    # Build a set from the valid links
    links = soup.find_all('a')
    linkSet = set()
    for link in links:

        # Check for valid link
        linkPath = link.get("href")
        if linkPath and fLinkValid(linkPath):

            # Trim any ?arguments and #links and prepend the host
            linkPath = linkPath.split("?")[0]
            linkPath = linkPath.split("#")[0]
            linkPath = linkPath.replace(" ", "%20")

            # Preppend the hostURl if the link does not have it
            if not linkPath.startswith(hostURL): linkPath = hostURL + linkPath

            linkSet.add(linkPath)

    return linkSet
    