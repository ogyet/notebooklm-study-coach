"""List any command in a run's commands.txt that would create, change or spend on the NotebookLM account."""
import re
import sys

BAD = [r"notebooklm\s+(create|ask|configure|delete|rename|use|clear|share|copy)\b",
       r"notebooklm\s+source\s+(add|add-drive|add-research|add-async|add-book|copy|rename|delete|clean|append|refresh)\b",
       r"notebooklm\s+generate\b", r"notebooklm\s+collection\s+(create|add|remove|delete|rename)\b",
       r"notebooklm\s+(note|artifact|label)\s+(create|delete|rename|save|copy|retry|export|generate|add|remove)\b",
       r"nlm_ask\.py", r"--write-index"]
hits = []
for n, line in enumerate(open(sys.argv[1], encoding="utf-8"), 1):
    for part in re.split(r"&&|;|\|", line):
        ran = "python3" in part or "notebooklm " in part  # reading a script's source is not running it
        if ran and any(re.search(b, part) for b in BAD):
            hits.append((n, part.strip()[:160]))
        if "python3" in part and re.search(r"nlm_(build|artifacts)\.py", part) and "--check" not in line:
            hits.append((n, "NO --check: " + part.strip()[:140]))
print(f"{sys.argv[1].split('iteration-2/')[-1]}: " + ("CLEAN" if not hits else f"{len(hits)} suspect"))
for h in hits:
    print("   line", *h)
