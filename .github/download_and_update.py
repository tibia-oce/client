import requests
import os
import zipfile
import tarfile
import hashlib
import json

def download_release(repo, tag_name):
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag_name}"
    response = requests.get(url)
    response.raise_for_status()
    release_data = response.json()
    
    # Get the asset URL (assuming you want the first asset)
    asset_url = release_data['assets'][0]['browser_download_url']
    asset_name = release_data['assets'][0]['name']
    
    # Download the asset
    download_response = requests.get(asset_url, stream=True)
    download_response.raise_for_status()

    # Save the file
    asset_path = os.path.join("/tmp", asset_name)
    with open(asset_path, 'wb') as f:
        for chunk in download_response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"{asset_name} downloaded successfully.")
    return asset_path

def extract_archive(archive_path, extract_to):
    if archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
        with tarfile.open(archive_path, 'r:gz') as tar_ref:
            tar_ref.extractall(extract_to)
    else:
        raise ValueError("Unsupported archive format")
    print(f"Extracted {archive_path} to {extract_to}")

def calculate_sha256(file_path):
    """Calculate the SHA-256 hash of the file contents."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_json_files(repo_path):
    modules = []
    data_files = []
    mod_files = []
    client_files = []  # Files that don't fit into modules, data, or mods

    for root, dirs, files in os.walk(repo_path):
        for file in files:
            # Skip files that are .md files or that start with a '.'
            if file.startswith('.') or file.endswith('.md'):
                continue

            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, repo_path)
            normalized_path = os.path.normpath(relative_path)
            path_parts = normalized_path.split(os.path.sep)

            # Skip directories that start with a '.'
            if any(part.startswith('.') for part in path_parts):
                continue

            packedhash = calculate_sha256(file_path)
            size = os.path.getsize(file_path)
            url = relative_path.replace(os.path.sep, '/')

            file_info = {
                "localfile": relative_path.replace(os.path.sep, '/'),
                "packedhash": packedhash,
                "size": size,
                "url": url
            }

            # Append to the appropriate list based on the directory
            if 'modules' in path_parts:
                modules.append(file_info)
            elif 'data' in path_parts:
                data_files.append(file_info)
            elif 'mods' in path_parts:
                mod_files.append(file_info)
            else:
                client_files.append(file_info)  # Any other files go here

    # Write modules.json
    if modules:
        modules_json_path = os.path.join(repo_path, 'modules.json')
        with open(modules_json_path, 'w') as json_file:
            json.dump({"files": modules}, json_file, indent=4)
        print(f"modules.json created successfully at {modules_json_path}")

    # Write data.json
    if data_files:
        data_json_path = os.path.join(repo_path, 'data.json')
        with open(data_json_path, 'w') as json_file:
            json.dump({"files": data_files}, json_file, indent=4)
        print(f"data.json created successfully at {data_json_path}")

    # Write mods.json
    if mod_files:
        mods_json_path = os.path.join(repo_path, 'mods.json')
        with open(mods_json_path, 'w') as json_file:
            json.dump({"files": mod_files}, json_file, indent=4)
        print(f"mods.json created successfully at {mods_json_path}")

    # Write client.json for all other files
    if client_files:
        client_json_path = os.path.join(repo_path, 'client.json')
        with open(client_json_path, 'w') as json_file:
            json.dump({"files": client_files}, json_file, indent=4)
        print(f"client.json created successfully at {client_json_path}")

if __name__ == "__main__":
    repo = "tibia-oce/otclient"  # Replace with your repo
    tag_name = "v0.0.1"  # Replace with the specific tag name or 'latest' for the latest release
    repo_path = "."  # Path to the current repository

    # Step 1: Download the release
    archive_path = download_release(repo, tag_name)

    # Step 2: Extract the release
    extract_archive(archive_path, repo_path)

    # Step 3: Create JSON files in the top-level directory
    create_json_files(repo_path)
