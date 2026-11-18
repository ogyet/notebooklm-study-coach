# notebooklm CLI cheat sheet (checked against v0.8.6)

If `notebooklm --version` shows a different version, re-check a command's `--help` before relying on a flag here. The scripts cover the common paths; use these commands directly only for what the scripts don't do.

## Operating rules

- Add `--json` to every command and parse it. Errors come back as `{error, code, message}`.
- Always pass `-n <notebook_id>`. Don't use `notebooklm use`, because a parallel job may depend on the current context.
- Partial IDs work (`-n f531c38a`), but the scripts store full IDs.
- Put `--` before free text that might start with a dash: `notebooklm ask -n NB --json -- "- my question"`.
- Login check: `notebooklm auth check --test --json` should show `status == "ok"`. If it fails, ask the user to run `notebooklm login`. Never handle their Google password.

## Read-only (safe anytime)

| Need | Command | Output |
|---|---|---|
| All notebooks | `list --json` | `notebooks[]`: `id, title, created_at, …` |
| Groups of notebooks | `collection list --json`; `collection notebooks <id\|name> --json` | `collections[]`: `id, name, notebook_count`; `notebooks[]` |
| Sources in a notebook | `source list -n NB --json` | `sources[]`: `id, title, type, url, status` |
| Studio outputs | `artifact list -n NB --json` | `artifacts[]`: `id, title, type, type_id, status, created_at` |
| What an output was asked for | `artifact get-prompt ARTIFACT_ID -n NB --json` | `prompt`; shows whether it was asked to cover several topics |
| Report formats NotebookLM suggests | `artifact suggestions -n NB --json` | a list of `title, description, prompt`; free (measured: no change in usage) |
| Notes | `note list -n NB --json` | `notes[]`: `id, title` |
| Usage | `usage --categories --json` | `active_window`; `windows[]`: `kind` (five_hour / weekly), `used_percent`. `actions[]`: `kind`, `estimated_cost_percent` |
| Check a download target | `download <kind> --dry-run -n NB --json` | which artifact would be fetched |

## Changes something (needs the user's OK)

| Need | Command | Gotchas |
|---|---|---|
| New notebook | `create --json -- "TITLE"` → `.notebook.id` | Don't pass `--use`. |
| Group a notebook | `collection create "NAME"`; `collection add "NAME" NB` | Removing a notebook from a group doesn't delete it, but leave groups alone unless asked. |
| Add a file | `source add PATH --type file --timeout 300 -n NB --json` → `.source.id` | **Always pass `--type file`:** a mistyped path is otherwise added as inline text. The title stays the filename; rename afterwards. Symlinks are rejected. |
| Add a web page | `source add URL --type url -n NB --json` | Paywalled or script-heavy pages can end in status `error`. Use another link or paste the text. |
| Add a YouTube video | `source add URL --type youtube -n NB --json` | Needs a transcript. |
| Paste text | `source add --type text --title "T" -n NB --json -- "TEXT"` | `source append SRC -` updates it in place. |
| Add a Drive doc | `source add-drive FILE_ID "TITLE" --mime-type google-doc\|google-slides\|google-sheets\|pdf -n NB --json` | Other Drive files (EPUB, DOCX) must be downloaded and added as files. |
| Find web sources | `source add-research "QUERY" --mode fast\|deep -n NB [--import-all --cited-only]` | Spends quota (fast about 0.1%, deep about 2%) and adds sources. Show the user what it found before importing. |
| Rename a source | `source rename SRC "Title — Author" -n NB --json` | Only for sources you added, and only once the source is `ready`: a rename sent while it is still processing reports success and is then lost. `nlm_build.py` renames last and checks the listing. |
| Read a conversation | `history -n NB --json --show-all` → `.qa_pairs[].question/.answer` | Read-only. **Check it before re-asking a question that timed out:** the service may have answered and charged already. `nlm_ask.py` recovers the answer from here. Never pass `--save` (creates a note) without approval. |
| Title a saved answer | `note rename NOTE_ID "Title" -n NB` | `ask --note-title` is ignored: the service titles a saved answer itself. `nlm_ask.py` renames the note afterwards. |
| Reuse a source | `source copy SRC... -n FROM_NB --to NB --json` → `.copied[].source.id` | No re-upload. |
| Wait for processing | `source wait SRC -n NB --timeout 600 --json` | Exit codes: 0 ready, 1 failed, 2 timeout. |
| Ask | `ask -n NB --json --save-as-note -t "Note title" [-c CONV] [-s SRC]... -- "Q"` | Continues the last conversation unless `-c` pins one. **Never use `--new`:** it deletes the conversation, and `--json` skips the confirmation. |
| Chat persona | `configure -n NB --persona "…"` **or** `--mode learning-guide\|concise\|detailed` | A mode can't be combined with a persona. Keep the response length on default; "shorter" cuts answers off. **A bare `configure` resets everything.** |
| Report | `generate report -n NB --format study-guide\|briefing-doc\|blog-post --append "…" [-s SRC]... --wait --timeout 900 --retry 2 --json` | Study guides are one report format. `--append` adds to the built-in prompt. |
| Custom report | `generate report -n NB --format custom --prompt-file FILE [-s SRC]... --wait --json` | `--append` has no effect with `custom`; the prompt file is the whole brief. |
| Quiz / flashcards | `generate quiz\|flashcards -n NB --difficulty medium --quantity fewer [-s SRC]... --wait --json -- "focus"` | |
| Mind map | `generate mind-map -n NB --kind interactive --instructions "…" [-s SRC]... --json` | **No `--wait`, `--retry` or `--later`** on this command; it finishes by itself. |
| Comparison table | `generate data-table -n NB [-s SRC]... --wait --json -- "columns and rows"` | No `--later`. |
| Infographic | `generate infographic -n NB --detail concise --orientation landscape [--style …] [-s SRC]... --wait --json -- "…"` | Avoid `--detail detailed`. |
| Slide deck | `generate slide-deck -n NB --format presenter --length short [-s SRC]... --wait --timeout 900 --json -- "…"` | About 12% of a five-hour window. |
| Fix one slide | `generate revise-slide -a ARTIFACT_ID --slide N -n NB --wait --json -- "what to change"` | Slides count from 0. About 0.9% each. Doesn't re-read sources. |
| Audio / video | `generate audio -n NB --format brief --length short …`; `generate video -n NB --format brief …` | About 10% each. Never `--format cinematic` (about 70%). |
| Download | `download report\|quiz\|flashcards\|mind-map\|data-table\|infographic\|slide-deck\|audio\|video OUT -n NB [-a ID \| --latest] --force --json` | Quiz and flashcards take `--format markdown`; a deck takes `--format pptx`. Mind maps come as JSON, tables as CSV. |
| Queue for later | add `--later` to `generate …` | Runs within a few hours and spares the five-hour window. |
| Question ideas | `suggest-next-steps -n NB --json` | A cross-check on your own question list. |

## Never, in this skill

`ask --new`; anything under `share`; `delete` of a notebook, source, note, artifact or collection; `source clean`; `source delete-by-title`; `label generate --scope all`; `language set`; a bare `configure`; `source fulltext`; `generate cinematic-video`.

## Costs (share of the five-hour window; check live with `usage --categories --json`)

`estimated_cost_percent` is a share of the `active_window`, which is `five_hour`. A week is roughly twenty five-hour windows (one measurement, 2026-11-17: 3.80% of five-hour was 0.18% of the week), so divide by about 20 for the weekly share.

| Action (`kind`) | Cost |
|---|---|
| Chat question (`qna`) | about 2%, measured over eight questions (the service quotes 0.05%, which is wrong) |
| Web research, fast (`fast_research`) | 0.09% |
| Mind map (`mindmap`) | 0.13% |
| Flashcards | 0.55% |
| Quiz | 0.67% |
| Slide revision (`slides_editing`) | 0.89% |
| Data table (`tables`) | 1.26% |
| Report (`reports`) | 1.39% |
| Infographic | 2.03% |
| Web research, deep (`deep_research`) | 2.08% |
| Audio overview | 9.7% |
| Video overview | 10.3% |
| Slides | 11.65% |
| Cinematic video (`breakdowns_video`) | 72.5% |

Per topic, Studio outputs only: Lite about 3% of a five-hour window, Standard about 6%, Full about 18%. The eight loop questions add about 16%. The five-hour window is the limit a batch run hits first; the weekly one is rarely the constraint.
