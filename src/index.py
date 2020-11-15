# ====================================================================
#
# Builds an index based on our local mini-web
# This index will be a directory of JSONs
# Each JSON will represent a website and contain
#   - URL to the website
#   - URLs that the website links to in a list
#   - Term frequency of each word in the <title>
#   - Term frequency of each word in the <h*>
#   - Term frequency of each word in the <p>
#   - Number of terms in *title*
#   - Number of terms in *headers*
#   - Number of terms in *p-tags*
#
# NOTE: All terms stored will be lemmatized
# 
from nltk import download as nltk_download
from nltk import RegexpTokenizer
from nltk.stem import WordNetLemmatizer
from nltk.data import load
from nltk.tokenize.destructive import NLTKWordTokenizer
from time import time

import os
from htmlparse import Host, getSoupLocal, getLinksFromSoup, WIKI_HOST_URL, SOF_HOST_URL
from json import dumps as json_dumps

## === ##
#  NLP  #
## === ##

# Language models needed
nltk_download('wordnet')
_lemmatizer = WordNetLemmatizer()
_tokenizer = RegexpTokenizer(r"\w+|\d+")

def tokenize(text: str):
    return _tokenizer.tokenize(text)

def lemmatize(word: str):
    return _lemmatizer.lemmatize(word)

def getLemmas(text: str):
    return [lemmatize(word) for word in tokenize(text)]

def getTermFreq(text: str, tfExt=None):

    lemmas = getLemmas(text)

    tf = tfExt if tfExt else {}
    for lemma in lemmas:
        if lemma in tf.keys():
            tf[lemma] += 1
        else:
            tf[lemma] = 1

    return tf

## ==== ##
#  Misc  #
## ==== ##

def generateIndexFromPage(htmlPath: str, webUrl: str, host: Host):

    soup = getSoupLocal(htmlPath)

    # Determine the links on the page
    # Convert to a list for the JSON
    links = list(getLinksFromSoup(soup, host))

    # Title term freq
    title = soup.title.string if soup.title else ""
    titleTF = getTermFreq(title)

    headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    headerTF = {}
    for header in headers:
        if header.text:
            headerTF = getTermFreq(header.text, headerTF)

    texts = soup.find_all('p')
    textTF = {}
    for text in texts:
        if text.text:
            textTF = getTermFreq(text.text, textTF)

    numTitleLemmas = 0
    for count in titleTF.values():
        numTitleLemmas += count
    numHeaderLemmas = 0
    for count in headerTF.values():
        numHeaderLemmas += count
    numTextLemmas = 0
    for count in textTF.values():
        numTextLemmas += count

    # Compile  and return the index JSON
    index = {
        "url": webUrl,
        "links": links,
        "title-tf": titleTF,
        "header-tf": headerTF,
        "text-tf": textTF,
        "numTitleLemmas": numTitleLemmas,
        "numHeaderLemmas": numHeaderLemmas,
        "numTextLemmas": numTextLemmas,
    }

    return index

if __name__ == "__main__":
    
    localWebDir = "tinyweb/"
    indexDir = "index/"

    # Make the index directory if this is the first time
    if not os.path.exists(indexDir): os.makedirs(indexDir)
    
    # Loop through the local web pages
    # If the page does not have an index file, then make one, and save it
    if os.path.exists(localWebDir):
        htmlPages = os.listdir(localWebDir)
        numPages = len(htmlPages)
        if 0 < len(htmlPages):
            for n, htmlPage in enumerate(htmlPages):
                print(f"({n+1}/{numPages}) {htmlPage}")

                # Filename will be the same in the index, only .json 
                if htmlPage.endswith(".html"):
                    pagename = htmlPage[:-5]
                    htmlPath = f"{localWebDir}/{htmlPage}"
                    jsonPath = f"{indexDir}/{pagename}.json"

                    # Determine the weburl from the name
                    webUrl = ""
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
                    else:
                        print(f"\tERROR! No way to determine url for page: \"{pagename}\".")
                        raise NotImplementedError

                    # If the index file is missing or is empty generate one
                    if not os.path.exists(jsonPath):
                        pageIndex = generateIndexFromPage(htmlPath, webUrl, host)

                        # Save the index information 
                        with open(jsonPath, mode='w') as fp:
                            fp.write(json_dumps(pageIndex))
                    
                else:
                    print(f"Skipping non-html file: \"{htmlPage}\"")

        else:
            print(f"\tWarning! Local web directory: \"{localWebDir}\" is empty.")

    else:
        print(f"\tERROR! Cannot see local web directory: \"{localWebDir}\".")
    