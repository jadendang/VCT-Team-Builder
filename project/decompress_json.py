import gzip
import json
import os

# Step 1: Specify the correct directory containing your .json.gz files
folder_path = "/Users/shadmanshahzahan/Downloads/VCT/VCT-Team-Builder/project/esports-data"

if not os.path.exists(folder_path):
    print(f"Error: Directory {folder_path} does not exist.")
    exit(1)
    
# Step 2: Loop through all files in the directory
for file_name in os.listdir(folder_path):
    if file_name.endswith(".json.gz"):
        file_path = os.path.join(folder_path, file_name)

        # Decompress the file
        with gzip.open(file_path, 'rt', encoding='utf-8') as gzipped_file:
            data = json.load(gzipped_file)

        # Save the decompressed JSON to a new file
        output_file_path = file_path[:-3]  # Remove the .gz extension
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4)

        print(f"Decompressed data saved to {output_file_path}")




