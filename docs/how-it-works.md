# How it works

Shoga-Speaks has two layers. The first works on every Claude Code version. The second adds display features on Claude Code 2.1.287 or later.

## Layer 1: hooks (every version)

[`hooks/hooks.json`](../hooks/hooks.json) runs [`scripts/shoga.mjs`](../scripts/shoga.mjs) at these points:

| Hook | What it does |
|---|---|
| `SessionStart` | Loads the rules, your language guide, your roles, the project glossary, your level and known terms. It also reads your git name and email and your GitHub login from local config (no network; the gh token is never read), so Claude can tell your own code from code that is new to you. Re-runs after `/clear` and compaction. |
| `UserPromptSubmit` | Adds a one-line reminder to every prompt, with the layout (folded or plain). Handles `en`, `tr`, `tech`, `story`, `huh` (or `??`) and `shoga …`. |
| `Stop` | Checks the finished reply ([quality check](settings.md#quality-check-quality_guard)). |
| `PreToolUse` (Bash) | Explains risky commands in the approval prompt. |
| `PostToolUseFailure` (Bash) | Asks for a plain explanation when a test, build or install fails. |

Hooks can't change a reply after it is written, so Shoga-Speaks shapes it before: Claude writes in your style from the start.

## Layer 2: display mod (Claude Code 2.1.287+)

[`hooks/shoga-mod.tsx`](../hooks/shoga-mod.tsx) runs inside Claude Code and changes what is drawn:

- The `▸ English` line under a reply becomes a toggle. The other language is translated by a small, fast model (Haiku) **only when you open it**, and cached.
- `en` / `tr` unfolds or folds every reply instantly, with no Claude turn.
- Shell commands get a plain line under the approval dialog and under the tool row. Your permission rules are not touched.
- A reply comes in two layers: the story in plain words, and the technical part for your role. The one `layers` leads with is shown, the other folded (`▸ Technical` or `▸ Story`); `tech` / `story` unfolds or folds them all. Without the mod, Claude writes the lead layer only and the keyword asks for the other.
- Technical terms Claude marks (`{{idempotency key}}`), or only lists under `▸ Terms`, are underlined inside the answer. On the terminal a hover opens a one-line card over the reply; on desktop, VS Code and mobile a click does. Glossary meanings are translated once and cached.
- A status line shows `🦜 Roman-Urdu · QA`.

Mods are early access in Claude Code. They don't run in `claude -p`, the Agent SDK or cloud sessions. There, layer 1 still works: `en` asks Claude for the other language instead.

## Files

```
.claude-plugin/     plugin.json, marketplace.json
hooks/              hooks.json, shoga-mod.tsx (+ tests)
scripts/            shoga.mjs, lib/pure.mjs (shared by both layers)
data/               commands.mjs (risky commands), glossary.mjs (tech terms)
core/               rules for chat, the two layers, PR comments, artifacts
languages/          one file per language
roles/              one file per role
skills/             /shoga-speaks:setup, /shoga-speaks:page
```

## Tests

```bash
node --test tests/node/*.test.mjs   # hooks and shared logic
claude plugin test .                # display mod, on terminal/desktop/vscode surfaces
claude plugin validate . --strict   # manifest and hooks
```
