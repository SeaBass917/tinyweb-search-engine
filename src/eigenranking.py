# ====================================================================
# Computes an eigenranking for all the pages in the index
#
# NOTE: Eigenranking format sorted tab seperated list file
#   0.0123  https://...
#   0.0091  https://...
#   0.0090  https://...
#   0.0087  https://...
# 
from json import loads as json_loads
from scipy.sparse import dok_matrix
import numpy as np
import os
from time import time

def determineEigenRankings(indexPath: str):
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
    
    eigenRankings = []

    # =============================
    # Step 1) Read Index Directory
    # =============================
    print("Reading The Index...")

    # Load up the index and check that its non-empty
    if os.path.exists(indexPath):
        index = {}
        with open(indexPath, mode='r') as fp:
            index = json_loads(fp.read())
        if 0 < len(index.keys()):

            # ===============================
            # Step 2) Populate spares matrix
            # ===============================
            print("Populating Sparse Matrix...")
            
            urls = index.keys()
            numPages = len(urls)

            ## DEV STUFF
            # Show stats on the links
            l_min = 2**32 - 1
            l_max = 0
            l_avg = 0
            for url in urls:
                l = len(index[url])
                l_min = min(l_min, l)
                l_max = max(l_max, l)
                l_avg += l
            
            print("Stats on links in the mini-web:")
            print(f"\tmin: {l_min}")
            print(f"\tmax: {l_max}")
            print(f"\tavg: {l_avg / numPages}\n")

            # Create maps to manage the index to url relationship
            enumLookup = {url: i for i, url in enumerate(urls)}
            urlLookup =  {i: url for i, url in enumerate(urls)}

            # Populate the sparse matrix with a uniform probability of going to each page
            matSparse = dok_matrix((numPages, numPages), dtype=np.float64)
            for url, links in index.items():
                i = enumLookup[url]
                n = len(links)
                p = 1.0 / n if 0 < n else 0.0
                for link in links:
                    j = enumLookup[link]
                    matSparse[j, i] = p

            # ==============================
            # Step 3) Determine Eigenvector
            # ==============================
            print("Determining eigenvector...")

            # Initialize a uniform probability vector
            p = 1.0 / numPages
            v = np.ones((numPages, 1), dtype=np.float64) * p
            
            # Run the vector through enough cycles until convergence on eigenvector
            epsilon = 1.0
            n = 0
            t0 = time()
            while 1e-6 < epsilon and n < 100000:
                if n%1000 == 0: print(f"n={n}, epsilon={round(epsilon, 7)}")
                vnew = matSparse * v

                # check difference between vectors for convergence
                epsilon = 0
                for i in range(numPages):
                    epsilon += abs(v[i][0] - vnew[i][0])
                    
                v = vnew
                n+=1

            t1 = time()
            print(f"Time elapsed: {t1-t0}")

            ## DEV STUFF
            # Check that v is an eigenvector that sums to 1
            s = 0
            for p in v:
                s += p[0]   # NOTE: Nx1 matrix
            print(f"\tEpsilon: {epsilon}. Eigenvector sums to {s}")

            # ==================
            # Step 4) Rank Urls
            # ==================
            print("Ranking Pages...")

            # Tuple the probabilties with the urls
            eigenRankings = [(p[0], urlLookup[i]) for i, p in enumerate(vnew)]
            eigenRankings.sort(key=lambda x: x[0], reverse=True)

    return eigenRankings

if __name__ == "__main__":

    indexPath = "index/index.json"
    eigenRankPath = "index/eigenranking.txt"
    
    # Get the eigenrankings
    if os.path.exists(indexPath):
        eRanks = determineEigenRankings(indexPath)

        # Print out to file
        sOut = ""
        for p, url in eRanks:
            sOut += f"{p}\t{url}\n"
        sOut = sOut[:-1]
        with open(eigenRankPath, mode="w") as fp:
            fp.write(sOut)

    else:
        print(f"\tERROR! Cannot see local index path: \"{indexPath}\".")
