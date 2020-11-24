# ====================================================================
#
# Crawls through pages like wikipedia and downloads them locally
# Traverses in a randomized DFS search
# Requests limited to 1 page / 3 sec
# A little bit of a bodge -- Expect it to run for ~1hr at a time 
#                            then stop due to python recursion limits
#
import os
import argparse
from random import randint

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
        if html:
            with open(localPath, mode="wb") as fp:
                fp.write(html)
        else:
            return
    else:
        soup = getSoupLocal(localPath)
        if soup.head == None:   # Invalid HTML file save (happens if interupted during write)
            soup, html = getSoup(url, delay)
            if html:
                with open(localPath, mode="wb") as fp:
                    fp.write(html)
            else:
                return


    # Get all the links from the page
    # If the link is valid then recursively call this function
    linkSet = getLinksFromSoup(soup, host)

    noLinksFound = True
    for linkPath in linkSet:
        # Check to see if this is a new page
        pageName_i = getPageNameFromURL(linkPath, host)
        localPath_i = f"{localWebDir}/{getFileNameFromPageName(pageName_i, host)}"
        if not os.path.exists(localPath_i):
            noLinksFound = False
            webpageDFS(linkPath, host, localWebDir)

    # All links on this page have been visited, recurse at random then
    if noLinksFound:
        irand = randint(0, len(linkSet) - 1)
        webpageDFS(list(linkSet)[irand], host, localWebDir)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--siteCode", help="Website seed code", type=str, choices=["WP", "SOF", "MW"], required=True)
    parser.add_argument("-o", "--localWebDir", help="Directory to save html files", type=str, required=True)
    args = parser.parse_args()

    siteCode = args.siteCode
    localWebDir = args.localWebDir

    if siteCode == "WP":
        webpageDFS("https://en.wikipedia.org/wiki/Linear_algebra", Host.WP, localWebDir)
    elif siteCode == "SOF":
        webpageDFS("https://stackoverflow.com/questions/45380417/optimizing-a-webcrawl", Host.SOF, localWebDir)
    elif siteCode == "MW":
        webpageDFS("https://www.merriam-webster.com/dictionary/web%20crawler", Host.MW, localWebDir)
    