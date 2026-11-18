"""Ask the manifest's pending questions in one continuing conversation, save each answer as a
NotebookLM note and as answers/<id>.md, and flag weak citations. Resumable; stops on rate limits.

Two things make the learning loop work:
  "pause_after": true on a question -> the script stops after it, so the learner can make their own
      attempt before the next question reveals the answer (problem first, teach-back).
  a {placeholder} left in a question's text (for example {attempt}) -> the script refuses to send it.

Usage: python3 -I nlm_ask.py --manifest m.json [--only Q3 Q4] [--max 5] [--no-pause]
Exit code: 0 done, 3 stopped on a rate limit, 4 paused for the learner, 1 other failures.
"""
import argparse
import collections
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nlm import PAUSE, err_text, is_rate_limited, load_manifest, project_dir, run, run_text, save_manifest, source_ids, sources  # noqa: E402

# Quote first, then answer: answers built on quoted passages stay closer to the sources. Each question is
# asked in one continuing conversation (`ask --new` would delete it), so tell NotebookLM to take facts from
# the sources, not from its own earlier answers. Gap markers are counted below as "not in sources".
CITE = (" Take every fact from the selected sources; use earlier answers in this chat only to know which case"
        " or idea I mean. Start by quoting the 2 to 4 passages that matter most, one sentence each, then answer"
        " from them. Mark any step or claim the sources do not support as [not in sources] instead of filling the gap.")
PLACEHOLDER = re.compile(r"\{[a-zA-Z_ ]{2,40}\}")
COMPARE_PHASES = ("disagree", "apply", "principles", "fails", "compare", "deliverable", "triage")


def from_history(nid, text):
    """The answer to `text` if the notebook's conversation already holds it, else "".
    The client can time out after the service has answered (and charged for) a question; seen live on 2026-11-17.
    Asking again would pay twice, so look before retrying."""
    j, _ = run(["history", "--notebook", nid, "--show-all"], timeout=180)
    want = " ".join(text.split())[:200]
    for pair in reversed((j or {}).get("qa_pairs") or []):
        if " ".join(str(pair.get("question", "")).split())[:200] == want:
            return pair.get("answer") or ""
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--only", nargs="*", help="question ids to run")
    ap.add_argument("--max", type=int, help="ask at most this many now")
    ap.add_argument("--no-pause", action="store_true", help="ignore pause_after (the learner skips their own attempt)")
    a = ap.parse_args()
    mp = a.manifest
    m = load_manifest(mp)
    nid = m.get("notebook_id") or sys.exit("No notebook_id in manifest; run nlm_build.py first.")
    pdir = project_dir(mp)
    titles = {s.get("source_id"): s["title"] for s in sources(m)}
    os.makedirs(os.path.join(pdir, "answers"), exist_ok=True)
    asked = failures = 0
    for q in m.get("questions", []):
        if q.get("status") == "done" or (a.only and q["id"] not in a.only):
            continue
        if a.max is not None and asked >= a.max:
            break
        hole = PLACEHOLDER.search(q["text"])
        if hole:
            print(f"PAUSE: {q['id']} still contains {hole.group(0)}. Fill it in (in the manifest), then rerun.")
            sys.exit(4)
        text = q["text"] if "not in sources" in q["text"].lower() else q["text"].rstrip() + CITE
        title = q.get("title") or f"{q['id']} · {q.get('phase', 'question')}"
        args = ["ask", "--notebook", nid, "--save-as-note", "--note-title", title]
        if m.get("conversation_id"):
            args += ["-c", m["conversation_id"]]
        for sid in source_ids(m, q.get("only", [])):
            args += ["-s", sid]
        j, r = run_text(args, text, timeout=600)
        ans = (j or {}).get("answer") or ""
        recovered = False
        if not ans:
            if is_rate_limited(r):
                print(f"Rate limited at {q['id']}. Stopping; rerun later to continue.")
                sys.exit(3)
            ans = from_history(nid, text)
            recovered = bool(ans)
        if not ans:
            failures += 1
            print(f"{q['id']} FAILED: {err_text(r)[-200:]}")
            time.sleep(PAUSE)
            continue
        refs = (j or {}).get("references") or []
        note_id = ((j or {}).get("note") or {}).get("id")
        if recovered:  # the answer exists but its note was never saved, and the reference list is lost
            nj, _ = run_text(["note", "create", "--notebook", nid, "--title", title], ans, timeout=180)
            note_id = (nj or {}).get("id")
        elif note_id:  # the service gives a saved answer a title of its own; put ours on it
            run(["note", "rename", note_id, title, "--notebook", nid], timeout=120)
        per_src = collections.Counter(x.get("source_id") for x in refs if isinstance(x, dict))
        gaps = len(re.findall(r"not in (the )?sources", ans, flags=re.I))
        flags = []
        if recovered:
            flags.append("recovered from the conversation after a timeout: citations not counted")
        elif not refs:
            flags.append("no citations")
        if len(refs) >= 5 and not q.get("only") and per_src and per_src.most_common(1)[0][1] / len(refs) > 0.8 \
                and len(m.get("sources", [])) > 1 and q.get("phase") in COMPARE_PHASES:
            flags.append(f"one source dominates ({titles.get(per_src.most_common(1)[0][0], '?')})")
        if gaps:
            flags.append(f"{gaps} gap(s) marked 'not in sources'")
        m["conversation_id"] = m.get("conversation_id") or (j or {}).get("conversation_id")
        q.update(status="done", citations=None if recovered else len(refs), flags=flags, gaps=gaps,
                 sources_cited=[titles.get(s, s) for s, _ in per_src.most_common()], note_id=note_id)
        with open(os.path.join(pdir, "answers", f"{q['id']}.md"), "w", encoding="utf-8") as f:
            f.write(f"# {q['id']} ({q.get('phase', '')})\n\n**Question:** {q['text']}\n\n"
                    f"**Citations:** {'not counted' if recovered else len(refs)} from {', '.join(q['sources_cited']) or 'none'}"
                    f"{'  ⚠ ' + '; '.join(flags) if flags else ''}\n\n---\n\n{ans}\n")
        save_manifest(mp, m)
        asked += 1
        print(f"{q['id']} {'recovered' if recovered else 'ok'}: {len(ans)} chars, {len(refs)} citations from {len(per_src)} source(s)"
              f"{'  ⚠ ' + '; '.join(flags) if flags else ''}")
        if q.get("pause_after") and not a.no_pause:
            print(f"PAUSE after {q['id']}: show answers/{q['id']}.md to the learner and get their own attempt "
                  f"before going on. Put it into the next question, then rerun.")
            sys.exit(4)
    left = sum(1 for q in m.get("questions", []) if q.get("status") != "done")
    print(f"asked {asked}, failed {failures}, still pending {left}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
