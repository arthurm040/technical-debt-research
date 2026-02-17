import os
import re
from time import sleep

import requests
import subprocess
from pathlib import Path
import zipfile
import tarfile
import shutil

def parse_version(version):
    """Parse version string, extracting numeric parts and handling pre-release suffixes"""
    parts = []
    for part in version.split('.'):
        # Extract leading digits only
        match = re.match(r'(\d+)', part)
        parts.append(int(match.group(1)) if match else 0)
    return parts

def download_major_releases(package, output_dir="./library-versions"):
    output_dir = f"{output_dir}/{package}"
    Path(output_dir).mkdir(exist_ok=True, parents=True)

    # Fetch all versions from PyPI
    response = requests.get(f"https://pypi.org/pypi/{package}/json")
    releases = response.json()["releases"]

    # Group versions by major
    major_versions = {}
    for v in releases.keys():
        if not releases[v]:
            continue
        major = v.split('.')[0].split('-')[0]  # Handle X-a format
        major = re.match(r'(\d+)', major)
        if not major:
            continue
        major = major.group(1)
        if major not in major_versions:
            major_versions[major] = []
        major_versions[major].append(v)

    # Download and extract
    for major, versions in sorted(major_versions.items()):
        sorted_versions = sorted(versions, key=parse_version)

        success = False
        for version in sorted_versions:
            version_dir = Path(output_dir) / version
            version_dir.mkdir(exist_ok=True)

            result = subprocess.run([
                "pip", "download", f"{package}=={version}",
                "--dest", version_dir, "--no-deps",
                "--python-version", "3.12",
                "--platform", "any"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✓ Downloaded {version}")

                # Extract
                for file in version_dir.glob("*"):
                    if file.suffix == ".whl":
                        with zipfile.ZipFile(file, 'r') as zip_ref:
                            zip_ref.extractall(version_dir)
                        os.remove(file)
                    elif file.suffix in [".gz", ".bz2"]:
                        with tarfile.open(file, 'r:*') as tar_ref:
                            tar_ref.extractall(version_dir)
                        os.remove(file)

                # Remove .dist-info directories
                for dist_info in version_dir.glob("*.dist-info"):
                    shutil.rmtree(dist_info)

                success = True
                break
            else:
                shutil.rmtree(version_dir, ignore_errors=True)

        if not success:
            print(f"✗ No downloadable version found for major {major}")

targets = ["marshmallow",
           "pydantic", "click", "python-dateutil", "requests"
           ]

for target in targets:
    print(target)
    download_major_releases(target)
    sleep(5)
