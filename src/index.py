# ====================================================================
# Creates or updates a map of the connections from each page 
# to the rest of the pages
#
# Stored in JSON format, keyed by url
# {
#     url0: [url1, url14, url52, ...],
#     url1: [url1, url3, url22, ...],
#     ...
# }
#  
from time import time, sleep

import os
from htmlparse import Host, getSoupLocal, getLinksFromSoup, getURLAndHostFromFileName, WIKI_HOST_URL, SOF_HOST_URL, MEWE_HOST_URL
from json import dumps as json_dumps
from json import loads as json_loads

def updateWebIndex(htmlPages: list, index: dict):

    # Fill index for each url
    for htmlPage in htmlPages:

        # Filename will be the same in the index, only .json 
        if htmlPage.endswith(".html"):
            pagename = htmlPage[:-5]
            htmlPath = f"{localWebDir}/{htmlPage}"

            # Determine the weburl from the name
            url, host = getURLAndHostFromFileName(pagename)

            if url not in index.keys():
                print(f"[Index] Adding \"{htmlPage}\"") 

                # Get the links from the page
                soup = getSoupLocal(htmlPath)
                links = getLinksFromSoup(soup, host)
                index[url] = links

        else:
            print(f"Skipping non-html file: \"{htmlPage}\"")

    # Remove links that arent in the tiny-web
    urls = set(index.keys())
    for url in urls:
        index[url] = list(set(index[url]).intersection(urls))

if __name__ == "__main__":
    
    localWebDir = "tinyweb/"
    indexDir = "index/"
    indexPath = f"{indexDir}/index.json"
    pollingRate = 10

    # Initialize index (read off file is file is there)
    index = {}
    if os.path.exists(indexPath):
        with open(indexPath, mode='r') as fp:
            index = json_loads(fp.read())

    # Run every pollingRate seconds,
    # check for updates to the tinyweb
    # If new files present, update the index
    htmlPagesPrev = set()
    while True:
        print("[Index] Tick.")
        if os.path.exists(indexDir):
            if os.path.exists(localWebDir):

                # Check for changes 
                htmlPages = set(os.listdir(localWebDir))
                if 0 < len(htmlPages.intersection(htmlPagesPrev)):
                    print("[Index] Changes to web.")
                    updateWebIndex(htmlPages, index)

                # Save the index information 
                with open(indexPath, mode='w') as fp:
                    fp.write(json_dumps(index))

                htmlPagesPrev = htmlPages

                sleep(pollingRate)

            else:
                print(f"[Index]\tERROR! Cannot see local web directory: \"{localWebDir}\".")
                break
        else:
            print(f"[Index]\tERROR! Cannot reach output index/ directory: \"{localWebDir}\".")
            break
    