"""A fake `notebooklm` for tests. Validates every call against spec.json (made from the real --help),
logs it, keeps a little state, and never touches the network. Driven by env vars:
  FAKE_STATE, FAKE_LOG   paths (required)
  FAKE_FAIL_ADD_ONCE=1   the first `source add` fails
  FAKE_RATE_LIMIT_AT=N   the Nth `ask` fails with a rate-limit error
  FAKE_TIMEOUT_AT=N      the Nth `ask` is answered on the server, but the client times out before it gets the answer
  FAKE_COMPLETE_ALL=1    queued artifacts become completed
Words inside a prompt or question steer the output: CROWD, NOCITE, GAPS, DOMINATE, BROKEN."""
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = json.load(open(os.path.join(HERE, "spec.json")))
STATE_P, LOG = os.environ["FAKE_STATE"], os.environ["FAKE_LOG"]
argv = sys.argv[1:]
with open(LOG, "a") as f:
    f.write(json.dumps(argv) + "\n")
st = json.load(open(STATE_P)) if os.path.exists(STATE_P) else {}
for k, v in (("n", 0), ("notebooks", {}), ("sources", {}), ("artifacts", {}), ("collections", {"Existing Group": []}),
             ("asks", 0), ("violations", []), ("personas", {})):
    st.setdefault(k, v)


def save():
    json.dump(st, open(STATE_P, "w"), indent=1)


def fail(msg, code=2):
    save()
    print(msg, file=sys.stderr)
    sys.exit(code)


def out(obj):
    save()
    print("Matched: something (fake)")
    print(json.dumps(obj))
    sys.exit(0)


def nid_():
    st["n"] += 1
    return st["n"]


cmd = next((" ".join(argv[:k]) for k in (2, 1) if " ".join(argv[:k]) in SPEC), None)
if not cmd:
    fail(f"Error: No such command {argv[:2]}")
sp, rest = SPEC[cmd], argv[len(cmd.split()):]
o, pos, i, literal = {}, [], 0, False
while i < len(rest):
    t = rest[i]
    if literal or not t.startswith("-") or t == "-":
        pos.append(t); i += 1; continue
    if t == "--":
        literal = True; i += 1; continue
    if t not in sp["options"]:
        fail(f"Error: No such option: {t}  (command: {cmd})")
    e = sp["options"][t]
    key = e["name"].lstrip("-")
    if e["value"]:
        if i + 1 >= len(rest):
            fail(f"Error: Option {t} requires an argument")
        if e["choices"] and rest[i + 1] not in e["choices"]:
            fail(f"Error: Invalid value for {t}: {rest[i + 1]!r} is not one of {e['choices']}  (command: {cmd})")
        o.setdefault(key, []).append(rest[i + 1]); i += 2
    else:
        o[t.lstrip("-")] = [True]; i += 1
if not sp["min_pos"] <= len(pos) <= sp["max_pos"]:
    fail(f"Error: wrong number of arguments for {cmd}: {pos}")
if "json" not in o:
    fail(f"Error (fake): scripts must pass --json  (command: {cmd})")
nb = (o.get("notebook") or [None])[0]
if os.environ.get("FAKE_COMPLETE_ALL"):
    for a in st["artifacts"].values():
        a["status"] = "completed"

TYPES = {"report": ("Report", "report"), "mind-map": ("Mind Map", "mind_map"), "data-table": ("Data Table", "data_table"),
         "infographic": ("Infographic", "infographic"), "slide-deck": ("Slide Deck", "slide_deck"), "quiz": ("Quiz", "quiz"),
         "flashcards": ("Flashcards", "flashcards"), "audio": ("Audio", "audio"), "video": ("Video", "video")}


def png(w=64, h=40):
    raw = b"".join(b"\x00" + b"\xcc\xdd\xee" * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)  # noqa: E731
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def pdf(pages):
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % (3 + k) for k in range(pages)) + b"] /Count %d >>" % pages]
    objs += [b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 320 180] >>" for _ in range(pages)]
    body, offs = b"%PDF-1.4\n", []
    for k, ob in enumerate(objs, 1):
        offs.append(len(body))
        body += b"%d 0 obj\n" % k + ob + b"\nendobj\n"
    xref = len(body)
    body += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % x for x in offs)
    return body + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)


def tree(branches, depth):
    def kids(level, label):
        return [] if level >= depth else [{"name": f"{label}.{k}", "children": kids(level + 1, f"{label}.{k}")} for k in range(1, 4)]
    return {"name": "Topic", "children": [{"name": f"Branch {b}", "children": kids(1, f"B{b}")} for b in range(1, branches + 1)]}


if cmd == "create":
    n = f"nb-{nid_()}"
    st["notebooks"][n] = {"title": pos[0]}
    out({"notebook": {"id": n, "title": pos[0]}})
if cmd == "list":
    out({"notebooks": [{"id": k, "title": v["title"]} for k, v in st["notebooks"].items()]})
if cmd == "collection list":
    out({"collections": [{"id": f"col-{k}", "name": k, "notebook_count": len(v)} for k, v in st["collections"].items()]})
if cmd == "collection create":
    st["collections"].setdefault(pos[0], [])
    out({"collection": {"name": pos[0]}})
if cmd == "collection add":
    if pos[0] not in st["collections"]:
        fail(json.dumps({"error": True, "code": "NOT_FOUND", "message": "no such collection"}), 1)
    st["collections"][pos[0]] += pos[1:]
    out({"added": pos[1:]})
if cmd == "collection notebooks":
    name = pos[0][4:] if pos[0].startswith("col-") else pos[0]
    out({"notebooks": [{"id": x, "title": st["notebooks"].get(x, {}).get("title", "?")} for x in st["collections"].get(name, [])]})
if cmd == "source copy":
    if any(p.startswith("bad") for p in pos):
        fail(json.dumps({"error": True, "code": "NOT_FOUND", "message": "source not found"}), 1)
    made = []
    for p in pos:
        sid = f"cp-{p}-{nid_()}"
        st["sources"][sid] = {"nb": o["to"][0], "title": f"copied {p}", "type": "epub", "url": None, "settled": False}
        made.append({"source": {"id": sid}})
    out({"copied": made})
if cmd in ("source add", "source add-drive"):
    if os.environ.get("FAKE_FAIL_ADD_ONCE") and not st.get("failed_once"):
        st["failed_once"] = True
        fail(json.dumps({"error": True, "code": "UPLOAD", "message": "transient upload error"}), 1)
    kind = "drive" if cmd.endswith("drive") else o.get("type", ["auto"])[0]
    if kind == "file" and not os.path.isfile(pos[0]):
        fail(json.dumps({"error": True, "message": "file not found"}), 1)
    title = pos[1] if kind == "drive" else (o.get("title") or [os.path.basename(pos[0])])[0]
    sid = f"src-{nid_()}"
    st["sources"][sid] = {"nb": nb, "title": title, "type": kind, "url": pos[0] if kind in ("url", "youtube") else None,
                          "content": pos[0][:200], "opts": {k: v for k, v in o.items() if k != "json"}, "settled": False}
    out({"source": {"id": sid, "title": title}})
if cmd == "source rename":
    if pos[0] not in st["sources"]:
        fail("not found", 1)
    if st["sources"][pos[0]].get("settled", True):  # like the real service: a rename sent while a source is
        st["sources"][pos[0]]["title"] = pos[1]        # still processing reports success and is then lost
    out({"action": "rename", "source_id": pos[0], "title": pos[1], "status": "renamed"})
if cmd == "source list":
    rows = [{"id": k, "title": v["title"], "type": v["type"], "url": v.get("url"),
             "status": "error" if "BROKEN" in v["title"] + str(v.get("content", "")) else "ready"}
            for k, v in st["sources"].items() if v["nb"] == nb]
    for v in st["sources"].values():  # a source counts as processed once it has been listed
        if v["nb"] == nb:
            v["settled"] = True
    out({"notebook_id": nb, "notebook_title": st["notebooks"].get(nb, {}).get("title", "?"), "count": len(rows), "sources": rows})
if cmd == "configure":
    if not any(k in o for k in ("persona", "mode", "response-length")):
        st["violations"].append("bare configure")
    st["personas"][nb] = (o.get("persona") or [""])[0]
    out({"configured": True})
if cmd == "ask":
    if "new" in o:
        st["violations"].append("ask --new")
    st["asks"] += 1
    if str(st["asks"]) == os.environ.get("FAKE_RATE_LIMIT_AT"):
        fail(json.dumps({"error": True, "code": "RATE_LIMITED", "message": "rate limit exceeded"}), 1)
    text = pos[0] if pos else ""
    sids = [k for k, v in st["sources"].items() if v["nb"] == nb] or ["s0"]
    refs = [] if "NOCITE" in text else [{"source_id": sids[0] if "DOMINATE" in text else sids[k % len(sids)]} for k in range(6)]
    st.setdefault("ask_log", []).append({"text": text, "conv": o.get("conversation-id"), "sources": o.get("source"),
                                         "note_title": o.get("note-title"), "saved": "save-as-note" in o})
    answer = f"Answer to: {text[:60]} [1][2]" + (" Part of this is not in sources." if "GAPS" in text else "")
    st.setdefault("history", {}).setdefault(nb, []).append({"question": text, "answer": answer})
    if str(st["asks"]) == os.environ.get("FAKE_TIMEOUT_AT"):  # seen live: the turn exists and is charged, the client gave up
        fail("Error: request timed out", 1)
    note_id = f"note-{nid_()}"
    if "save-as-note" in o:  # like the real service, a saved answer gets a title of its own, whatever --note-title says
        st.setdefault("notes", {})[note_id] = {"nb": nb, "title": f"Auto title {st['n']}", "content": answer}
    out({"answer": answer, "references": refs, "conversation_id": "conv-1", "note": {"id": note_id}})
if cmd == "history":
    for bad in ("clear", "save"):
        if bad in o:
            st["violations"].append(f"history --{bad}")
    pairs = [{"turn": k + 1, **p} for k, p in enumerate(st.get("history", {}).get(nb, []))]
    out({"notebook_id": nb, "conversation_id": "conv-1", "count": len(pairs), "qa_pairs": pairs})
if cmd == "note create":
    note_id = f"note-{nid_()}"
    title = (o.get("title") or ["New Note"])[0]
    st.setdefault("notes", {})[note_id] = {"nb": nb, "title": title, "content": pos[0] if pos else (o.get("content") or [""])[0]}
    out({"id": note_id, "notebook_id": nb, "title": title, "created": True})
if cmd == "note rename":
    if pos[0] not in st.get("notes", {}):
        fail("not found", 1)
    st["notes"][pos[0]]["title"] = pos[1]
    out({"id": pos[0], "title": pos[1]})
if cmd == "artifact list":
    out({"artifacts": [dict(a, id=k) for k, a in st["artifacts"].items() if a["nb"] == nb]})
if cmd == "artifact get-prompt":
    a = st["artifacts"].get(pos[0])
    out({"id": pos[0], "prompt": a["prompt"] if a else None})
if cmd == "note list":
    out({"notes": [{"id": k, "title": v["title"]} for k, v in st.get("notes", {}).items() if v["nb"] == nb]})
if cmd.startswith("generate "):
    kind = cmd.split()[1]
    prompt = pos[0] if pos else (o.get("append") or o.get("instructions") or [""])[0]
    if o.get("prompt-file"):
        prompt = open(o["prompt-file"][0], encoding="utf-8").read()
    aid = f"art-{nid_():03d}"
    later = "later" in o
    st["artifacts"][aid] = {"nb": nb, "type": TYPES[kind][0], "type_id": TYPES[kind][1], "title": f"{kind} {aid}",
                            "status": "in_progress" if later else "completed", "created_at": f"2026-11-17T10:{st['n']:02d}:00",
                            "prompt": prompt, "opts": {k: v for k, v in o.items() if k != "json"}}
    out({"status": "queued" if later else "completed"})
if cmd.startswith("download "):
    kind = cmd.split()[1]
    mine = {k: a for k, a in st["artifacts"].items() if a["nb"] == nb and a["type_id"] == TYPES[kind][1] and a["status"] == "completed"}
    aid = (o.get("artifact") or [None])[0] or (sorted(mine, key=lambda k: mine[k]["created_at"])[-1] if mine else None)
    if aid not in mine:
        fail(json.dumps({"error": True, "code": "NOT_FOUND", "message": f"no completed {kind} {aid}"}), 1)
    crowd = "CROWD" in mine[aid]["prompt"]
    data = {"mind-map": json.dumps(tree(9, 5) if crowd else tree(4, 2)).encode(),
            "data-table": ("﻿" + "\n".join(",".join(f"c{c}r{r}" for c in range(13 if crowd else 4)) for r in range(6))).encode(),
            "infographic": png(), "slide-deck": pdf(20 if crowd else 6), "audio": b"m4a", "video": b"mp4"}.get(
        kind, (f"# {mine[aid]['title']}\n\nPROMPT WAS: {mine[aid]['prompt']}\n"
               + ("\n```\n[A] --> [B]\n```\n" if "how the ideas relate" in mine[aid]["prompt"]
                  and "NODIAGRAM" not in mine[aid]["prompt"] else "")).encode())
    if kind in ("quiz", "flashcards") and (o.get("format") or ["json"])[0] == "json":  # the real shapes, seen 2026-11-17
        block = lambda t: {"flashcardContentBlock": [{"type": "text", "content": t}]}
        data = json.dumps({"title": "Cards", "cards": [{"front": block("What is a stock?"), "back": block("A store that builds up over time.")}]}
                          if kind == "flashcards" else {"title": "Quiz", "questions": [
            {"type": "multiple_choice", "question": "Which loop holds a room at a set temperature?", "hint": "It opposes change.",
             "answerOptions": [{"text": "A balancing loop", "isCorrect": True, "rationale": "It works against the gap."},
                               {"text": "A reinforcing loop", "isCorrect": False, "rationale": "That one amplifies."},
                               {"text": "A delay", "isCorrect": False, "rationale": "A delay is a lag."},
                               {"text": "None of the above", "isCorrect": False, "rationale": "One of them is right."}]},
            {"type": "multiple_choice", "question": "What does interest on savings show?",
             "answerOptions": [{"text": "A loop that feeds on itself", "isCorrect": True, "rationale": "More makes more."},
                               {"text": "A loop that holds steady", "isCorrect": False, "rationale": "No."},
                               {"text": "A stock with no flows", "isCorrect": False, "rationale": "No."}]},
            {"type": "multiple_choice", "question": "Why does a shower run hot then cold?",
             "answerOptions": [{"text": "The pipe adds a lag", "isCorrect": True, "rationale": "Delay."},
                               {"text": "The heater is broken", "isCorrect": False, "rationale": "No."},
                               {"text": "The drain is slow", "isCorrect": False, "rationale": "No."}]},
            {"type": "fill_in_the_blank", "question": "A quick fix that weakens the system's own ability is called ___.",
             "bestAnswer": "shifting the burden", "acceptableAnswers": ["addiction"], "rationale": "The fix replaces the system's own repair."},
            {"type": "short_answer", "question": "Why did the rent cap backfire?",
             "grading": {"modelAnswer": "Landlords' goals pulled the other way.", "rationale": "Policy resistance."}}]}).encode()
    elif kind == "flashcards":  # the real markdown export prints the raw data around the text
        data = b"## Card 1\n\n**Q:** {'flashcardContentBlock': [{'type': 'text', 'content': 'What is a stock?'}]}\n"
    elif kind == "quiz":        # ... and ticks the right answers
        data = b"## Question 1\n- [ ] A reinforcing loop\n- [x] A balancing loop\n"
    os.makedirs(os.path.dirname(os.path.abspath(pos[0])), exist_ok=True)
    open(pos[0], "wb").write(data)
    out({"artifact": {"id": aid}, "output_path": pos[0], "status": "downloaded"})
fail(f"fake: command not implemented: {cmd}")
