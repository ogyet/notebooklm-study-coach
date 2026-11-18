# Source finder brief

Finding sources is search work, not judgment work, so hand it to a cheaper model. In Claude Code, start a subagent with the Agent tool and `model: "sonnet"`, and give it the brief below with the blanks filled in. Run one finder per topic, in parallel when there are several. Where subagents aren't available, follow the brief yourself.

The finder only searches and reads. It never runs a `notebooklm` command and never downloads files. You check its list and put the sources in the plan; adding them still needs the user's yes.

## The brief

> Find sources for a NotebookLM notebook. NotebookLM will answer questions only from these sources, so they decide how good the answers are.
>
> Topic, as a question: {topic question}
> What the learner wants to be able to do: {problem}
> Their level: {new to it | some background | working in it}
> They already have: {sources the user gave, or "nothing"}
> {If they use Calibre: "Search their library first: `python3 -I <skill dir>/scripts/calibre_find.py "terms"`."}
>
> Find up to 8 candidates so that, with what they already have, the topic has about 5 strong sources. Prefer, in this order:
> 1. The original over anything that summarizes it (the paper over the news story, the book over the blog review).
> 2. For a factual or scientific topic: a review, guideline or official page, then a single study, then an explainer, then opinion.
> 3. One well-regarded book, lecture or long article that explains the foundations, for a learner who is new to it.
> 4. The strongest credible source that disagrees with the rest, on the same question. Skip it if there is none.
> 5. For facts that change (prices, rates, rules, tools), a source from the last one or two years.
>
> NotebookLM must be able to read it: a web page with its text on the page (not paywalled), a PDF with real text (not a scan), a YouTube video with captions. Prefer a written version of a talk when one exists.
>
> For each source you don't recognize, run one search about who is behind it (author, publisher, funding) instead of trusting the page's own description.
>
> Drop: a second copy or edition of the same work (keep one), articles that only repeat another source on the list, listicles, and AI-written summaries.
>
> Stop searching when two more candidates in a row add nothing new. Use at most 15 searches.
>
> Reply with one table, nothing else before it: title — author or publisher | link or local path | type (web, PDF, YouTube, book) | role (foundation, evidence, explainer, dissent, current facts) | why it is in, in one line | what the check found | date. Under the table, one line on anything you couldn't find.

## Checking what comes back

Read the table before it goes into the plan:
- Drop a candidate the check flagged, or one that answers a different question.
- If two sources would answer the same question differently because they are different editions, or a summary sits next to its original, keep one.
- Open any link the plan depends on to confirm it loads.

NotebookLM's own web search (`notebooklm source add-research`, fast mode about 0.1% of a five-hour window) is another way to find sources. It adds what it finds straight to a notebook, so it needs approval first.
