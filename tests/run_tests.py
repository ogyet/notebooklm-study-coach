"""Script tests against the fake CLI. Nothing here touches the real NotebookLM account.
Usage: python3 -I run_tests.py [-v]"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.abspath(os.path.join(HERE, "..", "skills", "notebooklm-study-coach", "scripts"))
VERBOSE = "-v" in sys.argv
results = []


class Box:
    """One isolated scenario: its own folder, fake state and call log."""

    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="nlmtest-")
        self.state, self.log = os.path.join(self.dir, "state.json"), os.path.join(self.dir, "calls.log")
        self.mp = os.path.join(self.dir, "topic", "manifest.json")
        os.makedirs(os.path.dirname(self.mp))

    def run(self, script, *args, **env):
        e = dict(os.environ, NOTEBOOKLM_BIN=os.path.join(HERE, "fake-notebooklm"), FAKE_STATE=self.state,
                 FAKE_LOG=self.log, LEARNING_ROOT=os.path.join(self.dir, "Learning"), NLM_RETRY_PAUSE="0", **env)
        r = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, script), *args], capture_output=True, text=True, env=e, timeout=60)
        if VERBOSE:
            print(f"--- {script} {' '.join(args)[:80]} -> {r.returncode}\n{r.stdout}{r.stderr}")
        return r.returncode, r.stdout + r.stderr

    def calls(self, *prefix):
        if not os.path.exists(self.log):
            return []
        rows = [json.loads(x) for x in open(self.log)]
        return [c for c in rows if c[:len(prefix)] == list(prefix)]

    def clear_log(self):
        open(self.log, "w").close()

    def manifest(self, data=None):
        if data is not None:
            json.dump(data, open(self.mp, "w"), indent=1)
        return json.load(open(self.mp))

    def st(self):
        return json.load(open(self.state))

    def seed(self, st):
        base = {"n": 100, "notebooks": {}, "sources": {}, "artifacts": {}, "collections": {"Existing Group": []},
                "asks": 0, "violations": [], "personas": {}}
        base.update(st)
        json.dump(base, open(self.state, "w"))

    def file(self, rel, text="x"):
        p = os.path.join(os.path.dirname(self.mp), rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(text)
        return p


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS  " if cond else "FAIL  ") + name + (f"   [{detail}]" if detail and not cond else ""))


def opt(call, flag):
    return call[call.index(flag) + 1] if flag in call else None


def after_dashes(call):
    return call[call.index("--") + 1] if "--" in call else None


# ---------- build ----------
b = Box()
b.manifest({"title": "T", "sources": [
    {"key": "a", "title": "A", "path": "/nope/missing.pdf"}, {"key": "a", "title": "Dup", "url": "ftp://x"},
    {"key": "c", "title": "No origin"}, {"key": "d", "title": "D", "text_file": "gone.md"}]})
code, out = b.run("nlm_build.py", "--manifest", b.mp)
check("build: invalid manifest is refused", code != 0 and "nothing created" in out, out)
check("build: every problem is listed", all(w in out for w in ("file not found", "duplicate key", "no origin", "url must start",
                                                              "text file not found", '"problem"')), out)
check("build: invalid manifest makes zero CLI calls", b.calls() == [])

b = Box()
pdf = b.file("book.pdf")
b.file("context.md", "- I am new to this\n- I want plain words")
b.seed({"notebooks": {"nb-old": {"title": "Old"}},
        "sources": {"keep-1": {"nb": "nb-101", "title": "Do Not Rename Me", "type": "pdf", "url": None}}})
src = [{"key": "book", "title": "The Book — Author", "path": pdf},
       {"key": "web", "title": "An Article", "url": "https://example.com/a?utm=1"},
       {"key": "yt", "title": "A Talk", "url": "https://youtu.be/abc123"},
       {"key": "me", "title": "Context about me", "text_file": "context.md"},
       {"key": "doc", "title": "Lender notes", "drive": {"file_id": "DRIVE123", "mime": "pdf"}},
       {"key": "copied", "title": "Copied Book", "copy_from": {"notebook_id": "nb-old", "source_id": "good1"}},
       {"key": "fallback", "title": "Fallback Page", "copy_from": {"notebook_id": "nb-old", "source_id": "bad1"},
        "url": "https://example.com/fallback"},
       {"key": "kept", "title": "My own name for it", "source_id": "keep-1"}]
b.manifest({"title": "Buying a Business · Due diligence", "problem": "tell whether a seller's profit is real",
            "collection": "New Group", "sources": src})
code, out = b.run("nlm_build.py", "--manifest", b.mp, "--check")
check("build --check: valid manifest passes and touches nothing", code == 0 and b.calls() == [], out)
code, out = b.run("nlm_build.py", "--manifest", b.mp, FAKE_FAIL_ADD_ONCE="1")
m, st = b.manifest(), b.st()
check("build: finishes READY", code == 0 and "READY" in out, out)
check("build: creates one notebook, title passed after --", len(b.calls("create")) == 1
      and after_dashes(b.calls("create")[0]) == "Buying a Business · Due diligence")
check("build: makes the missing collection and files the notebook", len(b.calls("collection", "create")) == 1
      and m.get("collection_added") and m["notebook_id"] in st["collections"]["New Group"])
adds = b.calls("source", "add")
types = sorted(opt(c, "--type") for c in adds)
check("build: file, link, YouTube and text each use the right type", types == ["file", "text", "url", "url", "url", "youtube"]
      or types == ["file", "file", "text", "url", "url", "youtube"], str(types))
check("build: one transient failure is retried", "add failed (try 1)" in out and all(s.get("source_id") for s in m["sources"]))
text_call = [c for c in adds if opt(c, "--type") == "text"][0]
check("build: pasted text starting with '-' goes after --", after_dashes(text_call).startswith("- I am new"))
check("build: Drive doc added with its type", [opt(c, "--mime-type") for c in b.calls("source", "add-drive")] == ["pdf"])
check("build: copies instead of uploading; failed copy falls back to its link", len(b.calls("source", "copy")) == 2
      and any("https://example.com/fallback" in c for c in adds) and "copy_from" not in m["sources"][6])
renamed = [c[2] for c in b.calls("source", "rename")]
# 5 renames, not 7: the pasted note and the Drive doc are added under their title already, so they need none
check("build: gives added sources a clean title, and the title sticks", len(renamed) == 5
      and all(s.get("renamed") and st["sources"][s["source_id"]]["title"] == s["title"] for s in m["sources"][:7]),
      str([(s["title"], st["sources"][s["source_id"]]["title"]) for s in m["sources"][:7]]))
calls = [c[:2] for c in b.calls()]
check("build: titles are set only after the sources are ready",
      min(i for i, c in enumerate(calls) if c == ["source", "rename"]) > min(i for i, c in enumerate(calls) if c == ["source", "list"]))
check("build: never renames a source that was already there", "keep-1" not in renamed
      and st["sources"]["keep-1"]["title"] == "Do Not Rename Me")
persona = st["personas"].get(m["notebook_id"], "")
check("build: sets the plain-language persona with the learner's problem", "not in sources" in persona
      and "seller's profit is real" in persona and m["persona"].get("set") and st["violations"] == [])
b.clear_log()
code, out = b.run("nlm_build.py", "--manifest", b.mp)
check("build: rerun changes nothing", code == 0 and [c[:2] for c in b.calls()] == [["source", "list"]], str(b.calls()))
st = b.st(); st["sources"][m["sources"][0]["source_id"]]["title"] = "reset-by-the-service.epub"; json.dump(st, open(b.state, "w"))
code, out = b.run("nlm_build.py", "--manifest", b.mp)
check("build: a rerun repairs a title that did not stick",
      b.st()["sources"][m["sources"][0]["source_id"]]["title"] == m["sources"][0]["title"], out)

b = Box()
b.seed({"notebooks": {"nb-live": {"title": "Existing"}}})
b.manifest({"title": "Existing", "problem": "p", "notebook_id": "nb-live", "persona": False,
            "sources": [{"key": "u", "title": "Paywalled page", "url": "https://example.com/BROKEN-paywalled"}]})
code, out = b.run("nlm_build.py", "--manifest", b.mp, "--timeout", "1")
check("build: reuse makes no new notebook and leaves the persona alone", not b.calls("create") and not b.calls("configure"))
check("build: a source that fails processing is reported, exit 1", code == 1 and "NOT READY (error)" in out, out)

# ---------- ask ----------
b = Box()
b.seed({"notebooks": {"nb-1": {"title": "N"}}, "sources": {"s1": {"nb": "nb-1", "title": "A", "type": "pdf"},
                                                           "s2": {"nb": "nb-1", "title": "B", "type": "pdf"}}})
b.manifest({"title": "N", "problem": "p", "notebook_id": "nb-1",
            "sources": [{"key": "a", "title": "A", "source_id": "s1"}, {"key": "b", "title": "B", "source_id": "s2"}],
            "questions": [
                {"id": "Q1", "phase": "problem", "text": "Present one real case without the solution.", "pause_after": True},
                {"id": "Q2", "phase": "resolve", "text": "My attempt: {attempt}. Show how the sources resolve it."},
                {"id": "Q3", "phase": "principles", "text": "- Break it down. NOCITE", "only": ["b"]},
                {"id": "Q4", "phase": "disagree", "text": "Where do they disagree? DOMINATE GAPS"},
                {"id": "Q5", "phase": "layers", "text": "Explain at three levels."}]})
code, out = b.run("nlm_ask.py", "--manifest", b.mp)
check("ask: stops after the problem case so the learner can try first", code == 4 and "PAUSE after Q1" in out
      and len(b.calls("ask")) == 1, out)
code, out = b.run("nlm_ask.py", "--manifest", b.mp)
check("ask: refuses to send a question with an unfilled {placeholder}", code == 4 and "{attempt}" in out
      and len(b.calls("ask")) == 1, out)
m = b.manifest()
m["questions"][1]["text"] = m["questions"][1]["text"].replace("{attempt}", "I would check the bank statements")
b.manifest(m)
code, out = b.run("nlm_ask.py", "--manifest", b.mp, FAKE_RATE_LIMIT_AT="4")
check("ask: stops cleanly on a rate limit and keeps earlier answers", code == 3 and b.manifest()["questions"][2]["status"] == "done"
      and b.manifest()["questions"][3].get("status") != "done", out)
code, out = b.run("nlm_ask.py", "--manifest", b.mp)
m, log = b.manifest(), b.st()["ask_log"]
check("ask: rerun finishes the rest", code == 0 and all(q["status"] == "done" for q in m["questions"]), out)
check("ask: one conversation, never --new", all(x["conv"] == ["conv-1"] for x in log[1:]) and b.st()["violations"] == []
      and not any("--new" in c for c in b.calls("ask")))
notes = b.st().get("notes", {})
check("ask: every answer saved as a note, under the title asked for", all(x["saved"] for x in log)
      and sorted(notes[q["note_id"]]["title"] for q in m["questions"])
      == ["Q1 · problem", "Q2 · resolve", "Q3 · principles", "Q4 · disagree", "Q5 · layers"],
      str([n["title"] for n in notes.values()]))
check("ask: 'only' restricts to that source", log[2]["sources"] == ["s2"] and log[0]["sources"] is None)
check("ask: adds the cite / 'not in sources' line", all("not in sources" in x["text"] for x in log))
check("ask: question starting with '-' is sent intact", log[2]["text"].startswith("- Break it down"))
flags = {q["id"]: q["flags"] for q in m["questions"]}
check("ask: flags an answer with no citations", flags["Q3"] == ["no citations"], str(flags))
check("ask: flags one source dominating, and gaps", any("dominates" in f for f in flags["Q4"])
      and any("not in sources" in f for f in flags["Q4"]) and flags["Q5"] == [], str(flags))
check("ask: local answer files written", sorted(os.listdir(os.path.join(os.path.dirname(b.mp), "answers")))
      == ["Q1.md", "Q2.md", "Q3.md", "Q4.md", "Q5.md"])

b = Box()
b.seed({"notebooks": {"nb-1": {"title": "N"}}, "sources": {"s1": {"nb": "nb-1", "title": "A", "type": "pdf"}}})
b.manifest({"title": "N", "problem": "p", "notebook_id": "nb-1", "sources": [{"key": "a", "title": "A", "source_id": "s1"}],
            "questions": [{"id": "Q1", "phase": "layers", "text": "Explain it."},
                          {"id": "Q2", "phase": "fails", "text": "When does it break?", "title": "Where it breaks"},
                          {"id": "Q3", "phase": "apply", "text": "Apply it."}]})
code, out = b.run("nlm_ask.py", "--manifest", b.mp, FAKE_TIMEOUT_AT="2")
m, st = b.manifest(), b.st()
q2 = m["questions"][1]
check("ask: an answer that arrived despite a timeout is recovered, not asked again", code == 0 and len(b.calls("ask")) == 3
      and all(q["status"] == "done" for q in m["questions"]) and any("recovered" in f for f in q2["flags"]), out)
check("ask: the recovered answer is saved locally and as a titled note",
      "Answer to: When does it break?" in open(os.path.join(os.path.dirname(b.mp), "answers", "Q2.md")).read()
      and st["notes"].get(q2.get("note_id"), {}).get("title") == "Where it breaks" and st["violations"] == [], str(q2))
code, out = b.run("nlm_ask.py", "--manifest", b.mp)
check("ask: a rerun after a recovery asks nothing", len(b.calls("ask")) == 3, out)

# ---------- artifacts ----------
def art_box(arts):
    bx = Box()
    bx.seed({"notebooks": {"nb-1": {"title": "N"}}, "sources": {"s1": {"nb": "nb-1", "title": "A", "type": "pdf"},
                                                                "s2": {"nb": "nb-1", "title": "B", "type": "pdf"}}})
    bx.manifest({"title": "N", "problem": "p", "notebook_id": "nb-1", "audience": "a new business buyer",
                 "sources": [{"key": "a", "title": "A", "source_id": "s1"}, {"key": "b", "title": "B", "source_id": "s2"}],
                 "artifacts": arts})
    return bx


b = art_box([{"id": "nofocus", "kind": "infographic", "prompt": "everything"},
             {"id": "deck", "kind": "slide-deck", "focus": "Quality of earnings"},
             {"id": "pod", "kind": "audio", "focus": "x"}, {"id": "odd", "kind": "hologram", "focus": "x"}])
code, out = b.run("nlm_artifacts.py", "--manifest", b.mp)
check("artifacts: a visual with no focus is refused", "nofocus: REFUSED" in out and '"focus"' in out, out)
check("artifacts: deck and audio refused without expensive_ok", "deck: REFUSED" in out and "pod: REFUSED" in out
      and "12%" in out, out)
check("artifacts: refusals generate nothing and exit 1", code == 1 and not [c for c in b.calls() if c[0] == "generate"])

ALL = [{"id": "map", "kind": "mind-map", "focus": "Quality of earnings"},
       {"id": "guide", "kind": "study-guide", "focus": "Quality of earnings", "only": ["a"]},
       {"id": "table", "kind": "data-table", "focus": "Three checks compared", "prompt": "Columns: check, what it shows, red flag."},
       {"id": "pic", "kind": "infographic", "focus": "The 30-day vanishing test", "only": ["b"], "options": {"style": "sketch-note"}},
       {"id": "deck", "kind": "slide-deck", "focus": "Quality of earnings", "expensive_ok": True},
       {"id": "quiz", "kind": "quiz", "focus": "Quality of earnings"},
       {"id": "cards", "kind": "flashcards"},
       {"id": "memo", "kind": "custom-report", "prompt": "- A one-page memo."},
       {"id": "post", "kind": "blog-post", "focus": "Quality of earnings"},
       {"id": "terms", "kind": "custom-report", "focus": "Quality of earnings", "prompt": "A glossary.", "diagrams": False},
       {"id": "flat", "kind": "custom-report", "focus": "Quality of earnings", "prompt": "NODIAGRAM"},
       {"id": "pod", "kind": "audio", "focus": "Quality of earnings", "expensive_ok": True},
       {"id": "rawmap", "kind": "mind-map", "focus": "x", "prompt": "EXACT WORDS", "raw": True}]
b = art_box(ALL)
code, out = b.run("nlm_artifacts.py", "--manifest", b.mp)
m, arts = b.manifest(), b.st()["artifacts"]
gen = {c[1]: c for c in b.calls() if c[0] == "generate"}
check("artifacts: all kinds generate with flags the real CLI accepts", code == 0 and len(arts) == 13
      and "No such option" not in out and "FAILED" not in out, out)
by = {a["id"]: a for a in m["artifacts"]}
sent = {k: v["sent_prompt"] for k, v in by.items()}
check("artifacts: prompts carry topic, clarity limits and audience", sent["pic"].startswith("Topic: The 30-day vanishing test. Cover only this topic.")
      and "at most 5 points" in sent["pic"] and sent["pic"].endswith("Audience: a new business buyer.")
      and "at most 3 bullets" in sent["deck"] and "at most 5 main branches" in sent["map"] and "At most 6 columns" in sent["table"])
check("artifacts: raw prompt is sent untouched", sent["rawmap"] == "EXACT WORDS")
check("artifacts: every report is asked to show how the ideas relate", all("Show how the ideas relate" in sent[k] for k in ("guide", "memo", "post", "flat"))
      and "Show how the ideas relate" not in sent["terms"] and "Show how the ideas relate" not in sent["pic"])
check("artifacts: a report with no diagram is flagged, one that opted out is not", by["flat"].get("warnings") and "CHECK: no diagram" in out
      and by["guide"].get("warnings") == [] and by["terms"].get("warnings") == [], out)
check("artifacts: light settings by default", opt(gen["slide-deck"], "--format") == "presenter" and opt(gen["slide-deck"], "--length") == "short"
      and opt(gen["infographic"], "--detail") == "concise" and opt(gen["infographic"], "--style") == "sketch-note"
      and opt(gen["flashcards"], "--quantity") == "fewer" and opt(gen["audio"], "--length") == "short")
check("artifacts: 'only' limits a visual to its own sources", opt(gen["infographic"], "-s") == "s2" and "-s" not in gen["slide-deck"])
check("artifacts: mind map sent without wait/retry flags", not any(f in c for c in b.calls("generate", "mind-map") for f in ("--wait", "--retry")))
check("artifacts: each download targets the artifact just made", all(by[k].get("artifact_id") for k in by)
      and len({by[k]["artifact_id"] for k in by}) == 13 and all("-a" in c for c in b.calls() if c[0] == "download"))
reports = {opt(c, "--format"): c for c in b.calls("generate", "report")}
check("artifacts: the four report formats use the right flags", set(reports) == {"study-guide", "blog-post", "custom"}
      and "--append" in reports["blog-post"] and "Topic: Quality of earnings" in opt(reports["blog-post"], "--append")
      and "--prompt-file" in reports["custom"] and "--append" not in reports["custom"], str(sorted(reports)))
folder = os.path.join(os.path.dirname(b.mp), "artifacts")
have = set(os.listdir(folder))
check("artifacts: files land with the right type", {"map.json", "map.md", "guide.md", "table.csv", "table.md", "pic.png", "deck.pdf",
                                                    "quiz.md", "cards.md", "memo.md", "post.md", "terms.md", "flat.md", "pod.m4a"} <= have, str(sorted(have)))
read = lambda name: open(os.path.join(folder, name), encoding="utf-8").read()
check("artifacts: the quiz file shows no answers; the key is a separate file",
      "quiz-answers.md" in have and "Which loop holds a room" in read("quiz.md") and "A balancing loop" in read("quiz.md")
      and not any(t in read("quiz.md") for t in ("[x]", "isCorrect", "shifting the burden", "Landlords", "works against the gap"))
      and all(t in read("quiz-answers.md") for t in ("A balancing loop", "shifting the burden", "addiction", "Landlords")),
      read("quiz.md")[:300] if "quiz.md" in have else "no quiz.md")
letter = lambda text, name: next(l.split(".")[0].strip("-* ") for l in read(name).splitlines() if text in l)
rights = [letter(t, "quiz.md") for t in ("A balancing loop", "A loop that feeds on itself", "The pipe adds a lag")]
check("artifacts: quiz options are shuffled, so the right answer is not always first; the key follows",
      len(set(rights)) > 1 and all(letter(t, "quiz.md") == letter(t, "quiz-answers.md")
                                   for t in ("A balancing loop", "A loop that feeds on itself", "The pipe adds a lag"))
      and read("quiz.md").split("None of the above")[0].count("\n- ") % 1 == 0
      and [l for l in read("quiz.md").split("## Question 2")[0].splitlines() if l.startswith("- ")][-1].endswith("None of the above"),
      str(rights))
check("artifacts: flashcards are plain questions and answers",
      "**Q:** What is a stock?" in read("cards.md") and "**A:** A store that builds up over time." in read("cards.md")
      and "flashcardContentBlock" not in read("cards.md"), read("cards.md")[:300])
check("artifacts: clean outputs are not flagged", all(by[k].get("crowded") == [] for k in ("map", "table", "deck")) and "CROWDED?" not in out, out)
check("artifacts: mind map outline is readable text", open(os.path.join(folder, "map.md")).read().startswith("- Topic\n  - Branch 1\n    - B1.1"))
prev = os.path.join(folder, "preview")
tools = (shutil.which("sips"), shutil.which("pdftoppm"))
check("artifacts: previews made for the picture and each slide", (not tools[0] or os.path.exists(os.path.join(prev, "pic.jpg")))
      and (not tools[1] or len([p for p in os.listdir(prev) if p.startswith("deck.slide-")]) == 6) and "LOOK AT" in out,
      str(os.listdir(prev)) if os.path.isdir(prev) else "no preview dir")
b.clear_log()
code, out = b.run("nlm_artifacts.py", "--manifest", b.mp)
check("artifacts: rerun generates nothing", code == 0 and b.calls() == [], str(b.calls()))

b = art_box([{"id": "map", "kind": "mind-map", "focus": "Finance rules, diligence, the 180-day plan and manager pay", "prompt": "CROWD"},
             {"id": "table", "kind": "data-table", "focus": "x", "prompt": "CROWD"},
             {"id": "deck", "kind": "slide-deck", "focus": "x", "prompt": "CROWD", "expensive_ok": True}])
code, out = b.run("nlm_artifacts.py", "--manifest", b.mp)
by = {a["id"]: a for a in b.manifest()["artifacts"]}
check("artifacts: warns when a focus lists several topics", "reads like several topics" in out, out)
check("artifacts: crowded mind map, table and deck are flagged", out.count("CROWDED?") == 3 and "9 main branches" in out
      and "13 columns" in out and "20 slides" in out and all(by[k]["crowded"] for k in by), out)
b.clear_log()
code, out2 = b.run("nlm_artifacts.py", "--manifest", b.mp, "--check")
check("artifacts --check: re-checks files without any CLI call", out2.count("CROWDED?") == 3 and b.calls() == [], out2)

b = art_box([{"id": "pic1", "kind": "infographic", "focus": "One"}, {"id": "pic2", "kind": "infographic", "focus": "Two"},
             {"id": "map", "kind": "mind-map", "focus": "One"}, {"id": "table", "kind": "data-table", "focus": "One"}])
code, out = b.run("nlm_artifacts.py", "--manifest", b.mp, "--later")
by = {a["id"]: a for a in b.manifest()["artifacts"]}
check("artifacts --later: pictures are queued; mind map and table still run now", by["pic1"]["status"] == by["pic2"]["status"] == "queued"
      and by["map"]["status"] == by["table"]["status"] == "done" and not any("--later" in c for c in b.calls("generate", "data-table")), out)
code, out = b.run("nlm_artifacts.py", "--manifest", b.mp)
check("artifacts --later: still-queued items wait", out.count("still queued") == 2 and len([c for c in b.calls() if c[0] == "generate"]) == 4, out)
code, out = b.run("nlm_artifacts.py", "--manifest", b.mp, FAKE_COMPLETE_ALL="1")
by = {a["id"]: a for a in b.manifest()["artifacts"]}
check("artifacts --later: finished items are fetched, one artifact each", code == 0 and by["pic1"]["status"] == by["pic2"]["status"] == "done"
      and by["pic1"]["artifact_id"] != by["pic2"]["artifact_id"] and by["pic1"]["artifact_id"] < by["pic2"]["artifact_id"], out)

b = art_box([{"id": "map", "kind": "mind-map", "focus": "x", "status": "done"}, {"id": "table", "kind": "data-table", "focus": "x", "status": "done"}])
os.makedirs(os.path.join(os.path.dirname(b.mp), "artifacts"))
shutil.copy(os.path.join(HERE, "fixtures", "real-mind-map.json"), os.path.join(os.path.dirname(b.mp), "artifacts", "map.json"))
shutil.copy(os.path.join(HERE, "fixtures", "real-table.csv"), os.path.join(os.path.dirname(b.mp), "artifacts", "table.csv"))
code, out = b.run("nlm_artifacts.py", "--manifest", b.mp, "--check")
check("artifacts --check: reads a real downloaded mind map and table", "main branches" in out and "columns x" in out
      and "13 columns" in out and "could not check" not in out, out)

# ---------- overlap, inventory ----------
b = Box()
b.seed({"notebooks": {"nb-a": {"title": "5 · Risk & Money"}, "nb-b": {"title": "Sales stuff"}},
        "sources": {"s1": {"nb": "nb-a", "title": "Antifragile_ Things That Gain - Nassim Taleb.epub", "type": "epub", "url": None},
                    "s2": {"nb": "nb-a", "title": "Finance Essentials", "type": "youtube", "url": "https://youtu.be/0x0EVSS_p4M"},
                    "s3": {"nb": "nb-b", "title": "Who Not How", "type": "pdf", "url": None}},
        "artifacts": {"art-1": {"nb": "nb-a", "type": "Report", "type_id": "report", "title": "Guide", "status": "completed",
                                "created_at": "1", "prompt": "four topics at once"}},
        "collections": {"Existing Group": ["nb-a"]}})
code, out = b.run("nlm_overlap.py", "--titles", "Antifragile", "Who", "--urls", "https://www.youtu.be/0x0EVSS_p4M/")
check("overlap: matches by title and by link, prints source ids", "-> source s1" in out and "-> source s2" in out
      and "REUSE" in out and "Who Not How" not in out and "Report" in out, out)
code, out = b.run("nlm_overlap.py", "--titles", "Nothing Like This")
check("overlap: no match says create new", "Create a new one" in out, out)
os.makedirs(os.path.join(b.dir, "Learning", "risk", "antifragility"))
json.dump({"notebook_id": "nb-a", "problem": "explain antifragility to a friend"},
          open(os.path.join(b.dir, "Learning", "risk", "antifragility", "manifest.json"), "w"))
b.clear_log()
code, out = b.run("nlm_inventory.py", "--write-index")
idx = os.path.join(b.dir, "Learning", "INDEX.md")
check("inventory: lists notebooks with group, sources and what was made", code == 0 and "group: Existing Group" in out
      and "2 sources" in out and "made: Report" in out, out)
check("inventory: index takes the purpose from the manifest", "explain antifragility to a friend" in open(idx).read())
check("inventory: read-only on the account", {c[0] if c[0] in ("list",) else " ".join(c[:2]) for c in b.calls()}
      <= {"list", "collection list", "collection notebooks", "source list", "artifact list"}, str(b.calls()))
text = open(idx).read().replace("| — | — | nb-b", "| Hand-written purpose | — | nb-b")
open(idx, "w").write(text)
code, out = b.run("nlm_inventory.py", "--write-index")
check("inventory: a purpose typed by hand survives a rerun", "Hand-written purpose" in open(idx).read(), open(idx).read())
code, out = b.run("nlm_inventory.py", "--notebook", "nb-a", "--prompts")
check("inventory: one notebook in detail, with the prompt behind each output", "source s1" in out and "<https://youtu.be/0x0EVSS_p4M>" in out
      and "asked for: four topics at once" in out, out)

bad = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(bad)}/{len(results)} passed" + (f"; FAILED: {bad}" if bad else ""))
sys.exit(1 if bad else 0)
