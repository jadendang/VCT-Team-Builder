import requests
import json
import gzip
import shutil
import os
from io import BytesIO
import time

S3_BUCKET_URL = "https://vcthackathon-data.s3.us-west-2.amazonaws.com"

LEAGUE = "game-changers"
YEAR = 2022

def download_gzip_and_write_to_json(file_name):
    if os.path.isfile(f"{file_name}.json"):
        return False

    remote_file = f"{S3_BUCKET_URL}/{file_name}.json.gz"
    retries = 3

    for attempt in range(retries):
        try:
            response = requests.get(remote_file, stream=True)

            if response.status_code == 200:
                gzip_bytes = BytesIO(response.content)
                with gzip.GzipFile(fileobj=gzip_bytes, mode="rb") as gzipped_file:
                    output_file_name = f"{file_name}.json"
                    with open(output_file_name, 'w', encoding='utf-8') as json_file:
                        json_data = json.load(gzipped_file)
                        json.dump(json_data, json_file, indent=4)
                    print(f"{output_file_name} written successfully.")
                return True
            elif response.status_code == 404:
                print(f"File {file_name} not found on server.")
                return False
            else:
                print(f"Failed to download {file_name}. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Download failed (attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return False
