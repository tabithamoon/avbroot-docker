#!/usr/bin/python
from packaging.version import Version
from datetime import datetime
import subprocess
import requests
import shutil
import json
import sys
import os

def get_timestamp():
    return datetime.now().replace(microsecond=0).isoformat()

def log(message):
    print(f"[{get_timestamp()}] {message}")

def handle_exception(exception):
    log(e)
    sys.exit(1)

def download_file(url, path):
    response = requests.get(url, allow_redirects=True)

    if not response.ok:
        raise Exception("Failed to download file")

    with open(path, mode="wb") as file:
        file.write(response.content)

def get_lineageos_versions():
    try:
        response = requests.get("https://download.lineageos.org/api/v1/shiba/nightly/autodownloader")
        data = response.json()
    except:
        raise RuntimeError("Failed to get LineageOS versions.")

    data = data["response"]
    versions = []

    for release in data:
        versions.append({
            "timestamp": release["datetime"],
            "filename": release["filename"],
            "hash": release["id"],
            "url": release["url"]
        })

    return versions

def check_lineageos_update(versions):
    if not os.path.isfile("/publish/.version"):
        return versions[0]

    with open("/publish/.version") as file:
        current_version = file.read()
        file.close()

    if versions[0]["timestamp"] > int(current_version):
        return versions[0]
    else:
        return None

def update_lineageos(lineageos_version):
    log("Downloading LineageOS...")
    try:
        download_file(lineageos_version["url"], "/tmp/lineage-shiba.zip")
    except:
        raise RuntimeError("Failed to download LineageOS update.")

    log("Calculating checksum...")
    try:
        subprocess.run(
            "sha256sum /tmp/lineage-shiba.zip",
            capture_output=True,
            check=True,
            shell=True
        )
    except:
        raise RuntimeError("LineageOS update failed checksum.")

    log("Signing update...")
    try:
        subprocess.run(
            f"/usr/bin/avbroot ota patch --input /tmp/lineage-shiba.zip --key-avb /keys/avb.key --key-ota /keys/ota.key --cert-ota /keys/ota.crt --magisk-preinit-device=sda10 --magisk /opt/magisk.apk --clear-vbmeta-flags --output lineage-shiba-signed.zip",
            capture_output=True,
            cwd="/publish",
            shell=True,
            check=True
        )
    except:
        raise RuntimeError("Failed to sign LineageOS update.")

    with open("/publish/.version", "w+") as file:
        file.write(str(lineageos_update["timestamp"]))
        file.close()

    log("Generating OTA metadata...")
    try:
        subprocess.run(
            f"/usr/bin/custota-tool gen-csig --input lineage-shiba-signed.zip --key /keys/ota.key --cert /keys/ota.crt",
            capture_output=True,
            cwd="/publish",
            shell=True,
            check=True
        )
    except:
        raise RuntimeError("Failed to generate OTA metadata.")

    os.remove("/tmp/lineage-shiba.zip")
    log("LineageOS update ready.")

## Main logic
log("Update script has started.")
log("Checking for LineageOS updates...")

try:
    lineageos_versions = get_lineageos_versions()
    lineageos_update = check_lineageos_update(lineageos_versions)
except Exception as e:
    handle_exception(e)

if lineageos_update is None:
    log("No update available.")
else:
    try:
        log("Update available.")
        update_lineageos(lineageos_update)
    except Exception as e:
        handle_exception(e)

log("Finished.")
