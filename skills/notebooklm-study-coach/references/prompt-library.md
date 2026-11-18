# Prompt library

How to word a question for NotebookLM, the loop's question templates, more questions to keep asking, and the plain-language rules.

**Placeholders.** Fill these in when writing the manifest: `{topic}`, `{problem}` (what the learner wants to be able to do), `{concept}`, `{my situation}`, `{deliverable}`. Leave `{attempt}`, `{the first case}` and `{my explanation}` exactly as written: `nlm_ask.py` refuses to send a question that still holds a placeholder, and that refusal is what gives the learner their turn. After question 1, fill `{attempt}` with the learner's attempt and `{the first case}` with a one-line description of the case it showed.

**Added for you.** The script appends this to every question that doesn't already mention "not in sources": *"Take every fact from the selected sources; use earlier answers in this chat only to know which case or idea I mean. Start by quoting the 2 to 4 passages that matter most, one sentence each, then answer from them. Mark any step or claim the sources do not support as [not in sources] instead of filling the gap."*

## Phrasing rules

1. **Complete on its own.** Name the topic and the case in every question; never "the above" or "that idea". NotebookLM searches the sources afresh for each question, and the words of the question are what it searches with.
2. **One thing per question.** Two needs make two questions. Packing several asks into one turn lowers the quality of each answer.
3. **The sources' own words.** Call things what the sources call them. A synonym they never use can miss the passage that answers it.
4. **Neutral.** Don't state a preference or a belief, and don't build a claim into the question: "why does X work?" assumes it does; ask "does X work, and when?". Models lean toward the answer a question hints at.
5. **No request for brevity.** "Be brief" and word caps make answers drop foundations and invent more. Cap the number of items instead ("at most five").
6. **Principle first on hard questions.** When a question is hard, ask first for the general idea that governs it, then for the specifics.
7. **Take "not in sources" for an answer.** Don't ask the same thing again in other words: repeated asking is when NotebookLM starts inventing. Add a source, or ask something else.
8. **Doubt with a passage, not a push.** To check an answer, ask "which passage supports …?". Never "are you sure?": models change correct answers under pushback.
9. **A question for the learner is phrased as a question** ("Why does … ?"), not a command.

## The loop

### 1. Problem first (`"phase": "problem", "pause_after": true`)

> I want to be able to {problem}. Using only the sources, choose one real case or example that shows this problem. Describe the situation in plain words in under 150 words, then stop: do not give the solution, the outcome, or the name of the idea that solves it. End by asking me what I would do. If the sources hold no suitable case, say so and build the closest scenario you can from what they do contain, marked as constructed.

*Why:* a short attempt before being told shows the learner what they don't know and makes the explanation stick. Keep it short and follow it with a clear explanation. For a learner with no background, keep the guess to a minute: a quick wrong guess still helps, a long struggle doesn't.

### 2. Resolve it (`"phase": "resolve"`)

> Here is my attempt at the case you described: {attempt}. Using only the sources, show how they resolve it as a numbered chain: what happens, what that causes, and why. Then say what my attempt got right, what it missed, and why the missed part matters. Introduce only the ideas the solution needs, one plain sentence each, and name each idea after explaining it.

### 3. First principles (`"phase": "principles"`)

> Break {topic} down to the smallest claims it rests on, using only the sources. For each claim say whether it is a fact or definition, an assumption the author makes, or a convention people follow, and where it appears. Say which single claim, if it were false, would bring down the most of the rest. Then rebuild {topic} in 5 to 7 plain steps, each using only the steps before it. Point out any step the sources assert without justifying. End with a text diagram in a code block, at most 20 lines with one line per step, showing which step depends on which.

*Why:* details are easier to hold once there is a skeleton, and sorting facts from assumptions shows which advice is solid and which is one author's taste.

### 4. Compare cases (`"phase": "compare"`)

> In the sources on {topic}, is there a second case that looks different from {the first case} on the surface but works by the same principle? Describe it in plain words. What do the two cases share, and which surface details should I ignore? Only then state the shared principle in one sentence, and say where in the sources it comes from. If the sources hold no such case, say so and build one from what they contain, marked as constructed.

*Why:* seeing one principle at work in two different-looking cases is what lets a learner spot it in a third. It has much better evidence than explaining at several levels. Fill `{the first case}` with a short description of the case from question 1.

### 5. Where it breaks (`"phase": "fails"`)

> According to the sources, when does {concept} stop working? Give the conditions, and a sign I would notice in practice. Describe a case that looks almost the same as one where it works but ends differently, and name the single factor that decides it. Then list the 3 to 5 mistakes a beginner most often makes with it, each as: the mistake, why it is tempting, and what to do instead.

### 6. Disagreements and gaps (`"phase": "disagree"`, with two or more sources)

> On {topic}, what does each selected source say? Give each one's position in one line with a short quote, or write "silent" if it doesn't address it. Then, in a table: where do they agree, and where do they conflict? For each conflict, quote both sides, name who holds each view, and say whether it is about facts, dates or versions, definitions, or opinion. Finally, list what none of them covers that someone would need in order to {problem}.

*Why:* asked loosely, a model lets one source speak for all and smooths conflicts over. One line per source makes a missing voice visible, and naming the kind of conflict makes it handled rather than hidden. In a large notebook, run it with `only` on two to four sources.

### 7. Decide or use it (optional; `"phase": "apply"` or `"deliverable"`)

> My situation, as facts: {my situation}. Which passages support applying {topic} here, and which argue against it or set conditions? If my situation assumes something the sources contradict, say so first. What would have to be true for the opposite choice to be right? Do the sources give a track record or base rate for cases like mine? If I acted on this and it failed a year from now, what is the most likely reason, according to the sources? End by listing any claim above that no quoted passage supports.

Write `{my situation}` as plain facts, with no hint of which way the learner leans.

> Turn the answers so far on {topic} into a one-page {deliverable} I can use this week, in plain words. Mark anything I should check with a current source or a real person.

### 8. Teach-back (`"phase": "teachback"`, asked after the visuals)

> Here is my explanation of {topic}, written from memory: {my explanation}. Using only the sources, tell me (1) what is correct, (2) what is wrong, (3) what is missing that matters, and (4) what I simplified too far. For each of 2 to 4, point to the passage I should re-read. Then ask me one question that tests the weakest part.

*Why:* explaining from memory shows what was understood rather than recognized. It only works with the sources closed, so the learner writes first and the notebook reads second.

## One concept, quickly

For "explain X simply" on a notebook that already exists, four questions are enough: **How it works** (below) on the concept, **Compare cases**, **Where it breaks**, then **Teach-back**. Add **Problem first** when the learner has some background.

## More questions

The loop is a start. These keep the learning going; each costs about 2% of a five-hour window.

- **How it works:** "Explain how {concept} works, as a numbered chain: what happens first, what that leads to, and why. Explain each term where it first appears. Use one everyday comparison and say where it stops being true. Then say in one line what this explanation leaves out."
- **Where to start (80/20):** "Which few ideas in these sources give most of the ability to {problem}? List at most five, in the order I should learn them, and say what I can safely skip for now."
- **How it fits together:** "List the main ideas in {topic}, at most six, one line each. Draw one text diagram in a code block, at most 20 lines: a single-line box for each idea, joined by arrows labelled with how one leads to the next. Under it, give one plain sentence for each arrow. Say which idea to learn first, and why. Stop there: no separate breakdown of each idea." Without the limits it draws tall boxes and adds a long glossary nobody asked for. A mind map answers the same question as a picture for about the same cost.
- **Prerequisites:** "What must someone already understand before {topic} makes sense? List the prerequisites in order, each with a one-sentence plain explanation, and say which of them these sources don't explain."
- **Contrast with something known:** "Explain {concept} by contrasting it with {something I know well}. What is the same, what is different, and where does the comparison mislead?"
- **Vocabulary:** "List the 10 terms I must know for {topic}. For each give a plain one-sentence meaning and a sentence using it the way the sources do."
- **Predict, then check** (needs `pause_after`): "Before explaining {concept}, describe a situation from the sources and ask me to predict what happens. Don't reveal the answer yet."
- **Strongest case against:** "What is the strongest case against {option}, according to the most credible source that disagrees? Quote it."
- **Comparison table** (also good as a `data-table` artifact): "Rows are the key questions for {decision}; columns are each source's position; a last column says where they differ and why."
- **Explain a miss:** "I answered '{my answer}' to this quiz question: {question}. Using the sources, explain why the right answer is right and what my answer gets wrong."

## Subject extras

- **Sales conversations:** "Write 10 discovery questions about {customer}'s last real decision on {problem}. Flag any that invite compliments instead of facts."
- **Buying a small business:** "Turn the sources' criteria for a good first acquisition into a checklist for {my situation}." Lending terms, rates and rules go on the verify list.
- **Investing and capital allocation:** "What did these investors have in common in how they used capital? Turn it into rules, each with the case it came from."
- **Personal topics** (keep the notebook private): "Using {source}, what is and isn't in my control about {my situation}?"

## Plain-language rules

The notebook's chat persona enforces these (`assets/persona-plain.txt`). Follow them in your own messages to the learner too.

1. Give the answer in one sentence first.
2. Say what happens and why before naming it.
3. Explain each technical term in the sentence where it first appears. Spell out abbreviations.
4. Give a concrete case before the general rule.
5. Use one everyday comparison, and say where it stops being true.
6. Short sentences, one idea per paragraph.
7. When something was left out to keep it simple, say so.
8. No filler ("basically", "simply"), no praise, no padding.
