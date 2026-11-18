"""Shared helpers for the notebooklm-study-coach scripts (python3 stdlib only)."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata

CLI = os.environ.get("NOTEBOOKLM_BIN", "notebooklm")
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_AUDIENCE = "a smart beginner who has never studied this field"
PAUSE = float(os.environ.get("NLM_RETRY_PAUSE", "10"))  # seconds between retries and status polls


def run(args, timeout=600):
    """Run `notebooklm <args> --json`. Returns (parsed_json_or_None, CompletedProcess)."""
    if "--json" not in args:
        args = [*args, "--json"]
    try:
        r = subprocess.run([CLI, *args], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        return None, subprocess.CompletedProcess(e.cmd, 124, "", f"timeout after {timeout}s")
    out = r.stdout or ""
    starts = [i for i in (out.find("{"), out.find("[")) if i >= 0]
    if not starts:
        return None, r
    try:
        return json.loads(out[min(starts):]), r
    except ValueError:
        return None, r


def run_text(args, text, timeout=600):
    """Like run(), for commands that end in free text (a question, a prompt, pasted source text).
    The `--` stops a text that starts with "-" (a markdown bullet, say) being read as an option."""
    return run([*args, "--json", "--", text], timeout=timeout)


def err_text(r):
    return ((r.stderr or "") + (r.stdout or ""))[-400:].strip()


def is_rate_limited(r):
    t = err_text(r).lower()
    return any(k in t for k in ("rate limit", "rate-limit", "429", "quota", "too many requests", "exhausted"))


def items(j, key):
    """Pull a list out of a CLI JSON response that may be {key: [...]} or a bare list."""
    if isinstance(j, list):
        return j
    if isinstance(j, dict):
        v = j.get(key)
        return v if isinstance(v, list) else []
    return []


def new_id(j, key="source"):
    """The id of the thing a command just made: {key: {id}} or a bare {id}."""
    if not isinstance(j, dict):
        return None
    inner = j.get(key)
    return (inner.get("id") if isinstance(inner, dict) else None) or j.get("id") or j.get(f"{key}_id")


def load_manifest(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_manifest(path, data):
    """Atomic write so an interrupted run never corrupts the manifest."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".manifest.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def project_dir(manifest_path):
    return os.path.dirname(os.path.abspath(manifest_path))


def resolve(pdir, p):
    """A manifest path: absolute, ~-relative, or relative to the topic folder."""
    p = os.path.expanduser(p or "")
    return p if os.path.isabs(p) else os.path.join(pdir, p)


def learning_root():
    return os.path.expanduser(os.environ.get("LEARNING_ROOT", "~/Documents/Learning"))


def sources(m):
    """Every source entry. (Version 1 manifests kept pasted notes in a separate "context" list.)"""
    return m.get("context", []) + m.get("sources", [])


def source_ids(manifest, keys):
    """Translate source keys to NotebookLM source IDs, skipping unknown or not-yet-added ones."""
    by_key = {s.get("key"): s.get("source_id") for s in sources(manifest)}
    return [by_key[k] for k in keys if by_key.get(k)]


def audience(m):
    return m.get("audience") or DEFAULT_AUDIENCE


def is_youtube(url):
    return bool(re.match(r"https?://(www\.|m\.)?(youtube\.com|youtu\.be)/", url or ""))


def norm_title(s):
    """Loose title key: ascii, lowercase, no punctuation, no leading article, first 6 words."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\.(epub|pdf|txt|md|docx|azw3|mobi|pptx|csv)$", "", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s.replace("'", "").replace("’", ""))
    s = re.sub(r"^(the|a|an) ", "", re.sub(r"\s+", " ", s).strip())
    return " ".join(s.split()[:6])


def norm_url(u):
    """Loose URL key: no scheme, no www, no query string, no trailing slash."""
    u = re.sub(r"^https?://(www\.)?", "", (u or "").strip().lower())
    return u.split("#")[0].split("?")[0].rstrip("/") if "youtu" not in u else u.split("#")[0].rstrip("/")


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)
