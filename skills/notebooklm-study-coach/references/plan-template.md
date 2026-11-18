# Plan template: folders, topic map, manifest, teach-back, index

## Folders

```
~/Documents/Learning/
  INDEX.md                      one line per notebook: what it is for (written by nlm_inventory.py --write-index)
  <subject>/                    for example buying-a-business/
    topic-map.md                the problem and the topics
    <topic>/                    for example checking-the-numbers/
      manifest.json             state for the scripts; safe to rerun from
      context.md                optional short note about the learner's situation
      answers/Q1.md …           local copy of each answer (written by nlm_ask.py)
      artifacts/                downloaded guide, map, table, pictures, quiz, cards
      artifacts/preview/        small images of pictures and slides, for checking
      teach-back.md             written by the LEARNER, from memory
```

Set `LEARNING_ROOT` to use a different root folder.

## topic-map.md

```markdown
# <Subject>

**I want to be able to:** <one sentence>
**My level:** <new to it | some background | working in it>

| # | Topic (as a question) | Needs first | Sources so far | Notebook | Status |
|---|---|---|---|---|---|
| 1 | How do I tell if a seller's profit is real? | — | 4 | new | build now |
| 2 | What breaks in the first 180 days? | 1 | 6 | reuse: 2. Buy Then Build | later |

**Not covering:** <what was left out on purpose>
**Verify with a current source or a person:** <facts that go out of date>
```

A topic is the right size when it can be put as one question, explained on one page, learned from about 3–15 sources, and drawn with five main ideas or fewer.

## manifest.json

One per topic notebook.

```json
{
  "subject": "Buying a business",
  "topic": "Checking the seller's numbers",
  "title": "Buying a Business · Checking the seller's numbers",
  "problem": "tell within a week whether a seller's stated profit is real",
  "audience": "a first-time buyer with no accounting background",
  "collection": "ETA & HoldCo Mastery",
  "notebook_id": null,
  "conversation_id": null,
  "sources": [
    {"key": "book", "title": "Buy Then Build — Walker Deibel", "path": "/Users/<you>/Books/buy-then-build.epub"},
    {"key": "article", "title": "What Buyers Get Wrong About Working Capital", "url": "https://example.com/working-capital"},
    {"key": "talk", "title": "Finance Essentials Before You Close", "url": "https://youtu.be/XXXXXXXXXXX"},
    {"key": "me", "title": "Context about me", "text_file": "context.md"},
    {"key": "lender", "title": "Lender checklist", "drive": {"file_id": "<drive file id>", "mime": "pdf"}},
    {"key": "buffett", "title": "Warren Buffett and the Interpretation of Financial Statements",
     "copy_from": {"notebook_id": "<notebook that has it>", "source_id": "<its source id>"},
     "path": "<optional local file, used only if the copy fails>"},
    {"key": "already", "title": "A source that is already in this notebook", "source_id": "<its id>"}
  ],
  "questions": [
    {"id": "Q1", "phase": "problem", "pause_after": true, "text": "I want to be able to … do not give the solution …"},
    {"id": "Q2", "phase": "resolve", "text": "Here is my attempt at that case: {attempt}. Using only the sources, show step by step …"},
    {"id": "Q3", "phase": "principles", "text": "Break … down to the smallest claims it rests on …"},
    {"id": "Q4", "phase": "layers", "text": "Explain … at three levels …", "only": ["book"]},
    {"id": "Q8", "phase": "teachback", "text": "Here is my explanation of …, written from memory: {my explanation}. …"}
  ],
  "pack": "standard",
  "artifacts": [
    {"id": "map", "kind": "mind-map", "focus": "How to tell if a seller's profit is real"},
    {"id": "guide", "kind": "study-guide", "focus": "How to tell if a seller's profit is real"},
    {"id": "table", "kind": "data-table", "focus": "Three checks on a seller's numbers",
     "prompt": "Columns: the check, what it shows, a red flag. One row per check."},
    {"id": "pic", "kind": "infographic", "focus": "Where reported profit and real cash differ", "only": ["book", "article"]},
    {"id": "quiz", "kind": "quiz", "focus": "Spotting profit that isn't real"},
    {"id": "cards", "kind": "flashcards", "focus": "Terms a buyer must know to read the numbers"},
    {"id": "deck", "kind": "slide-deck", "focus": "How to tell if a seller's profit is real", "expensive_ok": false}
  ],
  "budget": {"weekly_max_used": 60, "five_hour_max_used": 80}
}
```

### Sources: one origin each

| Field | What it is | How it is added |
|---|---|---|
| `path` | A local file: PDF, EPUB, DOCX, TXT, MD and similar | Uploaded |
| `url` | A web page or a YouTube link | Added by link; YouTube is detected from the address |
| `text_file` | A local text or markdown file, absolute or relative to the topic folder | Pasted as a text source under `title` |
| `drive` | `{"file_id": …, "mime": "google-doc" \| "google-slides" \| "google-sheets" \| "pdf"}` | Linked from Google Drive |
| `copy_from` | `{"notebook_id": …, "source_id": …}` from `nlm_overlap.py` | Copied from another notebook; falls back to `path` or `url` if given |
| `source_id` | The ID of something already in the notebook | Left as it is, never renamed |

Every source needs a unique `key` (used by `only` and `exclude`) and a `title`. Sources the script adds are renamed to `title`.

### Other fields

- **`problem`** (required): what the learner wants to be able to do. It goes into the chat persona and into your questions.
- **`audience`**: who the explanations are for. Default: "a smart beginner who has never studied this field".
- **`collection`**: a NotebookLM group to file the notebook under. Created if missing. Leave it out if the user doesn't group notebooks.
- **`notebook_id`**: `null` to create a notebook; an existing ID to reuse one.
- **`persona`**: leave out to set the plain-language persona. Use `{"file": "my-persona.txt"}` for a custom one, or `false` to leave a reused notebook's chat settings alone.
- **`pack`**: a label for the plan (`lite`, `standard`, `full`). The scripts generate whatever is in `artifacts`; the label is for the reader.
- **`questions[].pause_after`**: stop after this question so the learner can make their own attempt.
- **`questions[].only`**: source keys to restrict the question to. Empty means all sources.
- **`artifacts[].kind`**: `study-guide`, `briefing-doc`, `blog-post`, `custom-report` (the report formats), `mind-map`, `data-table`, `infographic`, `slide-deck`, `quiz`, `flashcards`, `audio`, `video`.
- **`artifacts[].focus`**: the one idea an output covers. Required for `mind-map`, `data-table`, `infographic` and `slide-deck`, and recommended for every report.
- **`artifacts[].only` / `exclude`**: source keys the output may use.
- **`artifacts[].options`**: settings such as `{"style": "sketch-note"}`; see `studio-playbook.md`.
- **`artifacts[].expensive_ok`**: must be `true` for `slide-deck`, `audio` and `video`, and only after the user agreed to the cost.
- **`artifacts[].diagrams`**: `false` stops the script asking a report for relationship diagrams. Leave it out for explainers and guides.
- **`artifacts[].raw`**: `true` sends `prompt` exactly as written, with no limits added.
- **What the scripts fill in:** `source_id`, `added_here`, `renamed`, `collection_added`, `conversation_id`, question `status`, `citations`, `flags`, `gaps`, artifact `status`, `artifact_id`, `sent_prompt`, `crowded` (visuals), `warnings` (reports), `downloaded`. Don't edit these by hand unless fixing a known problem.

### Starting from a notebook that already exists

Set `notebook_id` to its ID, list the sources you need with their `source_id` (from `notebooklm source list -n <id> --json`), and set `"persona": false` unless the user wants the plain-language persona applied to that notebook's chat.

## teach-back.md (the learner writes this)

```markdown
# <Topic>: explained from memory, <date>

**In one sentence:** …
**How it works (about five sentences, my own words):** …
**An example:** …
**When it doesn't work:** …
**What I'm still unsure about:** …

## What the notebook marked (filled in after question 8)
- Wrong: …
- Missing: …
- Re-read: …

**Review dates:** <+2 days> · <+7 days> · <+21 days>
```

## INDEX.md

Written by `python3 -I scripts/nlm_inventory.py --write-index`. One row per notebook: name, group, number of sources, purpose, what has been made, short ID. The purpose comes from the manifest's `problem`. A purpose typed into the file by hand is kept on later runs, so notebooks made outside this skill can be described there.
