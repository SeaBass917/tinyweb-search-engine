from json import loads as json_loads
from scipy.sparse import dok_matrix
# from scipy.sparse.linalg import eigs
import numpy as np
import os

def determineEigenRankings(indexDir: str):
    """
        Returns a sorted list of tuples (probability, url)
        [
            (0.01, "https://en.wikipedia.org/wiki/The_Mouse%27s_Tale"),
            (0.006, "https://en.wikipedia.org/wiki/Anthology_of_Planudes"),
            ...
            (p, url)
        ]

        :param indexDir: Path to the directory of the web index
    """
    
    # =============================
    # Step 1) Read Index Directory
    # =============================

    # Loop through the index files and build a map
    # url -> links
    linkMap = {}
    for indexfilename in os.listdir(indexDir):
        if indexfilename.endswith(".json"):
            indexPath = f"{indexDir}/{indexfilename}"

            # Read the index json
            index = {}
            with open(indexPath) as fp:
                index = json_loads(fp.read())

            # Check that all required fields are present
            keys = index.keys()
            if "url" in keys and "links" in keys:

                url = index["url"]
                links = index["links"]

                linkMap[url] = links

            else:
                print(f"\tError! Index \"{index}\" is inncomplete, could not include page in ranking.")

        else:
            print(f"\tSkipping non-json file \"{index}\" in index.")
    
    # ===============================
    # Step 2) Populate spares matrix
    # ===============================

    # Trim off the links we dont have in our index
    keyset = set(linkMap.keys())
    numPages = len(keyset)
    for url in keyset:
        linkMap[url] = set(linkMap[url]).intersection(keyset)
    
    ## DEV STUFF
    # Show stats on the links
    l_min = 2**32 - 1
    l_max = 0
    l_avg = 0
    nnn = 0
    for url in keyset:
        l = len(linkMap[url])
        l_min = min(l_min, l)
        l_max = max(l_max, l)
        l_avg += l
    
    print("Stats on links in the mini-web:")
    print(f"\tmin: {l_min}")
    print(f"\tmax: {l_max}")
    print(f"\tavg: {l_avg / numPages}\n")

    # Convert the urls to indices in the matrix
    enumLookup = {url: i for i, url in enumerate(keyset)}

    # Populate the sparse matrix with a uniform probability of going to each page
    matSparse = dok_matrix((numPages, numPages), dtype=np.float64)
    for url, links in linkMap.items():
        i = enumLookup[url]
        p = 1.0 / len(links)
        for link in links:
            j = enumLookup[link]
            matSparse[j, i] = p

    # ==============================
    # Step 3) Determine Eigenvector
    # ==============================

    # Initialize a uniform probability vector
    p = 1.0 / numPages
    v = np.ones((numPages, 1), dtype=np.float64) * p
    
    # Run the vector through enough cycles until convergence on eigenvector
    epsilon = 1.0
    n = 0
    while 1e-6 < epsilon and n < 20000:
        vnew = matSparse * v

        # check difference between vectors for convergence
        epsilon = 0
        for i in range(numPages):
            epsilon += abs(v[i][0] - vnew[i][0])
            
        v = vnew
        n+=1

    ## DEV STUFF
    # Check that v is an eigenvector that sums to 1
    s = 0
    for p in v:
        s += p[0]
    print(f"\tEigenvector sums to {s}")

    # ==================
    # Step 4) Rank Urls
    # ==================

    # Create an inverse map
    urlLookup = {i: url for url, i in enumLookup.items()}

    # Tuple the probabilties with the urls
    eigenRankings = [(p[0], urlLookup[i]) for i, p in enumerate(vnew)]
    eigenRankings.sort(key=lambda x: x[0], reverse=True)

    return eigenRankings

if __name__ == "__main__":

    indexDir = "index/"
    eigenRankPath = "eigenranking.txt"
    
    if os.path.exists(indexDir):
        eRanks = determineEigenRankings(indexDir)

        sOut = ""
        for p, url in eRanks:
            sOut += f"{p}\t{url}\n"
        sOut = sOut[:-1]
        with open(eigenRankPath, mode="w") as fp:
            fp.write(sOut)

    else:
        print(f"\tERROR! Cannot see local index directory: \"{indexDir}\".")
