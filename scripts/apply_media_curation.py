#!/usr/bin/env python3
"""Apply explicitly approved media placements from a reviewed proposal."""
from __future__ import annotations
import argparse, json, shutil
from datetime import datetime
from pathlib import Path
from wiki_memory import content_body, content_cards, read_frontmatter, render_content_frontmatter, validate_content, write_content_index

def apply(project, proposal_path, approved):
    proposal=json.loads(proposal_path.read_text(encoding="utf-8"))
    if proposal.get("proposal_version") != 1: raise ValueError("unsupported media proposal_version")
    candidates={item.get("candidate_id"):item for item in proposal.get("candidates",[])}
    updates={item.get("asset_id"):item for item in proposal.get("updates",[]) if item.get("asset_id")}
    if approved-updates.keys(): raise ValueError("approved asset IDs missing from proposal")
    cards={data["id"]:(path,data) for path,data in content_cards(project)}
    changed=[]
    for asset_id in sorted(approved):
        update=updates[asset_id]; candidate=candidates.get(update.get("candidate_id"))
        if not candidate or update.get("placement") not in {"inline","appendix"}: raise ValueError(f"invalid media update: {asset_id}")
        if not asset_id.startswith("assets.") or update.get("article_id") not in cards: raise ValueError(f"invalid media IDs: {asset_id}")
        article_path,article=cards[update["article_id"]]; caption=update.get("caption")
        if not isinstance(caption,str) or not caption: raise ValueError(f"missing caption for {asset_id}")
        if candidate["kind"] != "image": raise ValueError("only local image application is supported in this release")
        source=(project/candidate["source_path"]).parent/candidate["target"]
        if not source.is_file(): raise ValueError(f"missing local asset: {candidate['target']}")
        raw=project/"raw/assets"/proposal["source_slug"]/source.name; raw.parent.mkdir(parents=True,exist_ok=True)
        if raw.exists() and raw.read_bytes()!=source.read_bytes(): raise ValueError(f"asset destination differs: {raw.relative_to(project)}")
        if not raw.exists(): shutil.copyfile(source,raw)
        card_path=project/"wiki/assets"/(asset_id.removeprefix("assets.").replace(".","-")+".md")
        if card_path.exists(): raise ValueError(f"asset card already exists: {asset_id}")
        now=datetime.now().astimezone().isoformat(timespec="seconds"); raw_path=raw.relative_to(project).as_posix()
        metadata={"schema_version":2,"id":asset_id,"type":"image","title":caption,"description":caption,"tags":update.get("tags",[]),"source":{"raw_path":raw_path},"dates":{"added_at":now,"updated_at":now},"relations":[{"type":"supports","target":update["article_id"]}],"aliases":[],"status":"active"}; validate_content(metadata)
        card_path.parent.mkdir(parents=True,exist_ok=True); card_path.write_text(render_content_frontmatter(metadata)+f"# {caption}\n\n![[{raw_path}|680]]\n",encoding="utf-8")
        article["relations"].append({"type":"references","target":asset_id}); article["dates"]["updated_at"]=now
        body=content_body(article_path); block=f"![[{raw_path}|680]]\n\n*{caption} [[assets/{card_path.stem}|Asset card]]*\n"
        if update["placement"]=="appendix": body += "\n## Illustrations and materials\n\n"+block
        else: body += "\n"+block
        article_path.write_text(render_content_frontmatter(article)+body,encoding="utf-8"); changed.append(asset_id)
    write_content_index(project); return changed

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("project",type=Path);p.add_argument("proposal",type=Path);p.add_argument("--approve",action="append",required=True);a=p.parse_args()
    try:
        for item in apply(a.project.resolve(),a.proposal.resolve(),set(a.approve)): print(item)
    except (OSError,ValueError,json.JSONDecodeError) as exc: raise SystemExit(f"error: {exc}")
if __name__=="__main__": main()
