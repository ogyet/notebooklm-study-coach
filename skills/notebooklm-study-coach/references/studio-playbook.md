# Studio playbook

What each NotebookLM Studio output is for, how to keep it uncluttered, and how to fix one that isn't.

## What each output is for

Costs are a share of one **five-hour usage window** (check live with `nlm_budget.py`). The week is about twenty times larger: on 2026-11-17, four visuals estimated at 6.6% moved the five-hour window by 3.8% and the week by 0.18%. So the five-hour window is the limit that matters in practice, and a figure here is roughly a twentieth of that as a share of the week. The chat estimate is wrong: the service quotes 0.05% a question, but eight questions measured on 2026-11-17 averaged 1.9% of a five-hour window (1.3% to 2.6%), one across a 29-source notebook and seven in a two-book one. A chat question costs more than a report whatever the notebook's size, and `nlm_budget.py` prices it at 2%. "Kind" is the `kind` used in the manifest.

| Output | Use it to | Kind | Cost | Downloads as |
|---|---|---|---|---|
| Mind map | See the shape of a topic and check its scope. If the main branches look unrelated, the notebook is mixed. | `mind-map` | 0.1% | JSON, plus a text outline |
| Plain guide | A first read-through in plain words, with questions at the end. A Report in study-guide format. | `study-guide` | 1.4% | Markdown |
| Comparison table | Put several sources, methods or cases side by side. | `data-table` | 1.3% | CSV, plus a markdown table |
| Infographic | One process, cycle or idea on one page. | `infographic` | 2.0% | PNG |
| Slide deck | A walk through one topic in order, a slide per idea. | `slide-deck` | 11.7% | PDF |
| Quiz | Test whether the learner can use the idea. | `quiz` | 0.7% | Markdown: questions in one file, the answer key in another |
| Flashcards | The few things worth remembering, for later reviews. | `flashcards` | 0.6% | Markdown |
| Audio overview | A first listen away from the desk. On request. | `audio` | 9.7% | M4A |
| Video overview | A narrated walk-through. On request. | `video` | 10.3% | MP4 |
| Other reports | A briefing for a decision, an article to read straight through, or any written format you describe. See Reports below. | `briefing-doc`, `blog-post`, `custom-report` | 1.4% each | Markdown |

**Order:** get oriented (mind map, plain guide), compare (table), picture it (infographic, deck), then test (quiz, flashcards). The visuals come after the questions in the loop, so the learner meets them already knowing the problem they answer.

## Reports

Reports are NotebookLM's written outputs. In Studio they sit under one button; a study guide is now one report format among several. Every report costs the same (about 1.4% of a five-hour window) and downloads as markdown.

| Format | What comes back | Kind |
|---|---|---|
| Study guide | The preset is now a quiz with an answer key, essay questions and a glossary. The script's clarity line reshapes it into idea-by-idea cards (what it is, why it matters, an everyday example, a common mistake) plus a glossary and practice questions. | `study-guide` |
| Briefing doc | Key insights and quotes, written for someone who has to decide something. | `briefing-doc` |
| Blog post | An article to read straight through. | `blog-post` |
| Create your own | Whatever structure, style and tone the prompt describes. The most useful format for learning. | `custom-report` |
| Suggested by NotebookLM | Formats it proposes from the notebook's sources, each with a ready prompt. | `custom-report` with that prompt |

**Reports must show how the ideas relate.** A list of well-explained ideas is not yet understanding; seeing which idea leads to which is. The script asks every report for a big-picture text diagram at the top, a small diagram wherever an idea has a shape, and a closing table of what depends on what. It flags a report that comes back with no diagram or table. Set `"diagrams": false` only where a diagram makes no sense, such as a glossary.

| The ideas are… | Draw |
|---|---|
| steps in order | an arrow flow: `[A] --> [B] --> [C]` |
| an order of priority | a ladder, top to bottom |
| what is visible versus what is hidden | stacked layers (the iceberg) |
| phases over time | columns, one per phase, with two or three points under each |
| two or three things side by side | a small table |
| a rule with numbers | a worked sum |
| a cycle that feeds itself | a loop with arrows |

This came from a guide that read best in testing: it had seven such diagrams, each placed where its idea was explained, while a tightly structured explainer on the same material had none. A rigid outline crowds diagrams out, so recipes say what to cover and leave the model room to draw. For a true picture of the same relationships, pair the report with a mind map (nearly free) or an infographic on the same `focus`.

**One topic per report**, as with visuals. A report asked to cover four topics is crowded in the same way a picture is. Give each report a `focus` and `only` the sources for that topic.

**Recipes for `custom-report`** (put the text in `prompt`; the script adds the topic, plain-language and audience lines):

| Report | Prompt |
|---|---|
| **Plain explainer** | Start with the problem this topic solves, in two sentences, then the big-picture diagram. Then explain each core idea, at most five, at three levels: for a five-year-old with one everyday comparison, for a teenager with the real terms, and for a practitioner with the trade-offs. Say where each comparison stops being true, and end each idea with one line on how it connects to the next. End with five 'Check yourself' questions that test whether the reader understood the ideas (not questions to ask someone else), without answers. |
| **First-principles breakdown** | List the smallest claims this topic rests on, marking each as a fact, an assumption the author makes, or a convention. Then rebuild the topic in 5 to 7 steps, each using only the steps before it. Point out any step the sources assert without justifying. |
| **Glossary** (set `"diagrams": false`) | The 12 terms a beginner must know for this topic. For each: a one-sentence plain meaning, then one sentence using it the way the sources do. Order them so each term uses only terms defined above it. |
| **Questions a beginner asks** | The 10 questions a beginner asks about this topic, in the order they would ask them. Answer each in under 80 words with one concrete example. |
| **Step by step** | The steps or events in order, one line each: when, what happens, why it matters. |
| **Worked example** | One complete worked example from the sources, step by step, with the reason for each step. Then the same steps as a blank template to fill in. |
| **Common mistakes** | The mistakes beginners make with this topic. For each: the mistake, why it is tempting, what to do instead, and a sign that you are making it. |

**Using a suggested format.** Run `notebooklm artifact suggestions -n <id> --json`. Each suggestion has a `title`, a `description` and a `prompt`. Its prompts tend to be written for executives ("strategic alignment", "leadership review"), so pick the ones aimed at learners, such as a primer or overview, and put the `prompt` into a `custom-report` artifact with a `focus`.

**What a side-by-side run showed** (one topic, same four sources, 2026-11-17):

| Format | Length | How it read |
|---|---|---|
| Plain explainer recipe, before diagrams were asked for | about 1,500 words | Plain, with four ideas at three levels, but no diagram or table: the ideas were explained one by one and never related. |
| Plain explainer recipe, with the relationship line | about 2,400 words | Same three levels, plus six small diagrams matched to each idea's shape (a flow, an iceberg, a two-column box, a worked sum, a phase flow, a ladder) and a closing table. Best first read. |
| Study guide + clarity line | about 2,300 words | Plain and fuller: seven idea cards, a comparison table, a 14-term glossary, practice questions. Best reference. |
| Suggested "Conceptual Primer", sent as suggested | about 3,300 words | Reads like a professional handbook: long sentences, many unexplained terms, and it drifted beyond the topic. Not a beginner's read unless a `focus` and the plain-language line are added. |

Each report used about 1.0% of a five-hour window against an estimate of 1.4%. Dollar figures and other facts in a report still need checking against the sources.

FAQ and Timeline used to be preset formats and were reported removed when Create your own arrived; the recipes above cover both.

**Interactive reports.** Studio's Reports now offers a Format choice: Document (text, which is what this skill makes) or Interactive, where the report recommends Studio items such as an infographic, mind map, deck, quiz or flashcards at the points where they would help, and an Add button generates each one inside the report. The CLI (v0.8.6) cannot create interactive reports, so they are made by hand in Studio. The one-topic rule still applies: select only that topic's sources first.

## Packs

| Pack | Contents | Five-hour window | Week |
|---|---|---|---|
| **Lite** | mind map, plain guide, quiz, flashcards | 3% | 0.15% |
| **Standard** (default) | Lite + one comparison table + one infographic | 6% | 0.3% |
| **Full** | Standard + one short slide deck | 18% | 0.9% |

The figures are for the Studio outputs alone. The eight loop questions add about 16% of a five-hour window (0.8% of the week) to any pack, so a Standard topic with its loop is about 22%, and three of those are a comfortable limit for one window. The deck is 12 of Full's 18 points, so about four Full packs fit in one five-hour window. Offer Full when the user wants a deck, and say what it costs. Audio and video are never part of a pack.

## One topic per visual: writing the `focus`

The `focus` is the single idea the visual shows, in ten words or fewer. The test: you can say what the picture shows in one sentence without "and".

A real example of what goes wrong. This prompt asked one infographic for four topics, and the result had about twenty points and four unexplained abbreviations:

> Beginner 101 visual infographic explaining Buy Then Build & Warren Buffett's Financial Statement Rules, Quality of Earnings (QoE) vs OPTICS Operational Diligence, the 180-Day Transition Timeline, and GM Compensation.

The same material as four visuals, each with one focus:

| Focus | Best form |
|---|---|
| What makes a business worth buying: four money signs | infographic |
| Checking past profit versus checking future operations | comparison table |
| The first 180 days after taking over | infographic (timeline) |
| Three ways to pay a manager | comparison table |

Rules of thumb:
- **Pick the form that fits the idea.** A process or timeline is an infographic. A comparison is a table. An overview or hierarchy is a mind map. A story told in order is a deck.
- **Several small visuals beat one big one.** Mind maps are nearly free, so use them freely. Each extra infographic is 2%, so choose the idea that most needs a picture.
- **Limit the sources.** Give each visual `only` the sources that bear on its focus. Fewer sources also means less garbled text.
- **Say what is specific in `prompt`.** For a table, name the columns and rows. For an infographic, name the steps or parts. Leave the limits to the script.

## What the script adds

`nlm_artifacts.py` builds each prompt as: `Topic: <focus>. Cover only this topic.` + your `prompt` + a clarity line + `Audience: <audience>.` The clarity lines:

- **Slide deck:** one idea per slide; a headline of at most 8 words and at most 3 bullets under 12 words; terms explained where they first appear; empty space; open with the problem, end with 3 takeaways.
- **Infographic:** one idea, at most 5 points; short labels, not sentences; abbreviations spelled out; one simple picture per point; empty space.
- **Mind map:** at most 5 main branches and 3 levels; short labels; nothing off-topic.
- **Data table:** at most 6 columns and 8 rows; cells under 15 words.
- **Plain guide:** plain words; for each idea what it is, why it matters, an everyday example and a common mistake; 6 short-answer questions without answers.
- **Quiz:** using the idea in a new situation, not repeating a definition; some questions built on common mistakes.
- **Flashcards:** one idea per card; only what must be remembered.

Default settings, changeable through `options`:

| Kind | Defaults | Other values |
|---|---|---|
| `slide-deck` | `format: presenter`, `length: short` | `format: detailed`, `length: default` |
| `infographic` | `detail: concise`, `orientation: landscape` | `detail: standard`; `orientation: portrait` or `square`; `style: sketch-note`, `professional`, `instructional`, `bento-grid`, `editorial`, `scientific` and others |
| `quiz` | `difficulty: medium`, `quantity: standard` | `easy`, `hard`; `fewer`, `more` |
| `flashcards` | `difficulty: medium`, `quantity: fewer` | as quiz |
| `audio` | `format: brief`, `length: short` | `deep-dive`, `critique`, `debate`; `default`, `long` |
| `video` | `format: brief` | `explainer`, `short` |

Avoid `detail: detailed` on infographics: it is where garbled text shows up most. Set `"raw": true` on an artifact only when the user wants their exact prompt sent with nothing added.

## Crowding rubric

After generating, look at each visual: the preview images the script lists, the mind-map outline and the markdown table. The script flags the countable problems (more than 6 branches, 7 columns, 10 rows, 20 words in a table cell, or 15 slides). Judge the rest by eye:

1. **One topic.** Could you title it without "and"?
2. **Five main ideas or fewer.** Count the points on an infographic and the bullets on each slide (three at most).
3. **Readable.** Every word is legible at normal size and spelled correctly. Garbled lettering fails.
4. **No unexplained terms.** Every abbreviation is spelled out somewhere on the visual.
5. **Room to breathe.** There is empty space, and decoration doesn't compete with the content.
6. **True to the sources.** Spot-check a number or two.

Tell the user which visuals pass and which don't. Don't describe a crowded visual as fine.

## Fixing a crowded output

Each fix spends quota (figures are a share of a five-hour window), so say the cost and get a yes first.

| Output | Fix | Cost |
|---|---|---|
| Mind map | Narrow the focus or the sources and make it again. | 0.1% |
| Table | Name fewer columns in the prompt and make it again. | 1.3% |
| Infographic | Split it: make one infographic per panel of the crowded one. If the layout itself breaks, try `orientation: portrait` or another `style`. | 2% each |
| Slide deck, a few bad slides | `notebooklm generate revise-slide "Cut this to one headline and two bullets" -a <artifact_id> --slide <N> -n <NB> --wait --json`. Slides count from 0. The `artifact_id` is in the manifest. | 0.9% each |
| Slide deck, wrong scope | A new deck with a narrower focus. | 12% |

To regenerate through the script, add a new artifact entry with a new `id` and the narrower focus, so the earlier file stays for comparison. A slide revision doesn't re-read the sources, so check its facts afterwards.

## Known limits

- **Slides and infographics are pictures.** Their text can't be edited afterwards.
- **The chat persona may not reach Studio outputs.** That is why the script repeats the audience and the limits in every prompt.
- **Mind-map steering is recent.** If a map ignores the branch limit, scope it with `only` instead.
- **Styles are untested here.** Which infographic style reads cleanest hasn't been compared; try `sketch-note` or `instructional` if `auto` comes out busy.
- **Queueing.** `--later` runs reports, pictures and decks within a few hours and spares the five-hour window. Mind maps and tables always run at once.
