import sys
import os

sys.path.append(os.path.abspath('/Users/jadendang/Documents/GitHub/VCT-Team-Builder/project'))

from vlrdata.vlr_fetch import fetch_stats

if __name__ == "__main__":
    try:
        stats = fetch_stats("na", "60")
        print(stats)
    except Exception as e:
        print(f"Error fetching stats: {e}")