import os
import json
import requests
import hashlib
import tarfile
import zipfile
from dataclasses import dataclass, field
from typing import List, Dict, Union

@dataclass
class FileInfo:
    localfile: str
    packedhash: str
    size: int
    url: str

@dataclass
class ModulesJSON:
    version: Union[str, None] = "1"
    files: List[FileInfo] = field(default_factory=list)

@dataclass
class DataJSON:
    version: Union[str, None] = "1"
    files: List[FileInfo] = field(default_factory=list)

@dataclass
class ModsJSON:
    version: Union[str, None] = "1"
    files: List[FileInfo] = field(default_factory=list)

@dataclass
class ClientJSON:
    version: Union[str, None] = "1"
    revision: int = 1
    executable: Union[str, None] = "otclient.exe"
    files: List[FileInfo] = field(default_factory=list)

@dataclass
class ReleaseAsset:
    name: str
    browser_download_url: str

def fetch_release_data(repo: str, tag_name: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag_name}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_release_asset(release_data: dict) -> ReleaseAsset:
    asset_data = release_data['assets'][0]
    return ReleaseAsset(name=asset_data['name'], browser_download_url=asset_data['browser_download_url'])

def download_asset(asset: ReleaseAsset, download_dir: str = "/tmp") -> str:
    response = requests.get(asset.browser_download_url, stream=True)
    response.raise_for_status()
    asset_path = os.path.join(download_dir, asset.name)
    with open(asset_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"{asset.name} downloaded successfully.")
    return asset_path

def extract_archive(archive_path: str, extract_to: str) -> None:
    if archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    elif archive_path.endswith(('.tar.gz', '.tgz')):
        with tarfile.open(archive_path, 'r:gz') as tar_ref:
            tar_ref.extractall(extract_to)
    else:
        raise ValueError("Unsupported archive format")
    print(f"Extracted {archive_path} to {extract_to}")

def calculate_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def gather_files_info(repo_path: str) -> Dict[str, Union[ModulesJSON, DataJSON, ModsJSON, ClientJSON]]:
    files_info = {
        "modules": ModulesJSON(),
        "data": DataJSON(),
        "mods": ModsJSON(),
        "client": ClientJSON()
    }

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.startswith('.') or file.endswith('.md'):
                continue

            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, repo_path)
            normalized_path = os.path.normpath(relative_path)
            path_parts = normalized_path.split(os.path.sep)

            if any(part.startswith('.') for part in path_parts):
                continue

            file_info = FileInfo(
                localfile=relative_path.replace(os.path.sep, '/'),
                packedhash=calculate_sha256(file_path),
                size=os.path.getsize(file_path),
                url=relative_path.replace(os.path.sep, '/')
            )

            if 'modules' in path_parts:
                files_info["modules"].files.append(file_info)
            elif 'data' in path_parts:
                files_info["data"].files.append(file_info)
            elif 'mods' in path_parts:
                files_info["mods"].files.append(file_info)
            else:
                files_info["client"].files.append(file_info)
                if file.endswith('.exe'):
                    files_info["client"].executable = relative_path.replace(os.path.sep, '/')

    return files_info

def write_json_files(files_info: Dict[str, Union[ModulesJSON, DataJSON, ModsJSON, ClientJSON]], repo_path: str) -> None:
    for key, json_file in files_info.items():
        json_path = os.path.join(repo_path, f"{key}.windows.json")
        with open(json_path, 'w') as file:
            json.dump(
                json_file.__dict__,
                file,
                default=lambda o: o.__dict__ if isinstance(o, FileInfo) else o,
                indent=4
            )
        print(f"{key}.windows.json created successfully at {json_path}")

def main(repo: str, tag_name: str, repo_path: str) -> None:
    release_data = fetch_release_data(repo, tag_name)
    asset = get_release_asset(release_data)
    archive_path = download_asset(asset)
    extract_archive(archive_path, repo_path)
    files_info = gather_files_info(repo_path)
    write_json_files(files_info, repo_path)