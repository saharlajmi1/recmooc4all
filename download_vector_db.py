# download_vector_db.py
import gdown
import zipfile
import os

# Replace with your actual file ID
file_id = "1LSqIVnBs5zeqE78XizgzQVuBtdv6hdf0"
url = f"https://drive.google.com/uc?id={file_id}"
output_zip = "vector_db.zip"
target_folder = "app/vector_db"

# Create target folder if it doesn't exist
os.makedirs(target_folder, exist_ok=True)

# Download the zip
print("⬇️ Downloading vector_db.zip...")
gdown.download(url, output_zip, quiet=False)

print(zipfile.is_zipfile(output_zip))

# Extract into the target folder
print("📦 Extracting files...")
with zipfile.ZipFile(output_zip, 'r') as zip_ref:
    zip_ref.extractall(target_folder)

# Optionally remove the zip
os.remove(output_zip)
print("✅ vector_db is ready.")
