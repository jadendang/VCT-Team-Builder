import sys
import os

sys.path.append(os.path.abspath('/Users/jadendang/Documents/GitHub/VCT-Team-Builder/project'))

from vlrdata.vlr_fetch import fetch_stats

if __name__ == "__main__":
    print(fetch_stats("your region", "your timespan"))