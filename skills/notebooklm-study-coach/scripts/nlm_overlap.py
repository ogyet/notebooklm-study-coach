"""Read-only: which existing NotebookLM notebooks already hold these sources, and what's been made in them.

Usage:
  python3 -I nlm_overlap.py --manifest ~/Documents/Learning/x/y/manifest.json
  python3 -I nlm_overlap.py --titles "The Mom Test" "Founding Sales" --urls https://youtu.be/abc [--keywords sales]
Prints, per notebook with any match: the matched sources and their IDs (usable as copy_from), the kinds
of Studio output already made, the note count, and a reuse/create hint.
Uses only list / source list / artifact list / note list.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nlm import items, load_manifest, norm_title, norm_url, run, sources  # noqa: E402


def matches(want, have):
    """A wanted title matches a source if one normalized title starts the other on a word boundary.

    One-word titles ("Antifragile", "Influence", "Build") are common, so they count too, but only
    when the word is at least 5 letters: short words like "who" would otherwise match unrelated
    sources ("Who Not How"). Exact equality always matches."""
    w, h = norm_title(want).split(), norm_title(have).split()
    if not w or not h:
        return False
    if w == h:
        return True
    short, long_ = (w, h) if len(w) <= len(h) else (h, w)
    if long_[:len(short)] != short:
        return False
    return len(short) >= 2 or len(short[0]) >= 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest")
    ap.add_argument("--titles", nargs="*", default=[])
    ap.add_argument("--urls", nargs="*", default=[])
    ap.add_argument("--keywords", nargs="*", default=[], help="also report notebooks whose title has these words")
    a = ap.parse_args()
    titles, urls, skip_id = list(a.titles), list(a.urls), None
    if a.manifest:
        m = load_manifest(a.manifest)
        for s in sources(m):
            (urls if s.get("url") else titles).append(s["url"] if s.get("url") else s["title"].split(" — ")[0])
        skip_id = m.get("notebook_id")
    wanted = len(titles) + len(urls)
    if not wanted and not a.keywords:
        ap.error("give --manifest, --titles, --urls or --keywords")
    j, r = run(["list"], timeout=180)
    nbs = items(j, "notebooks")
    if not nbs:
        sys.exit(f"could not list notebooks: {r.stderr[-300:]}")
    kws = [k.lower() for k in a.keywords]
    want_urls = {norm_url(u): u for u in urls}
    report = []
    for nb in nbs:
        if nb["id"] == skip_id:
            continue
        sj, _ = run(["source", "list", "-n", nb["id"]], timeout=180)
        srcs = items(sj, "sources")
        hit = {t: s.get("id") for t in titles for s in srcs if matches(t, s.get("title", ""))}
        hit.update({want_urls[norm_url(s.get("url"))]: s.get("id") for s in srcs
                    if s.get("url") and norm_url(s.get("url")) in want_urls})
        kw_hit = any(k in nb["title"].lower() for k in kws)
        if not hit and not kw_hit:
            continue
        aj, _ = run(["artifact", "list", "-n", nb["id"]], timeout=180)
        nj, _ = run(["note", "list", "-n", nb["id"]], timeout=180)
        arts = items(aj, "artifacts")
        kinds = sorted({str(x.get("type") or x.get("kind") or "?") for x in arts})
        report.append((len(hit), nb, hit, kinds, len(items(nj, "notes")), len(srcs),
                       [f'{x.get("type")}: {x.get("title", "")[:60]}' for x in arts]))
    if not report:
        print("No existing notebook holds these sources. Create a new one.")
        return
    report.sort(key=lambda x: -x[0])
    for n_hit, nb, hit, kinds, n_notes, n_src, made in report:
        share = n_hit / wanted if wanted else 0
        hint = "REUSE if it is about the same topic, otherwise copy from it" if share >= 0.6 else ("partial overlap" if n_hit else "related by title")
        print(f'== {nb["title"]}  [{nb["id"][:8]}]  {n_src} sources, {n_notes} notes  -> {hint}')
        if hit:
            print(f"   has {n_hit}/{wanted} of your sources (source ids usable as copy_from):")
            for t, sid in sorted(hit.items()):
                print(f"     {t}  -> source {sid}")
        print("   already made: " + (", ".join(kinds) if kinds else "nothing"))
        for t in made:
            print(f"     {t}")


if __name__ == "__main__":
    main()
