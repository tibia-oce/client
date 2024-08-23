import requests
import os
import zipfile
import tarfile

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

if __name__ == "__main__":
    repo = "tibia-oce/otclient"  # Replace with your repo
    tag_name = "v0.0.1"  # Replace with the specific tag name or 'latest' for the latest release
    repo_path = "."  # Path to the current repository
    archive_path = download_release(repo, tag_name)
    extract_archive(archive_path, repo_path)
