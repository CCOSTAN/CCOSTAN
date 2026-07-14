#!/usr/bin/env python3
"""Update the profile README with paired vCloudInfo and YouTube links."""

from __future__ import annotations

import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


FEED_URL = "https://www.vcloudinfo.com/feed"
README_PATH = Path("README.md")
START_MARKER = "<!-- LATEST-CONTENT:START -->"
END_MARKER = "<!-- LATEST-CONTENT:END -->"
MAX_POSTS = 5
USER_AGENT = "CCOSTAN-profile-readme/1.0"

YOUTUBE_PATTERN = re.compile(
    r"(?:youtube(?:-nocookie)?\.com/(?:watch\?(?:[^\"'<>\s]*&)?v=|embed/)"
    r"|youtu\.be/)([A-Za-z0-9_-]{11})",
    re.IGNORECASE,
)

YOUTUBE_BADGE = (
    "[![Watch on YouTube]"
    "(https://img.shields.io/badge/Watch-YouTube-FF0000?logo=youtube&logoColor=white)]"
    "(https://youtu.be/{video_id})"
)
BLOG_BADGE = (
    "[![vCloudInfo Blog Post]"
    "(https://img.shields.io/static/v1?label=vCloudInfo&message=Blog%20Post&color=21759B"
    "&logo=wordpress&logoColor=white)]({url})"
)


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode(response.headers.get_content_charset() or "utf-8")


def latest_posts() -> list[tuple[str, str]]:
    root = ET.fromstring(fetch(FEED_URL))
    posts: list[tuple[str, str]] = []
    for item in root.findall("./channel/item")[:MAX_POSTS]:
        title = html.unescape(item.findtext("title", default="")).strip()
        url = item.findtext("link", default="").strip()
        if title and url:
            posts.append((title, url))
    if not posts:
        raise RuntimeError("The vCloudInfo feed did not contain any posts")
    return posts


def youtube_id(url: str) -> str | None:
    match = YOUTUBE_PATTERN.search(html.unescape(fetch(url)))
    return match.group(1) if match else None


def render_row(title: str, url: str) -> str:
    badges = []
    video_id = youtube_id(url)
    if video_id:
        badges.append(YOUTUBE_BADGE.format(video_id=video_id))
    badges.append(BLOG_BADGE.format(url=url))
    return f"- **{title}** {' '.join(badges)}"


def update_readme(rows: list[str]) -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    if readme.count(START_MARKER) != 1 or readme.count(END_MARKER) != 1:
        raise RuntimeError("README latest-content markers are missing or duplicated")
    before, remainder = readme.split(START_MARKER, 1)
    _, after = remainder.split(END_MARKER, 1)
    rendered_rows = "\n".join(rows)
    updated = f"{before}{START_MARKER}\n{rendered_rows}\n{END_MARKER}{after}"
    README_PATH.write_text(updated, encoding="utf-8")


def main() -> None:
    update_readme([render_row(title, url) for title, url in latest_posts()])


if __name__ == "__main__":
    main()
