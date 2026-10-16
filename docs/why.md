# Why not just a line in CLAUDE.md?

You can write *“Always reply in Roman Urdu, I am a product owner, keep it short”* in `CLAUDE.md`. That gets you part of the way. Here is what it can't do, and what a small test showed.

## What only a plugin can do

| | CLAUDE.md | Shoga-Speaks |
|---|---|---|
| Ask Claude to use your language | ✅ | ✅ |
| Tested word lists and fixed spellings per language and script | write them yourself | ✅ built in |
| Role files: what each role needs, what to leave out | write them yourself | ✅ built in |
| **Check** every reply for hard words, mixed scripts, length | ❌ | ✅ Stop hook |
| **Remember** your level and the terms you know | ❌ | ✅ profile |
| **Explain approval prompts** for risky commands | ❌ | ✅ |
| **Explain failing tests and builds** every time | ❌ (only if Claude decides to) | ✅ |
| Keep PR comments, commits and code in English for the team | ❌ (applies everywhere) | ✅ |
| Fold or unfold the other language without a new turn | ❌ | ✅ display mod |
| Hover glossary for technical terms | ❌ | ✅ display mod |
| Each teammate picks their own language, one shared setup | ❌ (one file, one language) | ✅ |

## A small side-by-side test

The same question, *“Review OrderRepository.php. Is it okay to release?”*, about a file with an SQL injection and an N+1 query. Two runs each:

| | A: “Reply in Roman Urdu” | B: CLAUDE.md (Urdu + PO + short) | C: Shoga-Speaks (Urdu, PO) |
|---|---|---|---|
| Words | 277–325 | 146–151 | 149–168 |
| Code jargon a PO won't follow | 22–34 | 8–9 | **4–5** |
| Hard Urdu words (*masla*, *behtar* …) | 1–2 | 1–3 | **0–1** |
| Characters from another script mixed in | 0 | **3** | 0 |
| Ends with what the PO should do | 1 of 2 | 0 of 2 | **2 of 2** |

Two runs per setup is a small sample, so read it as a signal, not proof. The checks added since then (quality guard, levels) are aimed at exactly the slips this test found.

## When CLAUDE.md is enough

If you only want chat replies in your language and don't care about roles, PRs or teammates, a few lines in `~/.claude/CLAUDE.md` is cheaper. Shoga-Speaks is for when understanding matters: different roles, mixed-language teams, and work that leaves your terminal.
