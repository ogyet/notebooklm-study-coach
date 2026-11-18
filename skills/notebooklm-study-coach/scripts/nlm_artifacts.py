"""Generate the manifest's pending Studio outputs, download them into the topic folder, and check
each one for crowding. Resumable.

Kinds: study-guide, briefing-doc, blog-post, custom-report (the four Report formats), mind-map,
       data-table, infographic, slide-deck, quiz, flashcards, audio, video.

What the script enforces, so it does not depend on anyone remembering:
  - A visual (mind-map, data-table, infographic, slide-deck) must have a "focus": one topic per visual.
  - Every prompt gets a clarity line (idea and word limits, plain words) and the audience line.
    Set "raw": true on an artifact to send its prompt untouched.
  - Every report is asked to SHOW how its ideas relate: a big-picture text diagram, a small diagram
    wherever an idea has a shape, and a closing table of what depends on what. Set "diagrams": false
    on a report where that makes no sense (a glossary, say). A report that comes back with no
    diagram or table is flagged.
  - Light settings by default: presenter + short decks, concise infographics.
  - slide-deck, audio and video are the largest single items (about 10-12% of a five-hour usage window
    each, roughly half a percent of the week): they are refused unless
    the artifact has "expensive_ok": true (set it once the user has agreed to the cost).

Usage: python3 -I nlm_artifacts.py --manifest m.json [--only guide map] [--later] [--check]
  --later   queue generation for a few hours later (not for mind-map or data-table)
  --check   make nothing; re-run the crowding checks and previews on what is already downloaded
Exit code: 0 ok, 1 something failed or was refused, 3 stopped on a rate limit.
"""
import argparse
import csv
import json
import random
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nlm import (audience, err_text, is_rate_limited, items, load_manifest, project_dir, resolve, run,  # noqa: E402
                  run_text, save_manifest, source_ids, sources)

REPORT_FORMATS = {"study-guide": "study-guide", "briefing-doc": "briefing-doc", "blog-post": "blog-post",
                  "custom-report": "custom"}
#        kind            download cmd   file ext   word in the artifact list's type
KINDS = {"study-guide": ("report", ".md", "report"), "briefing-doc": ("report", ".md", "report"),
         "blog-post": ("report", ".md", "report"), "custom-report": ("report", ".md", "report"),
         "mind-map": ("mind-map", ".json", "mindmap"),
         "data-table": ("data-table", ".csv", "datatable"), "infographic": ("infographic", ".png", "infographic"),
         "slide-deck": ("slide-deck", ".pdf", "slidedeck"), "quiz": ("quiz", ".md", "quiz"),
         "flashcards": ("flashcards", ".md", "flashcard"), "audio": ("audio", ".m4a", "audio"),
         "video": ("video", ".mp4", "video")}
VISUALS = {"mind-map", "data-table", "infographic", "slide-deck"}
EXPENSIVE = {"slide-deck": 12, "audio": 10, "video": 10}  # rough % of a five-hour usage window
NO_LATER = {"mind-map", "data-table"}
WAIT_SECONDS = {"slide-deck": 900, "audio": 1200, "video": 1800}

CLARITY = {
    "slide-deck": "One idea per slide. Each slide has one headline of at most 8 words and at most 3 bullets of "
                  "under 12 words each. Use plain words and explain any technical term on the slide where it first "
                  "appears. Spell out abbreviations. Leave empty space; no decoration that does not explain "
                  "something. Open with the problem this topic solves and end with one slide of 3 takeaways.",
    "infographic": "Show this one idea only, with at most 5 points. Use short labels, not sentences. Plain words; "
                   "spell out every abbreviation. One simple picture per point. Leave empty space.",
    "mind-map": "Use at most 5 main branches and at most 3 levels. Short labels in plain words. Leave out anything "
                "not directly about this topic. A clear structure matters more than more branches.",
    "data-table": "At most 6 columns and 8 rows. Keep each cell under 15 words, in plain words. Spell out "
                  "abbreviations.",
    "study-guide": "Write for a beginner: plain words, short sentences, and each technical term explained where it "
                   "first appears. Cover at most five ideas. For each idea give what it is, why it matters, one "
                   "everyday example and one common mistake. End with 6 short-answer questions without answers.",
    "briefing-doc": "Write in plain words and short sentences. Explain each technical term where it first appears.",
    "blog-post": "Write it as a plain-language article for a beginner: open with the problem in two sentences, keep "
                 "paragraphs short, explain each technical term where it first appears, give one concrete example, and "
                 "end with a three-line summary.",
    "custom-report": "Write in plain words and short sentences. Explain each technical term where it first appears.",
    "quiz": "Test whether the learner can use the idea in a new situation, not whether they can repeat a "
            "definition. Build some questions on common mistakes. Plain words.",
    "flashcards": "One idea per card, in plain words. Only what the learner must remember to use this topic.",
    "audio": "Explain it the way you would to a friend with no background: plain words, one everyday comparison, "
             "and end with what to remember.",
    "video": "One idea per scene, with little text on screen. Plain words, one everyday comparison, and end with "
             "what to remember.",
}
RELATE = ("Show how the ideas relate to each other, not only what each one is. Open with one small text diagram of "
          "the big picture: boxes joined by labelled arrows, at most six boxes. Then, wherever an idea has a shape, "
          "draw it in a code block next to its explanation: an arrow flow for steps in order, a top-to-bottom ladder "
          "for an order of priority, stacked layers for what is visible versus hidden, columns for phases over time, "
          "a small table for a side-by-side comparison, a worked sum for a rule with numbers. Keep every diagram "
          "under 12 lines and 80 characters wide, with plain-word labels. Close with a short table listing each "
          "idea, which earlier idea it builds on, and which idea it leads to.")
FINISHED = ("completed", "complete", "ready", "done", "success", "succeeded", "")
LIMITS = {"branches": 6, "levels": 4, "nodes": 45, "columns": 7, "rows": 10, "cell_words": 20, "slides": 15}


def norm(s):
    return re.sub(r"[^a-z]", "", str(s or "").lower())


def existing(nid, kind):
    """Artifacts of this kind already in the notebook (read-only)."""
    j, _ = run(["artifact", "list", "--notebook", nid], timeout=180)
    word = KINDS[kind][2]
    return [x for x in items(j, "artifacts") if word in norm(x.get("type_id")) or word in norm(x.get("type"))]


def scope_args(m, art):
    keys = art.get("only") or []
    if not keys and art.get("exclude"):
        keys = [s["key"] for s in sources(m) if s["key"] not in art["exclude"]]
    out = []
    for sid in source_ids(m, keys):
        out += ["-s", sid]
    return out


def wants_diagrams(art):
    return art.get("kind") in REPORT_FORMATS and art.get("diagrams") is not False and not art.get("raw")


def build_prompt(m, art):
    if art.get("raw"):
        return art.get("prompt", "")
    parts = [f"Topic: {art['focus'].rstrip('.')}. Cover only this topic." if art.get("focus") else "",
             (art.get("prompt") or "").strip(), CLARITY.get(art["kind"], ""),
             RELATE if wants_diagrams(art) else "", f"Audience: {audience(m)}."]
    return " ".join(p for p in parts if p)


def refusal(art):
    """Why this artifact must not be generated as written, or None."""
    kind = art.get("kind")
    if kind not in KINDS:
        return f"unknown kind '{kind}'"
    if kind in VISUALS and not (art.get("focus") or "").strip():
        return 'a visual needs a "focus": the one topic it covers'
    if kind in EXPENSIVE and not art.get("expensive_ok"):
        return (f"costs about {EXPENSIVE[kind]}% of a five-hour usage window; set \"expensive_ok\": true once the "
                f"user has agreed to that")
    return None


def looks_multi_topic(focus):
    return len(re.findall(r",|;| and | & |/| plus | vs\.? ", focus or "")) >= 2


def command(m, art, nid, pdir, later):
    """(args, free_text_or_None) for the generate call."""
    kind, opts, prompt = art["kind"], art.get("options", {}), build_prompt(m, art)
    wait = [] if later else ["--wait", "--timeout", str(WAIT_SECONDS.get(kind, 600))]
    tail = scope_args(m, art) + wait + (["--later"] if later else []) + ["--retry", "2"]
    if kind in REPORT_FORMATS:
        args = ["generate", "report", "--notebook", nid, "--format", REPORT_FORMATS[kind]]
        if kind == "custom-report":
            pf = os.path.join(pdir, f".prompt-{art['id']}.md")
            with open(pf, "w", encoding="utf-8") as f:
                f.write(prompt)
            return args + ["--prompt-file", pf] + tail, None
        return args + ["--append", prompt] + tail, None
    if kind == "mind-map":  # no --wait/--retry/--later on this command; it polls by itself
        return ["generate", "mind-map", "--notebook", nid, "--kind", "interactive", "--instructions", prompt] \
            + scope_args(m, art), None
    args = ["generate", kind, "--notebook", nid]
    if kind == "quiz":
        args += ["--difficulty", opts.get("difficulty", "medium"), "--quantity", opts.get("quantity", "standard")]
    elif kind == "flashcards":
        args += ["--difficulty", opts.get("difficulty", "medium"), "--quantity", opts.get("quantity", "fewer")]
    elif kind == "slide-deck":
        args += ["--format", opts.get("format", "presenter"), "--length", opts.get("length", "short")]
    elif kind == "infographic":
        args += ["--detail", opts.get("detail", "concise"), "--orientation", opts.get("orientation", "landscape")]
        if opts.get("style"):
            args += ["--style", opts["style"]]
    elif kind == "audio":
        args += ["--format", opts.get("format", "brief"), "--length", opts.get("length", "short")]
    elif kind == "video":
        args += ["--format", opts.get("format", "brief")]
        if opts.get("style"):
            args += ["--style", opts["style"]]
    return args + tail, prompt


# ---------- crowding checks on the downloaded files ----------

def outline(node, depth=0, lines=None):
    lines = [] if lines is None else lines
    lines.append("  " * depth + "- " + str(node.get("name") or node.get("title") or node.get("label") or "?"))
    for c in node.get("children") or []:
        if isinstance(c, dict):
            outline(c, depth + 1, lines)
    return lines


def check_mind_map(path):
    tree = json.load(open(path, encoding="utf-8"))
    tree = tree[0] if isinstance(tree, list) and tree else tree
    lines = outline(tree)
    depths = [(len(x) - len(x.lstrip())) // 2 for x in lines]
    branches, levels, nodes = depths.count(1), max(depths), len(lines)
    md = os.path.splitext(path)[0] + ".md"
    with open(md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    warn = []
    if branches > LIMITS["branches"]:
        warn.append(f"{branches} main branches (asked for 5)")
    if levels > LIMITS["levels"]:
        warn.append(f"{levels} levels deep (asked for 3)")
    if nodes > LIMITS["nodes"]:
        warn.append(f"{nodes} nodes")
    return f"{branches} main branches, {levels} levels, {nodes} nodes; outline: {md}", warn, []


def check_table(path):
    rows = [r for r in csv.reader(open(path, encoding="utf-8-sig", newline="")) if any(c.strip() for c in r)]
    if not rows:
        return "empty table", ["empty"], []
    head, body = rows[0], rows[1:]
    longest = max((len(c.split()) for r in body for c in r), default=0)
    md = os.path.splitext(path)[0] + ".md"
    esc = lambda c: c.replace("|", "\\|").replace("\n", " ")  # noqa: E731
    with open(md, "w", encoding="utf-8") as f:
        f.write("| " + " | ".join(esc(c) for c in head) + " |\n|" + "---|" * len(head) + "\n")
        f.writelines("| " + " | ".join(esc(c) for c in r) + " |\n" for r in body)
    warn = []
    if len(head) > LIMITS["columns"]:
        warn.append(f"{len(head)} columns (asked for 6)")
    if len(body) > LIMITS["rows"]:
        warn.append(f"{len(body)} rows (asked for 8)")
    if longest > LIMITS["cell_words"]:
        warn.append(f"a cell has {longest} words (asked for under 15)")
    return f"{len(head)} columns x {len(body)} rows, longest cell {longest} words; table: {md}", warn, []


def check_image(path, pdir, aid):
    prev = os.path.join(pdir, "artifacts", "preview", f"{aid}.jpg")
    os.makedirs(os.path.dirname(prev), exist_ok=True)
    if shutil.which("sips"):
        subprocess.run(["sips", "-Z", "1600", "-s", "format", "jpeg", path, "--out", prev], capture_output=True)
    look = [prev] if os.path.exists(prev) else [path]
    return "image downloaded", [], look


def check_deck(path, pdir, aid):
    data = open(path, "rb").read()
    pages = len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", data))
    folder, stem = os.path.join(pdir, "artifacts", "preview"), f"{aid}.slide"
    os.makedirs(folder, exist_ok=True)
    for stale in [p for p in os.listdir(folder) if p.startswith(stem + "-")]:
        os.remove(os.path.join(folder, stale))
    look = [path]
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-jpeg", "-r", "60", path, os.path.join(folder, stem)], capture_output=True)
        made = sorted(p for p in os.listdir(folder) if p.startswith(stem + "-"))
        look = [os.path.join(folder, p) for p in made] or look
    warn = [f"{pages} slides: check it stayed on one topic"] if pages > LIMITS["slides"] else []
    return f"{pages} slides", warn, look


def check(art, out, pdir):
    """Returns (summary, warnings, files_to_look_at) for a downloaded artifact."""
    kind = art["kind"]
    try:
        if kind == "mind-map":
            return check_mind_map(out)
        if kind == "data-table":
            return check_table(out)
        if kind == "infographic":
            return check_image(out, pdir, art["id"])
        if kind == "slide-deck":
            return check_deck(out, pdir, art["id"])
        if out.endswith(".md"):
            text = open(out, encoding="utf-8").read()
            diagrams = text.count("```") // 2
            tables = len(re.findall(r"^\|[\s:|-]+\|\s*$", text, flags=re.M))
            warn = ["no diagram or table: the ideas are described but not shown in relation to each other"] \
                if wants_diagrams(art) and diagrams + tables == 0 else []
            return f"{len(text.split())} words, {diagrams} diagrams, {tables} tables", warn, []
    except (OSError, ValueError, KeyError, IndexError) as e:
        return f"could not check ({e})", [], []
    return "downloaded", [], []


def _side(side):
    """A flashcard side is a list of content blocks; keep the text."""
    blocks = side.get("flashcardContentBlock") if isinstance(side, dict) else None
    if not isinstance(blocks, list):
        return str(side or "").strip()
    return " ".join(str(b.get("content", "")).strip() for b in blocks if isinstance(b, dict)).strip()


def render_cards(data):
    lines = [f"# {data.get('title') or 'Flashcards'}", ""]
    for n, c in enumerate(data.get("cards") or [], 1):
        lines += [f"## Card {n}", "", f"**Q:** {_side(c.get('front'))}", "", f"**A:** {_side(c.get('back'))}", ""]
    return "\n".join(lines)


def render_quiz(data):
    """(questions, answer key). A quiz that shows its answers tests nothing, so the key is a separate file."""
    title = data.get("title") or "Quiz"
    qs, key = [f"# {title}", "", "Answer from memory first. The answers are in the key file next to this one.", ""], [f"# {title}: answer key", ""]
    for n, q in enumerate(data.get("questions") or [], 1):
        opts = list(q.get("answerOptions") or [])
        # The data lists the right answer first every time. A shuffle seeded by the question hides that and is the
        # same on every run; "all/none of the above" stays last, where it still makes sense.
        last = [o for o in opts if re.search(r"\b(all|none) of the above\b", str(o.get("text", "")), re.I)]
        opts = [o for o in opts if o not in last]
        random.Random(str(q.get("question", ""))).shuffle(opts)
        opts += last
        qs += [f"## Question {n}", "", str(q.get("question", "")).strip(), ""]
        key += [f"## Question {n}", ""]
        if opts:
            if q.get("type") == "multiple_select":
                qs += ["*Choose every answer that applies.*", ""]
            qs += [f"- {chr(65 + k)}. {o.get('text', '')}" for k, o in enumerate(opts)] + [""]
            for k, o in enumerate(opts):
                if o.get("isCorrect"):
                    key += [f"- **{chr(65 + k)}. {o.get('text', '')}** {o.get('rationale', '')}".rstrip()]
            key += [""]
        else:
            g = q.get("grading") if isinstance(q.get("grading"), dict) else {}
            best = q.get("bestAnswer") or g.get("modelAnswer") or q.get("answer") or ""
            qs += ["*Write your answer down before you look at the key.*", ""]
            key += [f"- **{str(best).strip()}**"]
            if q.get("acceptableAnswers"):
                key += ["- Also accepted: " + "; ".join(str(x) for x in q["acceptableAnswers"])]
            why = q.get("rationale") or g.get("rationale")
            key += ([f"- Why: {why}"] if why else []) + [""]
        if q.get("hint"):
            qs += [f"**Hint:** {q['hint']}", ""]
    return "\n".join(qs), "\n".join(key)


def fetch_quiz_or_cards(kind, out, nid, pick):
    """Download a quiz or flashcards as JSON and write the reading files ourselves. The tool's markdown export
    ticks the right answers on a quiz and prints flashcards as raw data (seen 2026-11-17, CLI 0.8.6)."""
    raw = os.path.splitext(out)[0] + ".json"
    _, dr = run(["download", KINDS[kind][0], raw, "--notebook", nid, "--force", "--format", "json"] + pick, timeout=600)
    try:
        data = json.load(open(raw, encoding="utf-8"))
        if kind == "flashcards":
            open(out, "w", encoding="utf-8").write(render_cards(data))
        else:
            questions, key = render_quiz(data)
            open(out, "w", encoding="utf-8").write(questions)
            open(os.path.splitext(out)[0] + "-answers.md", "w", encoding="utf-8").write(key)
    except (OSError, ValueError, AttributeError, TypeError):  # fall back to the tool's own markdown
        _, dr = run(["download", KINDS[kind][0], out, "--notebook", nid, "--force", "--format", "markdown"] + pick, timeout=600)
    return dr


def report(art, out, pdir, looks):
    summary, warn, look = check(art, out, pdir)
    visual = art.get("kind") in VISUALS
    art["crowded" if visual else "warnings"] = warn
    looks += [(art["id"], p) for p in look]
    print(f"{art['id']}: {summary}" + (f"\n  {'CROWDED?' if visual else 'CHECK:'} {'; '.join(warn)}" if warn else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--later", action="store_true", help="queue generation for later instead of now")
    ap.add_argument("--check", action="store_true", help="only re-check what is already downloaded")
    a = ap.parse_args()
    mp = a.manifest
    m = load_manifest(mp)
    pdir = project_dir(mp)
    arts = m.get("artifacts", [])
    todo = [x for x in arts if not a.only or x["id"] in a.only]
    looks, bad = [], 0

    def out_path(art):
        return resolve(pdir, art.get("download") or f"artifacts/{art['id']}{KINDS[art['kind']][1]}")

    if a.check:
        for art in todo:
            if art.get("kind") in KINDS and os.path.exists(out_path(art)):
                report(art, out_path(art), pdir, looks)
        save_manifest(mp, m)
    else:
        nid = m.get("notebook_id") or sys.exit("No notebook_id in manifest; run nlm_build.py first.")
        for art in todo:
            if art.get("status") == "done":
                continue
            why = refusal(art)
            if why:
                bad += 1
                print(f"{art.get('id')}: REFUSED, {why}")
                continue
            kind = art["kind"]
            if looks_multi_topic(art.get("focus")):
                print(f"{art['id']}: NOTE the focus reads like several topics; one visual per topic stays clearer")
            later = a.later and kind not in NO_LATER
            aid = None
            if art.get("status") == "queued":  # made with --later on an earlier run: find it and fetch it
                claimed = {x.get("artifact_id") for x in arts}
                new = [x for x in existing(nid, kind) if x.get("id") not in set(art.get("before_ids", []))
                       and x.get("id") not in claimed and "complet" in str(x.get("status", "")).lower()]
                if not new:
                    print(f"{art['id']}: still queued; rerun later")
                    continue
                aid = sorted(new, key=lambda x: str(x.get("created_at")))[0]["id"]
            else:
                before = {x.get("id") for x in existing(nid, kind)}
                args, text = command(m, art, nid, pdir, later)
                limit = WAIT_SECONDS.get(kind, 600) + 120
                j, r = run_text(args, text, timeout=limit) if text is not None else run(args, timeout=limit)
                status = str((j if isinstance(j, dict) else {}).get("status") or "").lower()
                if r.returncode != 0 or status in ("failed", "error"):
                    if is_rate_limited(r):
                        print(f"Rate limited at {art['id']}. Stopping; rerun later (or use --later).")
                        save_manifest(mp, m)
                        sys.exit(3)
                    bad += 1
                    print(f"{art['id']} FAILED ({status or r.returncode}): {err_text(r)[-200:]}")
                    continue
                # Record "requested" before anything else can go wrong: from here on a rerun fetches this
                # artifact instead of generating (and paying for) it a second time.
                art.update(status="queued", before_ids=sorted(x for x in before if x), sent_prompt=build_prompt(m, art))
                save_manifest(mp, m)
                if later or status not in FINISHED:
                    print(f"{art['id']}: " + ("queued for later" if later else f"not finished yet ({status})")
                          + "; rerun this script afterwards to download it")
                    continue
                new = [x for x in existing(nid, kind) if x.get("id") not in before]
                aid = sorted(new, key=lambda x: str(x.get("created_at")))[-1]["id"] if new else None
            art.update(status="done", artifact_id=aid)
            save_manifest(mp, m)
            out = out_path(art)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            pick = ["-a", aid] if aid else ["--latest"]
            if kind in ("quiz", "flashcards"):
                dr = fetch_quiz_or_cards(kind, out, nid, pick)
            else:
                _, dr = run(["download", KINDS[kind][0], out, "--notebook", nid, "--force"] + pick, timeout=600)
            art["downloaded"] = os.path.exists(out)
            if not art["downloaded"]:
                bad += 1
                print(f"{art['id']}: generated, but the download failed: {err_text(dr)[-150:]}")
            else:
                report(art, out, pdir, looks)
            save_manifest(mp, m)

    if looks:
        print("LOOK AT these and judge them against the crowding rubric in references/studio-playbook.md:")
        for aid, p in looks:
            print(f"  {aid}: {p}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
