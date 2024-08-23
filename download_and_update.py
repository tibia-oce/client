import requests
import os
import zipfile
import tarfile
import shutil

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
    return asset_path, asset_name

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

def update_repository(extracted_path, repo_path):
    for item in os.listdir(extracted_path):
        s = os.path.join(extracted_path, item)
        d = os.path.join(repo_path, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    print("Repository files updated.")


if __name__ == "__main__":
    repo = "tibia-oce/otclient"  # Replace with your repo
    tag_name = "v0.0.1"  # Replace with the specific tag name or 'latest' for the latest release
    repo_path = "."  # Path to the current repository

    # Step 1: Download the release
    archive_path, asset_name = download_release(repo, tag_name)

    # Step 2: Extract the release
    extract_to = "/tmp/extracted_files"
    os.makedirs(extract_to, exist_ok=True)
    extract_archive(archive_path, extract_to)

    # Step 3: Update the repository files
    update_repository(extract_to, repo_path)
