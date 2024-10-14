import hashlib
import json
import os
import tarfile
import zipfile
from dataclasses import dataclass, field
from typing import Any

import requests


@dataclass
class FileInfo:
    localfile: str
    packedhash: str
    size: int
    url: str


@dataclass
class ModulesJSON:
    version: str | None = "1"
    files: list[FileInfo] = field(default_factory=list)


@dataclass
class DataJSON:
    version: str | None = "1"
    files: list[FileInfo] = field(default_factory=list)


@dataclass
class ModsJSON:
    version: str | None = "1"
    files: list[FileInfo] = field(default_factory=list)


@dataclass
class ClientJSON:
    version: str | None = "1"
    revision: int = 1
    executable: str | None = "otclient.exe"
    files: list[FileInfo] = field(default_factory=list)


@dataclass
class ReleaseAsset:
    name: str
    browser_download_url: str


def fetch_release_data(repo: str, tag_name: str) -> Any:
    # todo: create a data class for this response
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag_name}"

    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_release_asset(release_data: dict[str, Any]) -> ReleaseAsset:
    asset_data = release_data["assets"][0]
    return ReleaseAsset(
        name=asset_data["name"], browser_download_url=asset_data["browser_download_url"]
    )


def download_asset(asset: ReleaseAsset, download_dir: str = "./windows") -> str:
    os.makedirs(download_dir, exist_ok=True)
    response = requests.get(asset.browser_download_url, stream=True)
    response.raise_for_status()
    asset_path = os.path.join(download_dir, asset.name)
    with open(asset_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"{asset.name} downloaded successfully to {asset_path}.")
    return asset_path


def extract_archive(archive_path: str, extract_to: str) -> None:
    os.makedirs(extract_to, exist_ok=True)
    if archive_path.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
    elif archive_path.endswith((".tar.gz", ".tgz")):
        with tarfile.open(archive_path, "r:gz") as tar_ref:
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


def gather_files_info(
    repo_path: str,
) -> dict[str, ModulesJSON | DataJSON | ModsJSON | ClientJSON]:
    files_info: dict[str, ModulesJSON | DataJSON | ModsJSON | ClientJSON] = {
        "modules": ModulesJSON(),
        "data": DataJSON(),
        "mods": ModsJSON(),
        "client": ClientJSON(),
    }

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.startswith(".") or file.endswith(".md"):
                continue

            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, repo_path)
            normalized_path = os.path.normpath(relative_path)
            
            # serverSIDE directories are for features still in dev
            if file.endswith(".zip") or "serverSIDE" in normalized_path:
                continue

            file_info = FileInfo(
                localfile=relative_path.replace(os.path.sep, "/"),
                packedhash=calculate_sha256(file_path),
                size=os.path.getsize(file_path),
                url=relative_path.replace(os.path.sep, "/"),
            )

            if "modules" in normalized_path:
                files_info["modules"].files.append(file_info)
            elif "data" in normalized_path:
                files_info["data"].files.append(file_info)
            elif "mods" in normalized_path:
                files_info["mods"].files.append(file_info)
            elif isinstance(files_info["client"], ClientJSON):
                files_info["client"].files.append(file_info)
                if file.endswith(".exe"):
                    files_info["client"].executable = relative_path.replace(
                        os.path.sep, "/"
                    )

    return files_info


def write_json_files(
    files_info: dict[str, ModulesJSON | DataJSON | ModsJSON | ClientJSON],
    windows_path: str,
) -> None:
    os.makedirs(windows_path, exist_ok=True)

    for key, json_file in files_info.items():
        json_path = os.path.join(windows_path, f"{key}.windows.json")
        with open(json_path, "w") as file:
            json.dump(
                json_file.__dict__,
                file,
                default=lambda o: o.__dict__ if isinstance(o, FileInfo) else o,
                indent=4,
            )
        print(f"{key}.windows.json created successfully at {json_path}")


def main(repo: str, tag_name: str, repo_path: str) -> None:
    windows_path = os.path.join(repo_path, "windows")
    os.makedirs(windows_path, exist_ok=True)

    release_data = fetch_release_data(repo, tag_name)
    asset = get_release_asset(release_data)
    archive_path = download_asset(asset, download_dir=windows_path)
    extract_archive(archive_path, extract_to=windows_path)

    files_info = gather_files_info(windows_path)
    write_json_files(files_info, windows_path)

    if os.path.exists(archive_path):
        os.remove(archive_path)
        print(f"Removed archive: {archive_path}")
