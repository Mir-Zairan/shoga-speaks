---
name: page
description: Make a short, focused explainer page (artifact) in the user's language and script, written for their role, with a language switch. Use when the user asks for a page, artifact, one-pager or shareable explanation of a PR, feature, release, incident or any topic.
argument-hint: "[what to explain, e.g. PR 482 for the QA team]"
---

# Shoga page

Topic: $ARGUMENTS

## 1. Settings

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/shoga.mjs" resolve
```

Use `resolved` for the language, script and roles. If the topic names a role or team
("for the QA team"), write for that role instead.

## 2. Page rules

Read `${CLAUDE_PLUGIN_ROOT}/core/artifacts.md` and follow it exactly.

## 3. Gather facts

Collect what you need about the topic (PR diff, code, tickets, docs). Get the facts
right first; simplicity comes from choosing what to leave out, not from being vague.

## 4. Plan before writing

Decide, in this order:
1. The one line: the whole point in one sentence.
2. At most three key points.
3. One visual (table, before/after, flow) that replaces the most text.
4. The "what you need to do" checklist for the role(s).
5. What goes into collapsed details, and what is left out completely.

If something does not serve the reader's role, leave it out.

## 5. Build

- Write the content once per language in the switch. Same structure, same facts.
- One self-contained HTML page, following the page-design and artifact rules of this
  session (if an artifact tool is available, also follow its design guidance).
- Publish it as an artifact if the session has an artifact tool; otherwise save it as an
  `.html` file in the current directory and say where it is.

## 6. Reply

Two lines at most, in the user's language: what the page covers and the link or path.
