"""Find books in the Calibre library (read-only) and print their EPUB/PDF paths.

Usage:
  python3 -I calibre_find.py "mom test" "founding sales"     # search title or author
  python3 -I calibre_find.py --ids 63 5 97                   # exact Calibre IDs
  python3 -I calibre_find.py --recent 20                     # newest additions
  add --json for machine-readable output, --library PATH to override the library
"""
import argparse
import json
import os
import sqlite3
import sys

PREFERRED = ["EPUB", "PDF", "TXT", "DOCX", "MD"]


def library_path(override):
    if override:
        return override
    cfg = os.path.expanduser("~/Library/Preferences/calibre/global.py.json")  # macOS
    if not os.path.exists(cfg):
        cfg = os.path.expanduser("~/.config/calibre/global.py.json")  # Linux
    try:
        return json.load(open(cfg)).get("library_path") or os.path.expanduser("~/Calibre Library")
    except (OSError, ValueError):
        return os.path.expanduser("~/Calibre Library")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("terms", nargs="*")
    ap.add_argument("--ids", nargs="*", type=int)
    ap.add_argument("--recent", type=int)
    ap.add_argument("--library")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    lib = library_path(a.library)
    db = os.path.join(lib, "metadata.db")
    if not os.path.exists(db):
        sys.exit(f"Calibre library not found at {lib}")
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    base = """
      SELECT b.id, b.title, b.path, b.timestamp,
             (SELECT group_concat(au.name, ' & ') FROM books_authors_link l JOIN authors au ON au.id = l.author
              WHERE l.book = b.id) AS authors
      FROM books b"""
    if a.ids:
        rows = con.execute(base + f" WHERE b.id IN ({','.join('?' * len(a.ids))})", a.ids).fetchall()
    elif a.recent:
        rows = con.execute(base + " ORDER BY b.timestamp DESC LIMIT ?", (a.recent,)).fetchall()
    elif a.terms:
        rows, seen = [], set()
        for t in a.terms:
            like = f"%{t}%"
            for r in con.execute(base + " WHERE b.title LIKE ? OR b.id IN (SELECT l.book FROM books_authors_link l "
                                 "JOIN authors au ON au.id = l.author WHERE au.name LIKE ?)", (like, like)):
                if r[0] not in seen:
                    seen.add(r[0]); rows.append(r)
    else:
        ap.error("give search terms, --ids or --recent")
    out = []
    for bid, title, path, ts, authors in rows:
        authors = (authors or "").replace("|", ",")  # Calibre stores commas in names as "|"
        fmts = {f.upper(): name for f, name in con.execute("SELECT format, name FROM data WHERE book = ?", (bid,))}
        fmt = next((f for f in PREFERRED if f in fmts), None)
        fpath = os.path.join(lib, path, f"{fmts[fmt]}.{fmt.lower()}") if fmt else None
        size = round(os.path.getsize(fpath) / 1e6, 1) if fpath and os.path.exists(fpath) else None
        out.append({"calibre_id": bid, "title": title, "authors": authors or "", "format": fmt,
                    "path": fpath, "size_mb": size, "all_formats": sorted(fmts),
                    "suggested_title": f"{title.split(':')[0].strip()} — {(authors or '').split(' & ')[0]}".strip(" —")})
    if a.json:
        print(json.dumps(out, indent=1, ensure_ascii=False))
        return
    for b in out:
        flag = "" if b["path"] else "  !! no EPUB/PDF/TXT"
        print(f'{b["calibre_id"]:>4}  {b["title"][:55]:55}  {b["authors"][:28]:28}  {b["format"] or "-":4} '
              f'{(str(b["size_mb"]) + " MB") if b["size_mb"] is not None else "":>8}{flag}')
    print(f"{len(out)} book(s) in {lib}")


if __name__ == "__main__":
    main()
