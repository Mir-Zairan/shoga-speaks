# 🦜 Shoga-Speaks

*Shoga* means parrot in Kashmiri.

A Claude Code plugin that makes Claude explain things **your way**: in your language and
script, written for your role, short and simple. It works automatically on everything
Claude writes (chat, other skills' output, PR comments, artifacts), with nothing to invoke.

```
Release mat karein. Do problems hain: ek security risk aur ek slow page ka risk.

**1. Security (SQL injection) — line 6**
- `customer_id` seedha query mein joda ja raha hai, koi safety check nahi.
...
**Aap ka decision:** release ko hold karein jab tak dev team yeh fix na kar de.

▸ English: "en" likhein
```
*(Roman-Urdu, role: Product Owner)*

## Install

```bash
claude plugin marketplace add <owner>/shoga-speaks
claude plugin install shoga-speaks@shoga-speaks
```

Then in Claude Code run `/shoga-speaks:setup`.

To try it from a local folder: `claude --plugin-dir ./shoga-speaks`

Requires Node.js 18+ on your PATH (the hook script has no dependencies).

## What you get

| | |
|---|---|
| **Every reply** | In your language and script, for your role(s), at your chosen length |
| **Other language on request** | Type `en` (or `tr`) to see the last answer in the other language |
| **PR comments** | English open, your language in a collapsed `<details>` block (or the reverse) |
| **Artifacts** | Focused pages with a language switch: `/shoga-speaks:page <topic>`, or automatically whenever Claude makes one |
| **Project glossary** | Your project's own terms, kept as-is and explained simply |

## Shortcuts

Type these as the whole prompt:

| Prompt | Does |
|---|---|
| `en` / `tr` | Repeat the last explanation in English / your language |
| `shoga status` | Show current settings |
| `shoga off` / `shoga on` | Turn it off or on for this session |

## Settings

`/shoga-speaks:setup` writes these for you. Files, lowest to highest priority:

1. Plugin defaults (`defaults/settings.json`)
2. Team, per project: `.claude/shoga-speaks.json` (commit it)
3. You: `~/.claude/shoga-speaks.json`
4. You, one project only: `.claude/shoga-speaks.local.json`

```json
{
  "language": "urdu",
  "script": "roman",
  "github_script": "native",
  "roles": ["qa", "dev"],
  "length": "short",
  "keep_english_terms": true,
  "cli_open": "translated",
  "github_open": "english",
  "apply_to": {
    "chat": true,
    "pr_comments": true,
    "artifacts": true,
    "commit_messages": false,
    "code_comments": false
  },
  "artifacts": {
    "switch_languages": ["mine", "english"],
    "role_switch": false
  }
}
```

| Key | Values |
|---|---|
| `language` | `english`, `urdu`, `hindi`, `dutch` (any file in `languages/`) |
| `script` / `github_script` | `roman`, `native`, or `default`. `github_script` falls back to `script` |
| `roles` | `dev`, `qa`, `devops`, `po`, `pm`, `support`. The **first** role leads; others get one line each |
| `length` | `short`, `medium`, `detailed` |
| `cli_open` | `translated` or `english`: what the terminal shows first |
| `github_open` | `english` or `translated`: what PR comments show open |
| `artifacts.switch_languages` | `mine`, `english`, or `language:script` like `urdu:native` |

Settings changes apply fully after `/clear` or a new session.

## Languages and scripts

| Language | Scripts |
|---|---|
| English | plain English (B1) |
| Urdu | `roman` (Roman-Urdu) · `native` (اردو) |
| Hindi | `roman` (Hinglish) · `native` (हिन्दी) |
| Dutch | plain Dutch (B1) |

### Add a language

Copy `languages/_template.md` to `languages/<name>.md` and fill it in: the scripts it
supports, the tone, fixed spellings for roman text, and a "hard word → simple word" list.
No code changes. Native speakers are the best people to write these. Kashmiri, Punjabi
and Sindhi contributions are especially welcome.

### Add a role

Add `roles/<name>.md` with what the role cares about, which jargon is fine, what to
leave out, and how an answer should end.

## How it works

Hooks cannot rewrite Claude's replies after they are written, so Shoga-Speaks shapes
them before they are written:

- **SessionStart** loads the rules, your language guide, your roles and the project
  glossary once (re-loaded after `/clear` and compaction).
- **UserPromptSubmit** adds a one-line reminder to every prompt, and handles the
  shortcuts.

Because it works through instructions, Claude can occasionally slip (a formal word, a
longer answer than asked). The per-prompt reminder keeps this rare. If you see a word
that keeps coming back, add it to the language file's list.

## Limits

- The terminal cannot collapse text. The other language is shown on request (`en` / `tr`),
  not hidden in the same reply. GitHub and artifacts do have real collapsing.
- Right-to-left scripts often display badly in terminals. Use `roman` in the CLI and
  `native` for GitHub and artifacts.
- Quality is best for widely written languages. Low-resource languages need a good
  language file.
