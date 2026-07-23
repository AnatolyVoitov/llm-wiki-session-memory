#!/usr/bin/env python3
"""Discover local images and YouTube links in a Markdown or HTML source without changing the Wiki."""
from __future__ import annotations
import argparse, json, re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
MD_IMAGE = re.compile(r"!\[([^]]*)\]\(([^)]+)\)")
HTML_IMAGE = re.compile(r"<img\s+[^>]*src=[\"']([^\"']+)[\"'][^>]*>", re.I)
ALT = re.compile(r"alt=[\"']([^\"']*)[\"']", re.I)
URL = re.compile(r"https?://[^\s<>)]+")

def heading_before(text, position):
    headings = list(re.finditer(r"^#+\s+(.+)$", text[:position], re.M))
    return headings[-1].group(1).strip() if headings else None

def is_youtube(value):
    return urlparse(value).netloc.lower() in YOUTUBE_HOSTS

def proposal_for(project, source):
    if source.suffix.lower() not in {".md", ".markdown", ".html", ".htm"}:
        raise ValueError("source must be Markdown or HTML")
    text=source.read_text(encoding="utf-8")
    candidates=[]
    def add(kind, target, label, position):
        if kind == "image":
            parsed=urlparse(target)
            if parsed.scheme or Path(parsed.path).suffix.lower() not in IMAGE_SUFFIXES: return
        candidate={"candidate_id": f"media-{len(candidates)+1:03d}", "kind":kind, "target":target, "label":label or "", "heading":heading_before(text, position), "source_path":source.relative_to(project).as_posix()}
        candidates.append(candidate)
    for match in MD_IMAGE.finditer(text): add("image", match.group(2).strip(), match.group(1).strip(), match.start())
    for match in HTML_IMAGE.finditer(text):
        tag=match.group(0); alt=ALT.search(tag); add("image", match.group(1).strip(), alt.group(1).strip() if alt else "", match.start())
    for match in URL.finditer(text):
        value=match.group(0).rstrip(".,")
        if is_youtube(value): add("youtube", value, "", match.start())
    candidates.sort(key=lambda row: text.find(row["target"]))
    for number,row in enumerate(candidates,1): row["candidate_id"]=f"media-{number:03d}"
    return {"proposal_version":1,"generated_at":datetime.now().astimezone().isoformat(timespec="seconds"),"source":source.relative_to(project).as_posix(),"source_slug":source.stem,"candidates":candidates,"updates":[]}

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("project",type=Path); parser.add_argument("source",type=Path); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args()
    try:
        data=proposal_for(args.project.resolve(),args.source.resolve()); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(args.output)
    except (OSError,ValueError) as exc: raise SystemExit(f"error: {exc}")
if __name__=="__main__": main()
