# Prompt library

Question templates for the learning loop, the plain-language rules, and extras. Pick 6–8 questions per topic.

**Placeholders.** Fill these in when writing the manifest: `{topic}`, `{problem}` (what the learner wants to be able to do), `{concept}`, `{my situation}`, `{deliverable}`. Leave `{attempt}` and `{my explanation}` exactly as written: `nlm_ask.py` refuses to send a question that still holds a placeholder, and that refusal is what gives the learner their turn.

**Added for you.** The script appends "Cite the passages you rely on. Where the sources do not cover something, write 'not in sources'." to every question that doesn't already say it.

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

## The loop

### 1. Problem first (`"phase": "problem", "pause_after": true`)

> I want to be able to {problem}. Using only the sources, choose one real case or example that shows this problem. Describe the situation in plain words in under 150 words, then stop: do not give the solution, the outcome, or the name of the idea that solves it. End by asking me what I would do. If the sources hold no suitable case, say so and build the closest scenario you can from what they do contain, marked as constructed.

*Why:* a short attempt before being told shows the learner what they don't know and makes the explanation stick. It must be short and followed by a clear explanation; unguided struggling doesn't help a beginner. If the learner has no background at all, skip to question 2 and rewrite it without the attempt.

### 2. Resolve it (`"phase": "resolve"`)

> Here is my attempt at that case: {attempt}. Using only the sources, show step by step how they resolve it. Then say what my attempt got right, what it missed, and why the missed part matters. Introduce only the ideas the solution needs, one plain sentence each, and name each idea after explaining it.

### 3. First principles (`"phase": "principles"`)

> Break {topic} down to the smallest claims it rests on, using only the sources. For each claim say whether it is a fact or definition, an assumption the author makes, or a convention people follow, and where it appears. Then rebuild {topic} in 5 to 7 plain steps, each using only the steps before it. Point out any step the sources assert without justifying. End with a text diagram in a code block, at most 20 lines with one line per step, showing which step depends on which.

*Why:* details are easier to hold once there is a skeleton, and sorting facts from assumptions shows which advice is solid and which is one author's taste. The closing diagram shows the same chain at a glance, which a list of steps does not.

### 4. Three levels (`"phase": "layers"`)

> Explain {concept} at three levels. Level 1, for a five-year-old: no technical words and one everyday comparison. Level 2, for a teenager: the real terms, each explained where it first appears. Level 3, for someone who does this for a living: the trade-offs and the limits. Each level builds on the one before without contradicting it. After level 1, say in one line what it simplified, and say where the comparison stops being true.

Use one question per concept, or up to three closely related concepts in one question. Asking for "brief" answers here tends to drop the foundations, so don't.

### 5. Where it breaks (`"phase": "fails"`)

> According to the sources, when does {concept} stop working? Give the conditions, and a sign I would notice in practice. Then list the 3 to 5 mistakes a beginner most often makes with it, each as: the mistake, why it is tempting, and what to do instead.

### 6. Disagreements and gaps (`"phase": "disagree"`, with two or more sources)

> Where do the sources disagree about {topic}? For each disagreement give each side in one plain sentence, and say which assumption explains the difference. Then list what none of the sources covers that someone would need in order to {problem}.

### 7. Use it (optional; `"phase": "apply"` or `"deliverable"`)

> Apply {topic} to my situation: {my situation}. Go step by step and flag every assumption I should check.

> Turn the answers so far into a one-page {deliverable} I can use this week, in plain words. Mark anything I should check with a current source or a real person.

### 8. Teach-back (`"phase": "teachback"`, asked after the visuals)

> Here is my explanation of {topic}, written from memory: {my explanation}. Using only the sources, tell me (1) what is correct, (2) what is wrong, (3) what is missing that matters, and (4) what I simplified too far. For each of 2 to 4, point to the passage I should re-read. Then ask me one question that tests the weakest part.

*Why:* explaining from memory is the best-tested step in the loop. It only works with the sources closed, so the learner writes first and the notebook reads second.

## One concept, quickly

For "explain X simply" on a notebook that already exists, three questions are enough: **Three levels** on the concept, **Where it breaks**, then **Teach-back**. Add **Problem first** when the learner has some background.

## More tools

- **Where to start (80/20):** "Which few ideas in these sources give most of the ability to {problem}? List them in the order I should learn them, and say what I can safely skip for now."
- **How it fits together:** "List the main ideas in {topic}, at most six, one line each. Draw one text diagram in a code block, at most 20 lines: a single-line box for each idea, joined by arrows labelled with how one leads to the next. Under it, give one plain sentence for each arrow. Say which idea to learn first, and why. Stop there: no separate breakdown of each idea, and under 400 words in all." Without the limits it draws tall boxes and adds a long glossary nobody asked for (seen on 2026-11-17: a 39-line diagram inside a 1,900-word answer). A mind map answers the same question as a picture for about the same cost; use this one when the learner wants the links explained in words.
- **Prerequisites:** "What must someone already understand before {topic} makes sense? List the prerequisites in order, each with a one-sentence plain explanation, and say which of them these sources don't explain."
- **Contrast with something known:** "Explain {concept} by contrasting it with {something I know well}. What is the same, what is different, and where does the comparison mislead?"
- **Vocabulary:** "List the 10 terms I must know for {topic}. For each give a plain one-sentence meaning and a sentence using it the way the sources do."
- **Predict, then check** (needs `pause_after`): "Before explaining {concept}, describe a situation from the sources and ask me to predict what happens. Don't reveal the answer yet."
- **Explain a miss:** "I answered '{my answer}' to this quiz question: {question}. Using the sources, explain why the right answer is right and what my answer gets wrong."

## Decision add-ons

Use these when the learner has a decision to make, after question 6.
- **Pre-mortem:** "It is a year from now and {decision} has failed badly. Using the sources, list the most likely causes, ranked, with the earliest warning sign of each."
- **Strongest case against:** "Give the strongest case against the option I lean toward ({option}), using the most credible source that disagrees."
- **Comparison table** (also good as a `data-table` artifact): "Rows are the key questions for {decision}; columns are each source's position; a last column says where they differ and why."

## Subject extras

- **Sales conversations:** "Write 10 discovery questions about {customer}'s last real decision on {problem}. Flag any that invite compliments instead of facts."
- **Buying a small business:** "Turn the sources' criteria for a good first acquisition into a checklist for {my situation}." Lending terms, rates and rules go on the verify list.
- **Investing and capital allocation:** "What did these investors have in common in how they used capital? Turn it into rules, each with the case it came from."
- **Personal topics** (keep the notebook private): "Using {source}, what is and isn't in my control about {my situation}?"
