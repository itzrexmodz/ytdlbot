#!/usr/local/bin/python3
# coding: utf-8

# ytdlbot - sp_downloader.py
# 3/16/24 16:32
#

__author__ = "SanujaNS <sanujas@sanuja.biz>"

import logging
import pathlib
import re
import traceback
from urllib.parse import urlparse

import filetype
import requests
import yt_dlp as ytdl

from config import (
    IPv6,
)

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.128 Safari/537.36"


def sp_dl(url: str, tempdir: str):
    """Specific link downloader"""
    domain = urlparse(url).hostname
    domain_to_function = {
        "www.instagram.com": instagram,
        "pixeldrain.com": pixeldrain,
        "krakenfiles.com": krakenfiles,
    }
    for domain_key, function in domain_to_function.items():
        if domain_key in domain:
            return function(url, tempdir)
    
    return False


def sp_ytdl_download(url: str, tempdir: str):
    output = pathlib.Path(tempdir, "%(title).70s.%(ext)s").as_posix()
    ydl_opts = {
        "outtmpl": output,
        "restrictfilenames": False,
        "quiet": True,
        "format": None,
    }

    address = ["::", "0.0.0.0"] if IPv6 else [None]
    error = None
    video_paths = None
    for addr in address:
        ydl_opts["source_address"] = addr
        try:
            logging.info("Downloading %s", url)
            with ytdl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            video_paths = list(pathlib.Path(tempdir).glob("*"))
            break
        except Exception:
            error = traceback.format_exc()
            logging.error("Download failed for %s - %s", url)

    if not video_paths:
        raise Exception(error)

    return video_paths


def instagram(url: str, tempdir: str):
    resp = requests.get(f"http://192.168.6.1:15000/?url={url}").json()
    if url_results := resp.get("data"):
        for link in url_results:
            content = requests.get(link, stream=True).content
            ext = filetype.guess_extension(content)
            save_path = pathlib.Path(tempdir, f"{id(link)}.{ext}")
            with open(save_path, "wb") as f:
                f.write(content)

        return True


def pixeldrain(url: str, tempdir: str):
    user_page_url_regex = r"https://pixeldrain.com/u/(\w+)"
    match = re.match(user_page_url_regex, url)
    if match:
        url = "https://pixeldrain.com/api/file/{}?download".format(match.group(1))
        return sp_ytdl_download(url, tempdir)
    else:
        return url


def krakenfiles(url: str, tempdir: str):
    resp = requests.get(url)
    html = resp.content
    soup = BeautifulSoup(html, 'html.parser')
    link_parts = []
    token_parts = []
    for form_tag in soup.find_all('form'):
        action = form_tag.get('action')
        if action and 'krakenfiles.com' in action:
            link_parts.append(action)
        input_tag = form_tag.find('input', {'name': 'token'})
        if input_tag:
            value = input_tag.get('value')
            token_parts.append(value)
    for link_part, token_part in zip(link_parts, token_parts):
        link = f'https:{link_part}'
        data = {
            'token': token_part
        }
        response = requests.post(link, data=data)
        json_data = response.json()
        url = json_data['url']
    return sp_ytdl_download(url, tempdir)
