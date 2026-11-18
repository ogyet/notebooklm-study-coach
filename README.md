# notebooklm-study-coach

**You own forty books you've half-read, nineteen browser tabs you swear you'll get to, and a YouTube history that looks like a cry for help. This skill turns that pile into something you can actually explain to another human being.**

## Why I built this

My research process was a mess. Sources in one place, notes in another, and the reports I'd had Claude write buried in chats I'd never find again. Every time I wanted to revisit something I'd built, I was digging through the wreckage like someone hunting for car keys in a landfill.

The other thing bothered me more. I didn't want my research to depend on Claude. A report that exists only because a chatbot felt generous one afternoon isn't research. It's a rumor.

So the research lives in NotebookLM, built from *my* sources and answered with citations. Every answer is saved as a note and as a file on my own disk, and an index says what each notebook is for. Claude does the organizing and the coaching: it splits the pile into topics, builds the notebooks, asks the questions, and keeps its hands to itself. If Claude vanished tomorrow, the notebooks and the files would still be there, and I could open any of them in three weeks without scrolling through a chat history.

## The problem

Let's be honest about how most of us "learn." We highlight. We bookmark. We dump everything into one giant notebook, sit back, and feel productive. It's the intellectual equivalent of buying a gym membership and calling yourself an athlete.

Two things go wrong, and both are boring and both are fatal.

**First, the pile.** A notebook that holds your negotiation books, a loan guide, a podcast transcript and three random PDFs doesn't get smarter. It gets mushy. Ask it a question and every source elbows in to answer. Ask it for a graphic and you get a crowded wall of tiny text with misspelled labels, like a subway map drawn by a committee.

**Second, you.** Reading about a thing and understanding a thing are different animals. Understanding is the part where you close the book, open your mouth, and find out what you actually know. It's uncomfortable. It's also the only part that works.

So this skill does something stubborn. It splits a subject into topics, builds one small, focused NotebookLM notebook for each, and then makes *you* do the remembering. It doesn't hand you a shiny summary and call it a day. It asks you to guess first. It makes you explain it back. It's a coach, not a butler.

## What it is

A [Claude Code](https://claude.com/claude-code) skill that drives Google's NotebookLM through a local command-line tool. You talk in plain words. Claude proposes a plan, shows you what it costs, and waits. Only after you say yes do a handful of small scripts touch your account.

It works on anything NotebookLM can swallow: PDFs, books from your Calibre library, web pages, YouTube videos, pasted notes, Google Drive docs.

## How a topic gets learned

1. **Say what you want to be able to do.** One sentence: "I want to be able to explain X / judge Y / decide Z." Everything else is judged against it.
2. **Split the subject.** Three to seven topics, each small enough to explain on one page. Nothing that needs the word "and" in its title.
3. **One notebook per topic.** Existing notebooks get reused and sources get *copied*, never re-uploaded or deleted. When a topic needs more sources, a cheaper model (Sonnet) goes looking: originals over summaries, the strongest credible dissent, and text NotebookLM can actually read. About five good sources to start.
4. **Eight questions, in a deliberate order, then as many as you like.** A real problem with the answer hidden, so you take a swing first. Then the worked solution. Then the few first principles it all rests on. Then a second case that looks different but works the same way. Then where it breaks, where each source stands, and what none of them cover. Every question asks NotebookLM to quote its passages first and mark what the sources don't support.
5. **A pack of Studio outputs.** Mind map, plain-language guide, quiz, flashcards, and optionally a comparison table, an infographic, a short deck. One idea per visual.
6. **Teach-back.** You explain the topic from memory, in about five sentences, with nothing open. The notebook marks what's wrong or missing. This is the moment it either sticks or it doesn't.
7. **Review dates** about 2, 7 and 21 days out, because memory is a leaky bucket and you should know it.

Answers carry citations. An uncited answer is treated as a guess. When the notebook says "not in your sources," that's a finding, not a failure, and you're told about it.

## What's on the menu

| | |
|---|---|
| **Topic map** | Splits a subject into small topics, ordered so the basics come first. |
| **Notebook build** | Creates the notebook, adds or copies sources, gives them clean titles, waits until every one is ready. |
| **Learning loop** | The eight questions, with a pause after the problem so you can attempt it. Answers saved as notes and files. |
| **Studio pack** | Lite, Standard or Full. Every visual gets one `focus` and only the sources that bear on it. |
| **Audit** | Flags missing citations, one source drowning out the rest, and facts that go stale (rates, rules, prices). |
| **Visual check** | Opens every generated visual and judges it against a crowding rubric. It tells you which ones are clean and which aren't. |
| **Tidy mode** | Sorts a messy notebook into topics by *copying* sources into new notebooks. The original is left alone. |
| **Budget** | Prices a plan against your NotebookLM usage before you spend a dime of it. |
| **Index** | Keeps an `INDEX.md` of what every notebook is for. |

## Just ask

- "I need to understand SBA loans for buying a small business. Here's a page, a video and two PDFs."
- "Set up a notebook from my books on negotiating with sellers. First call is in three weeks."
- "My 'Deep Reads' notebook is a mess. Sort it out."
- "The deck and infographic in my pricing notebook came out way too busy. Redo them so they're clear."
- "Explain the core idea of this notebook like I'm new to it."
- "What notebooks do I have, and what is each one for?"

## How it keeps its hands to itself

NotebookLM has a shared, limited usage quota, and it holds your private sources. So the rules are strict.

- **Nothing creates, changes or spends without a yes.** Read-only steps run freely. Everything else shows you the plan and the cost first.
- **Always an explicit notebook.** Every command names its notebook. It never relies on whatever happened to be "current."
- **Never deletes.** No deleting notebooks, sources, notes or collections. No sharing, ever. No `ask --new`, which would wipe a notebook's conversation.
- **Tidying copies, never moves.** The original stays exactly as it was.
- **The expensive stuff needs its own yes.** A slide deck costs about 12% of a five-hour usage window. Audio and video about 10% each. The script refuses them until you've agreed.
- **A budget brake.** The plan is flagged STOP if it would pass 80% of the five-hour window or 60% of the week.
- **Your sources stay in your notebooks.** No full-text dumps, no long excerpts pasted around. Summaries are in its own words.
- **Personal notes stay short and vague on purpose.** Ranges instead of exact figures, nobody else's details, and a question first if it's sensitive.

**These numbers are mine.** The usage percentages were measured on one account, with one version of the CLI, on one day. Treat them as a rough guide and let `nlm_budget.py` read your live usage before you trust them.

## Does it work?

It works for me: on a Mac, with `notebooklm` CLI v0.8.6. The 70 offline tests pass, and they never touch a real account; they run the scripts against a fake CLI that rejects any flag the real one wouldn't accept.

That's the honest scope. The tool it drives is **unofficial**. It automates NotebookLM from the outside, so if Google changes something, a command can break overnight. Other machines and other CLI versions should behave the same way, but I haven't tried them. This is a well-tested personal tool, not a polished product.

## Get it running

You need:

- [Claude Code](https://claude.com/claude-code), or any agent that supports [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills)
- A Google account with [NotebookLM](https://notebooklm.google.com)
- The unofficial [`notebooklm-py`](https://github.com/teng-lin/notebooklm-py) CLI, installed and logged in (`notebooklm login`). Its README has the install steps (for example, `uv tool install notebooklm-py`).
- `python3`. The scripts use only the standard library, so there's no pip step.
- Optional: [Calibre](https://calibre-ebook.com), if you want to pull books from your own library.

**As a Claude Code plugin:**
```
/plugin marketplace add ogyet/notebooklm-study-coach
/plugin install notebooklm-study-coach@notebooklm-study-coach
```

**Or as a personal skill:**
```bash
git clone https://github.com/ogyet/notebooklm-study-coach.git
```
```bash
ln -s "$PWD/notebooklm-study-coach/skills/notebooklm-study-coach" ~/.claude/skills/notebooklm-study-coach
```

Then ask Claude something like *"help me learn X from these sources."* Your work lands in `~/Documents/Learning/<subject>/`. Set `LEARNING_ROOT` if you want it somewhere else.

## What's in the skill

```
skills/notebooklm-study-coach/
  SKILL.md                 the workflow Claude follows
  references/              plan template, source-finder brief, prompt library, Studio playbook, CLI cheat sheet,
                           guardrails, and the evidence behind each learning technique
  scripts/
    nlm_budget.py          prices a plan against your usage (read-only)
    nlm_inventory.py       lists notebooks, writes INDEX.md
    nlm_overlap.py         finds where a topic's sources already live
    nlm_build.py           creates notebooks, adds or copies sources
    nlm_ask.py             runs the learning loop, saves each answer
    nlm_artifacts.py       generates Studio outputs, downloads and checks them
    calibre_find.py        read-only Calibre library search
    _nlm.py                shared helpers
  assets/                  the plain-language chat persona
  evals/                   six test prompts with graders (see below)
tests/                     offline tests and the fake CLI they run against
```

Run the tests with:

```bash
python3 -I tests/run_tests.py
```

The `evals/` are prompts for checking how Claude *behaves* with the skill. They were written against my own NotebookLM account (some mention notebooks by name), so you'd need to adapt them to run them yourself. You never need them to use the skill.

## Credits

- [notebooklm-py](https://github.com/teng-lin/notebooklm-py) by Teng Lin (MIT): the CLI this skill is built on. None of this works without it.
- The learning loop leans on research summarized in `references/technique-library.md`, including Dunlosky et al. on effective study techniques and Sinha & Kapur on trying a problem before being taught. That file also says plainly which techniques have strong evidence and which don't.

NotebookLM is a Google product. This project is not affiliated with or endorsed by Google.

## License

MIT
