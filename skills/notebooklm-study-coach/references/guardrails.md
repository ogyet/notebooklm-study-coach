# Guardrails

## Privacy

- **A note about the learner** (their role, goals, situation) lives in their Google account once added. Keep it short, use ranges ("about $200K") instead of exact figures, and leave out account numbers, IDs and other people's personal details.
- **Personal topics** (relationships, family, faith, health) get their own notebook and their own note. Ask before adding the note, and offer to run without it.
- **Links are sources too.** Don't add a private or internal link (a company wiki, an unlisted document) without asking.
- **Never share a notebook, make it public, or export it.** That includes everything under `share` and `artifact export`.

## Copyright

- **Sources go only into the user's own private notebooks.**
- **No full-text dumps:** don't use `source fulltext`, and don't paste long passages into chat, files or other tools.
- **Summarize instead:** describe what an answer says in your own words and point to its file.
- **Local copies:** `answers/` keeps NotebookLM's answer with short cited snippets only.

## Budget

- **Check before every batch** with `nlm_budget.py`. Cost estimates are a share of the five-hour usage window; the week is about twenty times larger. STOP: the plan would pass 80% of the five-hour window or 60% of the week. WARN: within 10 points of either. Always say which window a figure refers to.
- **Packs set the default spend** per topic, as a share of a five-hour window: Lite about 3%, Standard about 6%, Full about 18% for the Studio outputs, plus about 16% for the eight loop questions.
- **Slide decks, audio and video are opt-in.** State the cost, get a yes, then set `expensive_ok`. Never cinematic video.
- **Fixes cost too.** Regenerating a picture is another 2% of a five-hour window; a new deck is another 12%. Get the focus right before generating, and ask before regenerating.
- **Spread big jobs out** with `--later`, and use `--retry 2` for rate limits. Never retry in an endless loop.

## Facts

- **Uncited means unverified.** Re-ask, or restrict the question to the relevant source.
- **"Not in sources" is a finding.** Report the gaps and offer to add a source; don't fill them from general knowledge without saying so.
- **Things that change over time** (loan terms, rates, regulations, tax rules, prices, market sizes) go on the verify list, to be checked with a current primary source or a person who does this for a living.
- **Health:** medical topics are for informed conversations with a doctor, not advice.
- **Pictures can be wrong.** Spot-check numbers on infographics and slides, and again after a slide revision.

## Tidying

- **Copy, never delete.** A split copies sources into topic notebooks. The original notebook, its notes and its outputs stay.
- **One change at a time.** Renaming the original to `Archive · …`, or moving notebooks between groups, each need their own yes.
- **Don't rename sources you didn't add.** The build script only renames what it added.
- **Don't change a reused notebook's chat settings silently.** Setting the persona on an existing notebook is part of the plan the user approves; use `"persona": false` to leave it alone.

## Learning that gets used

- **A topic is done when the learner has explained it from memory**, not when its notebook is full.
- **Finish before starting.** Build a few topics at a time and do the teach-back for one before generating the next.
- **Respect the user's own rules.** If they've set one, such as "study only after the day's work is done", follow it and remind them of it gently.
- **Watch the ratio of making to doing.** If notebooks and visuals keep growing while teach-backs stay unwritten, say so kindly and point back to the one in progress.
