"""Read-only inventory of the account's notebooks, for mapping topics, spotting mixed notebooks,
and keeping the index file. The only thing it ever writes is the local INDEX.md.

Usage:
  python3 -I nlm_inventory.py                       # every notebook: group, sources, what's been made
  python3 -I nlm_inventory.py --notebook ID         # one notebook in detail (to plan a split)
  python3 -I nlm_inventory.py --notebook ID --prompts   # ...plus the prompt behind each Studio output
  python3 -I nlm_inventory.py --write-index         # also (re)write <learning root>/INDEX.md
The index keeps a "Purpose" for each notebook. A purpose typed by hand is kept on later runs; otherwise it
is taken from the "problem" in that notebook's manifest under the learning root.
"""
import argparse
import collections
import glob
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nlm import items, learning_root, run  # noqa: E402

BIG = 15
BLANK = "—"


def groups():
    """notebook id -> collection name(s)."""
    out = collections.defaultdict(list)
    j, _ = run(["collection", "list"], timeout=120)
    for c in items(j, "collections"):
        nj, _ = run(["collection", "notebooks", c.get("id", "")], timeout=120)
        for nb in items(nj, "notebooks"):
            out[nb.get("id")].append(c.get("name", "?"))
    return out


def manifest_purposes(root):
    out = {}
    for p in glob.glob(os.path.join(root, "**", "manifest.json"), recursive=True):
        try:
            m = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if m.get("notebook_id") and m.get("problem"):
            out[m["notebook_id"]] = m["problem"]
    return out


def index_purposes(path):
    """Purposes already written in INDEX.md, keyed by the short id in the last column."""
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and cells[-1] not in ("ID", "") and cells[3] not in ("Purpose", BLANK, "") \
                and not set(cells[3]) <= set("-: "):
            out[cells[-1]] = cells[3]
    return out


def detail(nid, with_prompts):
    sj, r = run(["source", "list", "-n", nid], timeout=180)
    if not isinstance(sj, dict):
        sys.exit(f"could not read notebook {nid}: {r.stderr[-200:]}")
    srcs = items(sj, "sources")
    print(f'== {sj.get("notebook_title", "?")}  [{str(sj.get("notebook_id", nid))[:8]}]  {len(srcs)} sources')
    for s in srcs:
        print(f'  source {s.get("id", "")[:8]}  {str(s.get("type", "?")):9} {s.get("title", "")}'
              + (f'  <{s["url"]}>' if s.get("url") else ""))
    aj, _ = run(["artifact", "list", "-n", nid], timeout=180)
    for x in items(aj, "artifacts"):
        print(f'  made   {x.get("id", "")[:8]}  {str(x.get("type", "?")):11} {x.get("title", "")}')
        if with_prompts:
            pj, pr = run(["artifact", "get-prompt", x.get("id", ""), "-n", nid], timeout=120)
            prompt = (pj or {}).get("prompt") if isinstance(pj, dict) else None
            print(f'         asked for: {(prompt or "(no custom prompt)").strip()[:300]}')
    nj, _ = run(["note", "list", "-n", nid], timeout=180)
    for n in items(nj, "notes"):
        print(f'  note   {n.get("title", "")}')
    if len(srcs) > BIG:
        print(f"  NOTE: more than {BIG} sources. Check whether this is one topic or several.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notebook")
    ap.add_argument("--prompts", action="store_true")
    ap.add_argument("--write-index", action="store_true")
    ap.add_argument("--root", default=learning_root())
    a = ap.parse_args()
    if a.notebook:
        detail(a.notebook, a.prompts)
        return
    j, r = run(["list"], timeout=180)
    nbs = items(j, "notebooks")
    if not nbs:
        sys.exit(f"could not list notebooks: {r.stderr[-300:]}")
    grp = groups()
    index_path = os.path.join(a.root, "INDEX.md")
    purposes = {nid[:8]: text for nid, text in manifest_purposes(a.root).items()}
    purposes.update(index_purposes(index_path))  # a purpose typed into the index by hand wins
    rows = []
    for nb in sorted(nbs, key=lambda x: (", ".join(grp.get(x["id"], ["~"])), x.get("title", ""))):
        sj, _ = run(["source", "list", "-n", nb["id"]], timeout=180)
        aj, _ = run(["artifact", "list", "-n", nb["id"]], timeout=180)
        srcs, arts = items(sj, "sources"), items(aj, "artifacts")
        types = collections.Counter(str(s.get("type", "?")) for s in srcs)
        made = sorted({str(x.get("type", "?")) for x in arts})
        rows.append({"title": nb.get("title", ""), "id": nb["id"][:8], "group": ", ".join(grp.get(nb["id"], [])) or BLANK,
                     "n": len(srcs), "types": ", ".join(f"{n} {t}" for t, n in types.most_common()),
                     "made": ", ".join(made) or BLANK, "purpose": purposes.get(nb["id"][:8], BLANK)})
    for x in rows:
        print(f'{x["id"]}  {x["title"][:58]:58}  {x["n"]:>3} sources ({x["types"]})'
              + (f'  group: {x["group"]}' if x["group"] != BLANK else "")
              + (f"  BIG" if x["n"] > BIG else "") + (f'\n          made: {x["made"]}' if x["made"] != BLANK else "")
              + (f'\n          purpose: {x["purpose"]}' if x["purpose"] != BLANK else ""))
    no_purpose = sum(1 for x in rows if x["purpose"] == BLANK)
    print(f"{len(rows)} notebooks; {no_purpose} have no purpose recorded; "
          f"{sum(1 for x in rows if x['n'] > BIG)} have more than {BIG} sources")
    if a.write_index:
        os.makedirs(a.root, exist_ok=True)
        esc = lambda c: str(c).replace("|", "/")  # noqa: E731
        fd, tmp = tempfile.mkstemp(dir=a.root, prefix=".index.", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("# Learning index\n\nOne line per NotebookLM notebook: what it is for. Edit the Purpose column by hand; "
                    "reruns keep your text.\n\n| Notebook | Group | Sources | Purpose | Made | ID |\n|---|---|---|---|---|---|\n")
            f.writelines(f'| {esc(x["title"])} | {esc(x["group"])} | {x["n"]} | {esc(x["purpose"])} | {esc(x["made"])} '
                         f'| {x["id"]} |\n' for x in rows)
        os.replace(tmp, index_path)
        print(f"index written: {index_path}")


if __name__ == "__main__":
    main()
