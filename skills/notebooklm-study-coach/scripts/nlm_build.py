"""Create (or reuse) one topic notebook, add its sources, set the plain-language chat persona,
and wait until every source is ready. Resumable: anything already recorded in the manifest is skipped.

Each entry in the manifest's "sources" needs a "key", a "title" and ONE origin:
  "path"       local file (PDF, EPUB, DOCX, TXT, MD ...)        -> uploaded
  "url"        web page or YouTube link                          -> added by reference
  "text_file"  local text or markdown file                       -> pasted as a text source under the title
  "drive"      {"file_id": "...", "mime": "google-doc|google-slides|google-sheets|pdf"}
  "copy_from"  {"notebook_id": "...", "source_id": "..."}        -> copied from another notebook, no re-upload
               (add a "path" or "url" as well and it is used if the copy fails)
or an existing "source_id" for something already in the notebook.

Usage: python3 -I nlm_build.py --manifest .../manifest.json [--check] [--no-wait] [--timeout 900]
  --check   only validate the manifest; touches nothing (safe before approval)
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nlm import (PAUSE, SKILL_DIR, audience, err_text, is_youtube, items, load_manifest, new_id, project_dir,  # noqa: E402
                  resolve, run, run_text, save_manifest, sources)

ORIGINS = ("path", "url", "text_file", "file", "drive", "copy_from")
PERSONA_LIMIT = 10000


def persona_file(m, pdir):
    p = m.get("persona")
    if isinstance(p, dict) and p.get("file"):
        return resolve(pdir, p["file"])
    return os.path.join(SKILL_DIR, "assets", "persona-plain.txt")


def problems(m, pdir):
    """Everything wrong with the manifest that can be seen without calling NotebookLM."""
    out, seen = [], set()
    if not m.get("title"):
        out.append('no "title" for the notebook')
    if not m.get("problem"):
        out.append('no "problem": say what the learner wants to be able to do or explain')
    for i, s in enumerate(sources(m)):
        name = s.get("title") or s.get("key") or f"source #{i + 1}"
        if not s.get("key") or not s.get("title"):
            out.append(f'{name}: needs both "key" and "title"')
        if s.get("key") in seen:
            out.append(f'{name}: duplicate key "{s.get("key")}"')
        seen.add(s.get("key"))
        if s.get("source_id"):
            continue
        if not any(s.get(o) for o in ORIGINS):
            out.append(f"{name}: no origin (one of path, url, text_file, drive, copy_from)")
        local = s.get("text_file") or s.get("file")
        if local and not os.path.isfile(resolve(pdir, local)):
            out.append(f"{name}: text file not found: {local}")
        if s.get("path") and not s.get("copy_from") and not os.path.isfile(resolve(pdir, s["path"])):
            out.append(f"{name}: file not found: {s['path']}")
        if s.get("url") and not str(s["url"]).startswith(("http://", "https://")):
            out.append(f"{name}: url must start with http:// or https://")
        if s.get("drive") and not (isinstance(s["drive"], dict) and s["drive"].get("file_id")):
            out.append(f'{name}: drive needs {{"file_id": ...}}')
        cf = s.get("copy_from")
        if cf and not (isinstance(cf, dict) and cf.get("notebook_id") and cf.get("source_id")):
            out.append(f'{name}: copy_from needs {{"notebook_id": ..., "source_id": ...}}')
    if m.get("persona") is not False:
        pf = persona_file(m, pdir)
        if not os.path.isfile(pf):
            out.append(f"persona file not found: {pf}")
        elif len(open(pf, encoding="utf-8").read()) > PERSONA_LIMIT - 600:
            out.append(f"persona file is too long (limit about {PERSONA_LIMIT - 600} characters): {pf}")
    return out


def add_source(nid, s, pdir):
    """Add one source by its origin. Returns (source_id_or_None, CompletedProcess)."""
    if s.get("path"):
        j, r = run(["source", "add", "--notebook", nid, "--type", "file", resolve(pdir, s["path"]),
                    "--timeout", "300"], timeout=420)
    elif s.get("url"):
        kind = "youtube" if is_youtube(s["url"]) else "url"
        j, r = run(["source", "add", "--notebook", nid, "--type", kind, s["url"], "--timeout", "120"], timeout=240)
    elif s.get("text_file") or s.get("file"):
        text = open(resolve(pdir, s.get("text_file") or s.get("file")), encoding="utf-8").read().strip()
        j, r = run_text(["source", "add", "--notebook", nid, "--type", "text", "--title", s["title"]], text, timeout=180)
    elif s.get("drive"):
        d = s["drive"]
        j, r = run(["source", "add-drive", "--notebook", nid, "--mime-type", d.get("mime", "google-doc"),
                    d["file_id"], s["title"]], timeout=240)
    else:
        return None, None
    return new_id(j), r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--check", action="store_true", help="validate the manifest only; nothing is created")
    ap.add_argument("--no-wait", action="store_true")
    ap.add_argument("--timeout", type=int, default=900, help="seconds to wait for all sources to be ready")
    a = ap.parse_args()
    mp = a.manifest
    m = load_manifest(mp)
    pdir = project_dir(mp)

    # 0. validate BEFORE touching NotebookLM (a bad path would otherwise be uploaded as text).
    bad = problems(m, pdir)
    n_src = len(sources(m))
    if bad:
        sys.exit("Manifest problems, nothing created:\n  - " + "\n  - ".join(bad))
    if n_src > 15:
        print(f"NOTE: {n_src} sources in one notebook. Above about 15, answers get vaguer; consider splitting the topic.")
    if a.check:
        print(f"OK: manifest is valid ({n_src} sources). Nothing was created.")
        return

    # 1. notebook
    if not m.get("notebook_id"):
        j, r = run_text(["create"], m["title"], timeout=180)
        nid = new_id(j, "notebook")
        if not nid:
            sys.exit(f"create failed: {err_text(r)}")
        m["notebook_id"] = nid
        save_manifest(mp, m)
        print(f"created notebook {m['title']} [{nid}]")
    nid = m["notebook_id"]

    # 1b. file it under the subject's collection (a NotebookLM group of notebooks). Never fatal.
    col = m.get("collection")
    if col and not m.get("collection_added"):
        j, _ = run(["collection", "list"], timeout=120)
        if col not in {c.get("name") for c in items(j, "collections")}:
            run(["collection", "create", col], timeout=120)
        _, r = run(["collection", "add", col, nid], timeout=120)
        if r.returncode == 0:
            m["collection_added"] = True
            save_manifest(mp, m)
            print(f"filed under collection: {col}")
        else:
            print(f"could not add to collection '{col}' (carrying on): {err_text(r)[-160:]}")

    # 2. sources that already exist in another notebook: copy them (no re-upload, same processed text)
    for s in sources(m):
        cf = s.get("copy_from")
        if s.get("source_id") or not cf:
            continue
        j, r = run(["source", "copy", cf["source_id"], "--notebook", cf["notebook_id"], "--to", nid], timeout=300)
        copied = (j or {}).get("copied") or []
        sid = (copied[0].get("source") or {}).get("id") if copied else None
        if sid:
            s.update(source_id=sid, added_here=True)
            save_manifest(mp, m)
            print(f"copied from notebook {cf['notebook_id'][:8]}: {s['title']}")
            continue
        print(f"copy failed for {s['title']}: {err_text(r)[-200:]}")
        if any(s.get(o) for o in ORIGINS if o != "copy_from"):
            print("  will add it from its own origin instead")
            s.pop("copy_from")

    # 3. everything else (the clean title comes last, in step 6)
    for s in sources(m):
        if not s.get("source_id") and not s.get("copy_from"):
            for attempt in range(3):
                sid, r = add_source(nid, s, pdir)
                if sid:
                    s.update(source_id=sid, added_here=True)
                    save_manifest(mp, m)
                    print(f"added: {s['title']}")
                    break
                print(f"add failed (try {attempt + 1}): {s['title']}: {err_text(r)[-200:] if r else 'no origin'}")
                time.sleep(PAUSE)
            else:
                print(f"GAVE UP on {s['title']}; rerun later, or give it another origin")
                continue

    # 4. chat persona: plain-language tutor rules, plus who the learner is and what they are after
    p = m.get("persona")
    if p is not False and not (isinstance(p, dict) and p.get("set")):
        text = open(persona_file(m, pdir), encoding="utf-8").read().strip()
        text += f"\n\nThe learner is {audience(m)}. What they want to be able to do: {m['problem']}"
        _, r = run(["configure", "--notebook", nid, "--persona", text[:PERSONA_LIMIT]], timeout=120)
        if r.returncode == 0:
            m["persona"] = {**(p if isinstance(p, dict) else {}), "set": True}
            save_manifest(mp, m)
            print("chat persona set (plain-language tutor)")
        else:
            print(f"could not set the chat persona (carrying on): {err_text(r)[-160:]}")

    if a.no_wait:
        print("Not waiting. Run again (or source list) to confirm everything is ready.")
        return

    # 5. wait until every recorded source is ready
    want = {x["source_id"]: x["title"] for x in sources(m) if x.get("source_id")}
    missing = [x["title"] for x in sources(m) if not x.get("source_id")]
    deadline = time.time() + a.timeout
    while True:
        j, r = run(["source", "list", "--notebook", nid], timeout=180)
        status = {x.get("id"): x.get("status", "?") for x in items(j, "sources")}
        pending = {sid: t for sid, t in want.items() if status.get(sid) != "ready"}
        failed = {sid: t for sid, t in pending.items() if status.get(sid) in ("error", "failed")}
        if not pending:
            print(f"READY: {len(want)} sources processed in notebook {nid}")
            break
        if failed or time.time() > deadline:
            for sid, t in pending.items():
                print(f"NOT READY ({status.get(sid, 'missing')}): {t}")
            sys.exit(1)
        time.sleep(PAUSE)

    # 6. clean titles, last. A rename sent while a source is still processing reports success and is then lost
    #    (seen live on 2026-11-17), so rename only what is ready, and believe the listing, not the exit code.
    mine = {x["source_id"]: x for x in sources(m) if x.get("source_id") and x.get("added_here")}  # never what was already there
    held = {x.get("id"): x.get("title") for x in items(j, "sources")}
    todo = [x for sid, x in mine.items() if held.get(sid) != x["title"]]
    for x in todo:
        run(["source", "rename", x["source_id"], x["title"], "--notebook", nid], timeout=120)
    if todo:
        j, r = run(["source", "list", "--notebook", nid], timeout=180)
        held = {x.get("id"): x.get("title") for x in items(j, "sources")}
    for sid, x in mine.items():
        x["renamed"] = held.get(sid) == x["title"]
    save_manifest(mp, m)
    stuck = [x["title"] for x in mine.values() if not x["renamed"]]
    if stuck:
        print("TITLE NOT CHANGED (rerun to retry): " + "; ".join(stuck))
    if missing:
        print("NOT ADDED: " + "; ".join(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()
