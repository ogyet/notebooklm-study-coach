---
name: notebooklm-study-coach
description: Turns any material (books, PDFs, web pages, YouTube videos, notes, Drive docs) into focused NotebookLM (Gemini Notebook) notebooks through the local `notebooklm` CLI, then teaches it in plain language. Splits a subject into separate topics with one notebook each, keeps an index of what every notebook is for, and can tidy a notebook that mixes unrelated material. Runs a cited learning loop (problem first, first principles, explain-like-I'm-five at three levels, Feynman teach-back) and builds uncluttered Studio outputs, one topic per visual, within a usage budget. Use this whenever the user wants to learn, study or understand a topic from their own material; create, organize, split or clean up NotebookLM notebooks; add sources to one; get something explained simply from their sources; or make a report, study guide, mind map, slide deck, infographic, data table, quiz or flashcards in NotebookLM, even if they don't say "NotebookLM".
allowed-tools: Bash(notebooklm list *) Bash(notebooklm usage *) Bash(notebooklm metadata *) Bash(notebooklm source list *) Bash(notebooklm artifact list *) Bash(notebooklm artifact get-prompt *) Bash(notebooklm artifact suggestions *) Bash(notebooklm note list *) Bash(notebooklm collection list *) Bash(notebooklm collection notebooks *) Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/nlm_inventory.py *) Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/nlm_overlap.py *) Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/nlm_budget.py *) Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/calibre_find.py *)
---

# NotebookLM Study Coach

Help the user understand a subject from their own material, fast, and keep what they learn. NotebookLM is where the research is collected and questioned. Where the material comes from doesn't matter: a book, a link, a video, a pasted note.

## The ideas behind it

- **One notebook, one topic.** A notebook that mixes unrelated material gives vaguer answers and cluttered visuals, because everything in it competes for attention. So a subject is first split into topics, and each topic gets its own small notebook.
- **Show how the ideas connect.** Understanding a topic means seeing which idea leads to which, so every report carries small diagrams of those relationships, placed where each idea is explained, and the first-principles answer in the loop ends with one.
- **One visual, one idea.** A graphic asked to cover four topics comes out crowded however it is styled. Crowding is fixed by narrowing what the visual is about, then by lighter settings, then by word limits.
- **Plain words first.** Say how something works before naming it, explain each term where it first appears, and use one everyday comparison. This is how every answer, guide and visual should read.
- **The learner does the remembering.** Guessing before being told, explaining it back from memory and answering quizzes are what make learning stick. Explanations and visuals make a topic easy to enter; they don't replace that work. Keep the split even when generating everything would be faster.

## Hard rules (read before running anything)

- **Approval before anything that creates, changes or spends.** Read-only steps are fine anytime: inventory, overlap, budget, `nlm_build.py --check`, `nlm_artifacts.py --check`. Show the plan and its cost, then wait for an explicit yes before `create`, `source add`/`copy`, `ask`, `generate`, `configure`, `rename`, `collection create`/`add`. The usage quota is limited and shared across all the user's notebooks.
- **Always pass `-n <notebook-id>`.** Never rely on `notebooklm use`; another job may be using the current context.
- **Never run** `ask --new` (it deletes the notebook's conversation), anything under `share`, any `delete` (notebook, source, note, artifact, collection), `source clean`, `source delete-by-title`, `label generate --scope all`, `language set`, or a bare `configure` with no flags.
- **Tidying never deletes.** It copies sources into new notebooks and leaves the original alone.
- **The largest outputs need their own yes.** A slide deck uses about 12% of a five-hour usage window (roughly half a percent of the week); audio and video about 10% each. Offer them, state the cost, and set `"expensive_ok": true` only after the user agrees. The script refuses them otherwise.
- **Copyright.** Source text stays inside the user's private notebooks. Don't use `source fulltext`, and don't paste long excerpts into chat or other tools. Summarize in your own words.
- **Privacy.** A note about the user's own situation lives in their Google account. Keep it short, use ranges instead of exact figures, and leave out other people's details. Ask before adding anything sensitive.

## Which path

| The user wants | Do this |
|---|---|
| To learn a subject or a new topic | The full workflow below |
| Something more from a notebook they already have ("explain X simply", "make me a deck") | Start at step 2 with that notebook: write one manifest holding its `notebook_id` and the `source_id`s already in it, then steps 4–11. Several visuals for one notebook go in that one manifest, each with its own `focus` and `only` |
| A mixed notebook sorted out, or all notebooks organized | Tidy mode (further down) |
| To see what they have | `nlm_inventory.py`, and offer `--write-index` |

## Workflow

The scripts are tools to run, not files to read: each prints its usage with `--help`, and the references say what they do. The `evals/` folder holds test cases for this skill and is never needed to use it.

Copy this checklist and work through it. Files live in `~/Documents/Learning/<subject>/`: a `topic-map.md`, then one folder per topic holding `manifest.json` (state for the scripts), `answers/`, `artifacts/` and `teach-back.md`. Layouts are in `references/plan-template.md`.

```
- [ ] 0. Budget check                 scripts/nlm_budget.py
- [ ] 1. Problem and topic map        references/plan-template.md
- [ ] 2. Reuse, copy or create        scripts/nlm_inventory.py, scripts/nlm_overlap.py
- [ ] 3. Sources for each topic       any type, 3-15 per topic
- [ ] 4. Learning loop questions      references/prompt-library.md
- [ ] 5. Pack and visuals             references/studio-playbook.md (one topic per visual)
- [ ] 6. USER APPROVES plan and cost
- [ ] 7. Build                        scripts/nlm_build.py
- [ ] 8. Ask the loop                 scripts/nlm_ask.py (pauses for the learner's own attempt)
- [ ] 9. Audit                        citations, gaps, verify list
- [ ] 10. Studio pack                 scripts/nlm_artifacts.py, then look at every visual
- [ ] 11. Teach-back, quiz, review dates, update the index
```

### 0. Budget check

Run `python3 -I scripts/nlm_budget.py --pack standard --topics N` to price a plan before any manifest exists, and `--manifest a.json b.json` afterwards. NotebookLM meters usage in two windows, five hours and a week, and its cost estimates are a share of the five-hour one. Per topic, the Studio outputs cost about 3% of a five-hour window for Lite, 6% for Standard and 18% for Full (the deck is 12 of those). The eight loop questions add about 16%: a chat question measures about 2%, far above the 0.05% the service quotes, and the script uses the measured figure. A week holds roughly twenty of those windows, so a Standard topic with its questions is about 22% of a five-hour window and 1% of the week. Always say which window a figure refers to. The script says STOP when the plan would pass 80% of the five-hour window or 60% of the week. When it warns, build fewer topics now, pick a smaller pack, or queue with `--later`.

### 1. Problem and topic map

**The problem.** Get one sentence: "I want to be able to …" (explain X to someone, judge Y, decide Z, do W). It doesn't have to be a decision. If the user has none, ask for one concrete question they'd like to be able to answer, because every later step uses it to decide what is relevant. Also learn their level (new to it, some background, working in it); it becomes the `audience` line in every prompt.

**The topic map.** Split the subject into 3–7 topics. A topic is the right size when all of these hold:
- it can be put as one question
- it could be explained on one page
- it can be learned from about 3–15 sources
- a picture of it needs five main ideas or fewer

A topic that fails gets split. Order topics so each one's prerequisites come first. Show the map and let the user choose which topics to build now, usually one to three. Write it to `topic-map.md`.

### 2. Reuse, copy or create

Run `python3 -I scripts/nlm_inventory.py` to see every notebook, and `scripts/nlm_overlap.py --manifest <path>` (or `--titles … --urls …`) to find where a topic's sources already live.
- **Reuse** a notebook when it is about the same topic. Holding the same sources is not enough: a mixed notebook that happens to contain the book is a place to copy from.
- **Copy, don't re-upload.** The overlap check prints source IDs. Put one in the manifest as `"copy_from": {"notebook_id": …, "source_id": …}`. A source can live in several notebooks.
- **Create** a new notebook for a new topic, named `<Subject> · <Topic>`. If the user groups notebooks, set `"collection"` to the subject's group.
- **Skip what already exists.** If a notebook already has a guide or visual on the same topic, don't make another.

### 3. Sources for each topic

A source can be a local file, a web page, a YouTube video, a pasted note, a Google Drive doc, or a copy from another notebook; the manifest fields are in `references/plan-template.md`. Aim for 3–15 per topic.
- Include one source that disagrees with the others when there is one.
- Add a short note about the learner's situation as a `text_file` when applying the ideas matters.
- For facts that go out of date (rates, rules, prices), add a current primary source or put the fact on the verify list.
- Finders are optional helpers: `scripts/calibre_find.py "terms"` for a Calibre library, and `notebooklm source add-research` for the web (it spends quota and adds sources, so it needs approval).

### 4. Learning loop questions

Write 6–8 questions from `references/prompt-library.md`, in this order:
1. **Problem first:** one real case from the sources, presented without the answer. The learner tries it. (`pause_after`)
2. **Resolve it:** how the sources solve the case, as a worked example, checked against the learner's attempt.
3. **First principles:** the few basic claims the topic rests on, and how the rest follows from them, drawn as a small diagram.
4. **Three levels:** the core ideas explained for a five-year-old, a teenager and a practitioner.
5. **Where it breaks:** when the idea fails, and the mistakes beginners make.
6. **Disagreements and gaps:** where the sources differ, and what none covers (with two or more sources).
7. **Use it** (optional): apply it to the learner's own case, or build a checklist.
8. **Teach-back:** the learner explains the topic from memory and the notebook marks what is wrong or missing. (`pause_after`, asked after the visuals)

Restrict a question to one source with `only` when asking what that author argues, or when one long source would drown out the rest. In a reused notebook that holds more than this topic, give every question `only` the topic's sources: a question with no `only` reads the whole notebook and strays off topic.

### 5. Pack and visuals

Pick a pack per topic from `references/studio-playbook.md`: **Lite** (mind map, plain guide, quiz, flashcards), **Standard** (Lite plus a comparison table and one infographic; the default), or **Full** (Standard plus one short deck). For every visual write a `focus`: the single idea it shows, in a few words. A topic with several big ideas gets several small visuals, not one large one. Give each visual `only` the sources that bear on its focus. The script adds the idea and word limits and the audience line to every prompt, so the manifest prompt only needs to say what is specific to this visual.

**Reports** are NotebookLM's written outputs: study guide, briefing doc, blog post, or a custom report you describe. The pack's plain guide is a report. Add others from the recipes in `references/studio-playbook.md` (plain explainer, glossary, FAQ, worked example, common mistakes), one topic per report, each with a `focus` and `only` its own sources. `notebooklm artifact suggestions -n <id> --json` lists the formats NotebookLM itself suggests for a notebook; it is free and read-only.

### 6. Approval

Show the user, per topic: the notebook (new or reused), the sources, the questions, the pack with each visual's focus, the cost estimate, and anything that changes an existing notebook (added sources, the chat persona). Keep the message to about one screen, roughly 400–500 words: what you found in a few lines, the plan as tables, one cost line, what changes, then the question. Assumptions, alternatives and detail go in `topic-map.md`, with one line saying they are there. A long approval message gets skimmed, and then the yes doesn't mean much. Wait for an explicit yes. Then write the manifests and run `python3 -I scripts/nlm_build.py --manifest <path> --check`.

### 7–10. Build, ask, audit, Studio pack

Each script is safe to rerun: it skips whatever the manifest already records.
- `python3 -I scripts/nlm_build.py --manifest <path>` creates the notebook, adds or copies the sources, gives the ones it added a clean title, sets the plain-language chat persona, and waits until every source is `ready`. A web page that fails to load is reported; replace it with another link or a pasted `text_file`.
- `python3 -I scripts/nlm_ask.py --manifest <path>` asks the questions in one conversation and saves each answer as a note and in `answers/`. It stops (exit 4) after a `pause_after` question. Show the learner that answer, get their own attempt, put it in the next question in place of `{attempt}`, and rerun. If they'd rather skip trying, rerun with `--no-pause` and say what they give up.
- **Audit.** Read the flags. No citations: re-ask, restricted to the relevant source. One source dominating a comparison: re-ask restricted to the missing one. "Not in sources" gaps: tell the user, and offer to add a source. Anything decision-critical that changes over time goes on a verify list.
- `python3 -I scripts/nlm_artifacts.py --manifest <path>` generates the pack and downloads it to `artifacts/`. Then **look at every visual**: open the preview images it lists, and read the mind-map outline and table it writes as markdown. For each report, check that its diagrams show how the ideas relate; the script flags a report with none. Judge them against the rubric in `references/studio-playbook.md` and fix what is crowded as described there. Tell the user plainly which ones came out clean and which didn't.

### 11. Teach-back, quiz, review, index

1. The learner explains the topic from memory in about five sentences, with nothing open. Save it to `teach-back.md`, put it into the teach-back question and run it. Go through what the notebook marked wrong or missing.
2. They take the quiz from `<id>.md`, which holds the questions only; the answers are in `<id>-answers.md`, for afterwards. Misses go back to the notebook as "explain why this answer is right".
3. Propose review dates about 2, 7 and 21 days out. Each review: redo the teach-back from memory, then the flashcards.
4. Run `python3 -I scripts/nlm_inventory.py --write-index` so `INDEX.md` says what each notebook is for.

Offer to critique their explanation. Don't write it for them.

## Tidy mode

For "this notebook is a mess" or "organize my notebooks":
1. Run `python3 -I scripts/nlm_inventory.py --notebook <id> --prompts` (or with no arguments for all). The prompts show whether past outputs were asked to cover several topics at once.
2. Group the sources into topics with the step 1 size test. For each group, check whether another notebook already covers that topic: `nlm_overlap.py` finds shared sources, and `nlm_inventory.py --notebook <id>` shows what a similar-sounding notebook really holds. Judge a notebook by its contents, not its name.
3. Propose a split: for each group, where it goes (an existing notebook, or a new `<Subject> · <Topic>`), and which sources are copied there. Say that existing notes and Studio outputs stay in the original, since they can't be moved. Say so when a new notebook would start with a single source: that is thin, and it gets better when the user adds to the topic they study first.
4. After a yes, write one manifest per destination using `copy_from`, and build. The original stays as it is. Renaming it to `Archive · …` is a separate question.
5. Update the index, then offer the learning loop for whichever topic the user cares about first.

## How to talk to the learner

Your own messages follow the same plain-language rules as the notebook (they are spelled out in `references/prompt-library.md`): the answer in one sentence first, how it works before what it's called, each term explained where it first appears, a concrete case before a general rule, one everyday comparison and where it stops being true. Summarize an answer and point to its file; don't paste it whole. Say what is unverified.

## When to stop

Stop asking when the learner can explain the topic and handle a new case. Keep to about 8 questions and one pack per topic unless asked for more. Build a few topics at a time, and finish the teach-back for one before generating the next. If notebooks keep multiplying while teach-backs stay unwritten, say so kindly and point back to the one in progress.

## Reference files (read when needed)

- `references/plan-template.md`: folder layout, `topic-map.md`, the `manifest.json` schema with every source type, `teach-back.md` and the index.
- `references/prompt-library.md`: the learning-loop question templates, the plain-language rules, and extras for decisions.
- `references/studio-playbook.md`: what each Studio output is for, the packs and their cost, how to write a focus, the crowding rubric and the fixes.
- `references/cli-cheatsheet.md`: commands, flags, JSON fields, costs and gotchas. Read before running any `notebooklm` command yourself.
- `references/technique-library.md`: why each learning technique works and how strong the evidence is.
- `references/guardrails.md`: privacy, copyright, budget, fact-checking and tidy-mode rules in detail.
