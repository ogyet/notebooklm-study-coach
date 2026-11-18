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
| **Comparing cases** | Disagreements; comparison table | Moderate, stronger when the principle is stated after the cases. |
| **Feynman technique** | Three levels, then teach-back | Thin as a named method. Its parts hold up: people overrate how well they understand how things work, and teaching helps mainly when it is done from memory. |
| **First principles** | First principles | No studies of it as a study method. Experts do organize a field by its principles while beginners sort by surface features, which is the reason to build the skeleton early. |
| **Explain like I'm five** | Three levels | No controlled evidence for it as such. Plain explanations help a beginner get started and can slow an expert, so drop level 1 for someone who already works in the field. |
| **Re-reading, highlighting, summaries** | Reading the guide, listening to audio | Weak on their own. Treat them as a way in, not as the learning. |

**What this means in practice.** If only two steps fit, keep the three-level explanation and the teach-back. If the learner skips the teach-back, say what they are giving up: the explanation will feel understood without being remembered.

## Why plain words, and why the rules are strict

- **Mechanism before name.** A name with nothing behind it feels like knowledge and isn't. Saying what happens first gives the name something to attach to.
- **One comparison, with its limit.** A comparison carried too far teaches something false. Saying where it stops is what keeps a simple version honest.
- **Never simplify into a falsehood.** Level 1 may leave things out; it may not say something untrue. That is why the template asks what level 1 simplified.

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

Dunlosky et al. (2013), *Improving Students' Learning With Effective Learning Techniques*; Adesope et al. (2017) on practice testing; Sinha & Kapur (2021) on problem-solving before instruction; Kirschner, Sweller & Clark (2006) on unguided discovery; Rozenblit & Keil (2002) on overrating one's understanding; Koh et al. (2018) on teaching from memory; Alfieri et al. (2013) on comparing cases; Kalyuga et al. (2003) on support that slows experts. The research notes behind this file are in the skill's workspace folder (`research-v2/`).
