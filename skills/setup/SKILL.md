---
name: setup
description: Set up Shoga-Speaks - choose your language, script, roles and answer length, and optionally build a project glossary.
argument-hint: "[glossary]"
disable-model-invocation: true
---

# Shoga-Speaks setup

Keep this friendly and quick. Ask, don't lecture. Use simple words.

## 1. Read the current state

Run:

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/shoga.mjs" resolve
```

It prints the current settings, the settings file paths, and the available languages
(with their scripts) and roles. If `$ARGUMENTS` is `glossary`, skip to step 4.

## 2. Ask the user

Use the AskUserQuestion tool. Show the current value as the first option when one exists.

**Round 1**
1. *Language*: which language should Claude explain things in? Options from `available.languages`
   (the most likely four; the user can type another via "Other").
2. *Roles* (multiSelect): which roles do you have? Options from `available.roles`
   (dev, qa, devops, po, pm, support). Tell them the first one they list matters most;
   ask for the order in a follow-up only if they pick more than one.
3. *Length*: short (recommended) / medium / detailed.

**Round 2** (only if the language is not English)
1. *Script in the terminal*: the scripts of that language, by label (for example
   Roman-Urdu / اردو). Recommend the roman script for the terminal: right-to-left text
   often displays badly there.
2. *Script on GitHub*: same options. Native scripts display well on GitHub.
3. *What the terminal shows first*: their language (recommended) or simple English.
   The other one is available by typing "en" / "tr".
4. *What GitHub comments show first*: English (recommended for mixed teams) or their language.
   The other one goes in a collapsed section.

If the user typed a language that is not in the list, say it is not supported yet, point
them to `${CLAUDE_PLUGIN_ROOT}/languages/_template.md`, and let them pick another.

## 3. Save

Write only the chosen keys to the user settings file (`settings_files.user`, normally
`~/.claude/shoga-speaks.json`), merged with whatever is already there. Example:

```json
{
  "language": "urdu",
  "script": "roman",
  "github_script": "native",
  "roles": ["dev", "qa"],
  "length": "short",
  "cli_open": "translated",
  "github_open": "english"
}
```

Values: `cli_open` is `translated` or `english`; `github_open` is `english` or `translated`.

## 4. Project glossary (optional)

Ask: "Should I make a short glossary of this project's own terms? It helps me explain
domain words simply and keeps them from being translated badly."

If yes:
1. Read only light sources: README, docs folder titles, CLAUDE.md, top-level folders,
   and names of main domain models/entities. Do not read the whole codebase.
2. Pick at most 20 project-specific terms (business or domain words, product names,
   internal module names). Skip general programming words.
3. Draft each as one line, in plain English so the whole team can use it:
   `- **Term**: what it means, in under 15 simple words`
4. Show the draft and ask the user to approve or edit it.
5. Save it to `settings_files.glossary` (`.claude/shoga-speaks/glossary.md` in the project).
   Suggest committing it so teammates get it too.

## 5. Finish

In the user's chosen language and style (it is short anyway), tell them:
- What is set, in one line.
- Type `/clear` or start a new session so the full settings load.
- Shortcuts: `en` / `tr` for the other language, `shoga off` / `shoga on`, `shoga status`.
- For a different setup in one project, use `.claude/shoga-speaks.local.json` there.
