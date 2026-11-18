"""Build spec.json from the real CLI's --help: which options, values and positionals each command accepts.
The fake CLI validates every call against this, so a flag the real tool would reject fails the tests.
Usage: python3 -I mkspec.py   (read-only: only runs `notebooklm <cmd> --help`)"""
import json
import os
import re
import subprocess

COMMANDS = ["create", "list", "ask", "configure", "usage", "collection list", "collection create", "collection add",
            "collection notebooks", "source add", "source add-drive", "source copy", "source rename", "source list",
            "artifact list", "artifact get-prompt", "note list", "note create", "note rename", "history"] \
    + [f"{verb} {k}" for verb in ("generate", "download") for k in
       ("report", "quiz", "flashcards", "mind-map", "data-table", "infographic", "slide-deck", "audio", "video")]
spec = {}
for cmd in COMMANDS:
    text = subprocess.run(["notebooklm", *cmd.split(), "--help"], capture_output=True, text=True).stdout
    usage = re.search(r"Usage: notebooklm " + re.escape(cmd) + r" (.*?)\n\s*\n", text, re.S).group(1)
    pos = [w for w in usage.split() if w not in ("[OPTIONS]",)]
    min_pos = sum(1 for w in pos if not w.startswith("["))
    max_pos = 99 if any("..." in w for w in pos) else len(pos)
    options = {}
    for line in text.split("Options:")[-1].splitlines():
        if not re.match(r"^  -", line):
            continue
        part = re.split(r"\s{2,}", line.strip())[0]
        names = re.findall(r"(?<![\w\[|-])(-{1,2}[A-Za-z][\w-]*)", part)
        rest = part
        for n in names:
            rest = rest.replace(n, "", 1)
        rest = rest.replace(",", " ").replace("/", " ").strip()
        ch = re.search(r"\[([^\]]+)\]", rest)
        entry = {"name": max(names, key=len), "value": bool(rest), "choices": ch.group(1).split("|") if ch else None}
        for n in names:
            options[n] = entry
    spec[cmd] = {"min_pos": min_pos, "max_pos": max_pos, "options": options}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec.json")
json.dump(spec, open(out, "w"), indent=1)
print(f"{len(spec)} commands -> {out}")
