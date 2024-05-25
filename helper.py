import os
import re

import requests
from bs4 import BeautifulSoup


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            return value
    return None


def find(val, text, offset):
    soup = BeautifulSoup(text, "lxml")
    match = soup.find_all(val)
    if match:
        return match[offset].text
    return ""


def get_content_len(response, val=0):
    headers = response.headers
    val = float(headers.get("Content-Length", 0))
    if not val:
        val = find("span", response.text, -1)
        if val:
            size = val.split()[-1][1:-1]
            if "M" in size:
                val = float(size[:-1]) * 10**6
            elif "G" in size:
                val = float(size[:-1]) * 10**9
    return val


def get_gdrive_name(response):
    head = response.headers
    rule = re.compile(r'filename="(.*)"')
    match = rule.search(head.get("Content-Disposition", ""))
    if match:
        return match.group(1)
    return find("a", response.text, -4)


def gdrive_size_bypass(response):
    soup = BeautifulSoup(response.text, "lxml")
    inputs = soup.find_all("input")
    return {i["name"]: i["value"] for i in inputs if i["type"] == "hidden"}


def gdown(url, path, enable=False):
    baseurl = "https://drive.usercontent.google.com/download"
    fileid = url.split("id=")[1]
    params = {"id": fileid}
    session = requests.session()
    response = session.get(baseurl, params=params, stream=True)
    if response.headers["Content-Type"] != "application/octet-stream":
        params.update(gdrive_size_bypass(response))
        response = session.get(baseurl, params=params, stream=True)

    tokens = get_confirm_token(response)
    filename = get_gdrive_name(response)
    filesize = get_content_len(response)

    if tokens:
        params.update(dict(confirm=tokens))
    path = os.path.join(path, filename)
    if not os.path.exists(path) or enable:
        respons = session.get(baseurl, params=params, stream=True)
        download(respons, path)
        # if os.path.exists(path):
        #   print('success')
    return filename, filesize


def download(response, path):
    if response.status_code == 200:
        with open(path, "wb") as f:
            for chunk in response.iter_content(512 * 1024):
                if chunk:
                    f.write(chunk)


gdown(
    "https://drive.google.com/uc?export=download&id=1-XTk3j9UbU0wlVoFJYvfWS0mZvXnC719",
    "./",
)
