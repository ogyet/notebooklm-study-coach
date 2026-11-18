# Technique library

Why each part of the learning loop is there and how strong the evidence is. Use it to decide what to keep when time or budget is short. The templates are in `prompt-library.md`.

## What the evidence supports

| Technique | Where it is in the loop | Evidence |
|---|---|---|
| **Answering from memory** (retrieval practice) | Teach-back, quiz, flashcards | Strong. Practice tests beat re-reading across many studies. |
| **Spreading reviews out** (spacing) | Review dates at about 2, 7 and 21 days | Strong. |
| **Explaining why, in your own words** (self-explanation) | Teach-back; "where it breaks" | Moderate. |
| **A short attempt before being taught** | Problem first | Moderate. A meta-analysis of 53 studies found a gain for older students and adults (it reversed for young children), and only when a clear explanation follows. Left to discover everything alone, beginners learn less. |
| **Worked examples** | Resolve it | Strong for beginners. As skill grows, have the learner try first. |
| **Comparing cases** | Compare cases; where it breaks (the near-miss case); comparison table | Moderate to strong: a meta-analysis of 57 experiments found a medium effect, largest when the learner looks for what the cases share before the principle is stated. |
| **Feynman technique** | How it works, then teach-back | Thin as a named method. Its parts hold up: people overrate how well they understand how things work, and teaching helps mainly when it is done from memory. |
| **First principles** | First principles | No studies of it as a study method. Experts do organize a field by its principles while beginners sort by surface features, which is the reason to build the skeleton early. |
| **Explain like I'm five / three levels** | Removed from the loop | No controlled evidence for it, and reading three explanations written by someone else is passive. Plain explanations still help a beginner start, so "How it works" keeps one plain explanation with one comparison and its limit. |
| **Re-reading, highlighting, summaries** | Reading the guide, listening to audio | Weak on their own. Treat them as a way in, not as the learning. |

**What this means in practice.** If only two steps fit, keep the problem-first case and the teach-back: they are the two steps where the learner does the work. If the learner skips the teach-back, say what they are giving up: the explanation will feel understood when it may not be.

## Why questions are worded the way they are

The phrasing rules in `prompt-library.md` come from tests on grounded AI models, mostly on models older than NotebookLM's current one, so trust the direction more than the size.
- **Quote first.** Asking for the supporting passages before the answer keeps answers closer to the sources. NotebookLM still attaches citations that don't quite support a claim, so a citation is a pointer to check, not proof.
- **One complete question per turn.** Across 15 models, spreading one task over several turns cost about 39% on average. Each question here is self-contained so the conversation's history matters less.
- **Neutral wording.** A user's hinted answer cut model accuracy by up to 27%, and "are you sure?" made models change 32–86% of their answers.
- **No brevity.** Asking for short answers made some models invent more.
- **One line per source on disagreements.** Models given conflicting sources tend to let one speak for all; asking them to name the kind of conflict improved how they handled it.
- **Accept "not in sources".** Asking again after "nothing relevant found" is when NotebookLM was seen to invent examples.

## Why plain words, and why the rules are strict

- **Mechanism before name.** A name with nothing behind it feels like knowledge and isn't. Saying what happens first gives the name something to attach to.
- **One comparison, with its limit.** A comparison carried too far teaches something false. Saying where it stops is what keeps a simple version honest.
- **Never simplify into a falsehood.** A plain explanation may leave things out; it may not say something untrue. That is why "How it works" ends by saying what it left out.

## Why one topic per notebook and per visual

- **Answers.** A notebook can only draw on its own sources, and unrelated sources dilute what comes back.
- **Mind maps.** Mixed material produces unrelated top-level branches. That is also a quick test: if the branches look unrelated, the notebook is mixed.
- **Pictures.** Crowding comes mostly from scope. Narrowing the topic and the sources does more than any wording about layout.
- **The opposite mistake.** One notebook per book or article loses the comparison between sources. A topic usually needs several sources, and a source can sit in several notebooks.

## Known NotebookLM failure modes to design around

- **Long sources:** answers can lean on early or prominent passages. Name the chapters in the question, and restrict to one source with `only`.
- **One source dominating:** in a comparison, one source can crowd out the rest. `nlm_ask.py` flags it; re-ask restricted to the missing one.
- **Weak citations:** spot-check cited passages. Treat an uncited answer as a guess.
- **Filling gaps:** the persona and every question say to write "not in sources". The script counts those markers so the gaps can be reported.
- **Outdated facts:** sources age. Rates, rules and prices go on the verify list.
- **Garbled text in pictures:** most common with many sources and high detail. Keep visuals narrow and concise.

## Sources for the evidence ratings

Dunlosky et al. (2013), *Improving Students' Learning With Effective Learning Techniques*; Adesope et al. (2017) on practice testing; Sinha & Kapur (2021) on problem-solving before instruction; Kirschner, Sweller & Clark (2006) on unguided discovery; Rozenblit & Keil (2002) on overrating one's understanding; Koh et al. (2018) on teaching from memory; Alfieri et al. (2013) on comparing cases; Kalyuga et al. (2003) on support that slows experts. On asking grounded models: Laban et al. (2025) on multi-turn conversations; Sharma et al. (2023) on sycophancy; Cattan et al. (2025) on conflicting sources; Hagar, Agustianto & Diakopoulos (2025) on NotebookLM's error types; Giskard's Phare benchmark on brevity. The research notes behind this file are in the skill's workspace folder (`research-v2/`).
