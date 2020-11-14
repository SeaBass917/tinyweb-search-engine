# ====================================================================
#
# Crawls through pages like wikipedia and downloads them locally
# Traverses in a randomized DFS search
# Requests limited to 1 page / 3 sec
# A little bit of a bodge -- Expect it to run for ~1hr at a time 
#                            then stop due to python recursion limits
#
import os

from htmlparse import Host, getSoup, getSoupLocal, getLinksFromSoup, getPageNameFromURL, getFileNameFromPageName

def webpageDFS(url: str, host: Host, localWebDir: str, delay=3.0):
    """
        DFS on the host website

        url        - Full url to page: (e.g. "https://en.wikipedia.org/wiki/Linear_algebra")
        host       - Enum to indicate where the page is hosted (e.g. Host.WP <-> wikipedia)
        localWebDir   - Directory for caching the webpage
        fValidLink - function that dictates what is considered a valid link on this page
        delay      - Minimum time between each request from the host
    """

    pageName = getPageNameFromURL(url, host)

    # Make sure the output directory is there
    if not os.path.exists(localWebDir): os.makedirs(localWebDir)
        
    # Only run if the page is not on file
    localPath = f"{localWebDir}/{getFileNameFromPageName(pageName, host)}"
    if not os.path.exists(localPath): 
        soup, html = getSoup(url, delay)
        with open(localPath, mode="wb") as fp:
            fp.write(html)
    else:
        soup = getSoupLocal(localPath)
        if soup.head == None:   # Invalid HTML file save (happens if interupted during write)
            soup, html = getSoup(url, delay)
            with open(localPath, mode="wb") as fp:
                fp.write(html)


    # Get all the links from the page
    # If the link is valid then recursively call this function
    linkSet = getLinksFromSoup(soup, host)

    for linkPath in linkSet:
        # Check to see if this is a new page
        pageName_i = getPageNameFromURL(linkPath, host)
        localPath_i = f"{localWebDir}/{getFileNameFromPageName(pageName_i, host)}"
        if not os.path.exists(localPath_i):
            webpageDFS(linkPath, host, localWebDir)

if __name__ == "__main__":
    
    host = "https://en.wikipedia.org"
    seedURL = "https://en.wikipedia.org/wiki/Linear_algebra"
    localWebDir = "tinyweb/"

    webpageDFS(seedURL, Host.WP, localWebDir)