# ====================================================================
# Computes and stores term frequency information for each page
#
# NOTE: All terms stored will be lemmatized
# 
from nltk import download as nltk_download
from nltk import RegexpTokenizer
from nltk.stem import WordNetLemmatizer
from nltk.data import load
from nltk.tokenize.destructive import NLTKWordTokenizer
from time import time, sleep

import os
from htmlparse import Host, getSoupLocal, getLinksFromSoup, getURLAndHostFromFileName, WIKI_HOST_URL, SOF_HOST_URL, MEWE_HOST_URL
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

def generateTermFreqFromPage(htmlPath: str, webUrl: str, host: Host):

    soup = getSoupLocal(htmlPath)

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
        "title-tf": titleTF,
        "header-tf": headerTF,
        "text-tf": textTF,
        "numTitleLemmas": numTitleLemmas,
        "numHeaderLemmas": numHeaderLemmas,
        "numTextLemmas": numTextLemmas,
    }

    return index

def updateTermFreqCache(htmlPages: list, localWebDir: str, termFreqDir: str):

    if 0 < len(htmlPages):
        for htmlPage in htmlPages:

            # Filename will be the same in the index, only .json 
            if htmlPage.endswith(".html"):
                pagename = htmlPage[:-5]
                htmlPath = f"{localWebDir}/{htmlPage}"
                jsonPath = f"{termFreqDir}/{pagename}.json"

                # Determine the weburl from the name
                webUrl, host = getURLAndHostFromFileName(pagename)

                # If the index file is missing or is empty generate one
                if not os.path.exists(jsonPath):
                    print(f"[NLP] Adding \"{htmlPage}\"")
                    pageIndex = generateTermFreqFromPage(htmlPath, webUrl, host)

                    # Save the index information 
                    with open(jsonPath, mode='w') as fp:
                        fp.write(json_dumps(pageIndex))
                
            else:
                print(f"Skipping non-html file: \"{htmlPage}\"")

    else:
        print(f"\tWarning! Local web directory: \"{localWebDir}\" is empty.")
    

if __name__ == "__main__":
    
    localWebDir = "tinyweb/"
    termFreqDir = "term-freq/"
    pollingRate = 10

    htmlPagesPrev = set()
    while True:
        print("[NLP] Tick.")
        if os.path.exists(termFreqDir):
            if os.path.exists(localWebDir):

                # Check for changes 
                htmlPages = set(os.listdir(localWebDir))
                if 0 < len(htmlPages.intersection(htmlPagesPrev)):
                    print("[NLP] Changes to web.")
                    updateTermFreqCache(htmlPages, localWebDir, termFreqDir)

                htmlPagesPrev = htmlPages

                sleep(pollingRate)

            else:
                print(f"[NLP]\tERROR! Cannot see local web directory: \"{localWebDir}\".")
                break
        else:
            print(f"[NLP]\tERROR! Cannot reach output termFreq directory: \"{localWebDir}\".")
            break
    