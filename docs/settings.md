# Settings

`/shoga-speaks:setup` writes your settings. You can also edit the files by hand. Changes apply fully after `/clear` or a new session.

## Where settings live

Lowest to highest priority:

1. Plugin defaults: [`defaults/settings.json`](../defaults/settings.json)
2. Team, per project: `.claude/shoga-speaks.json` (commit it)
3. You: `~/.claude/shoga-speaks.json`
4. You, one project only: `.claude/shoga-speaks.local.json`

Your level, known terms and stats are kept in `~/.claude/shoga-speaks/profile.json`.

## All options

| Key | Values | Default | What it does |
|---|---|---|---|
| `enabled` | `true` / `false` | `true` | Turns the plugin on or off |
| `language` | `english`, `urdu`, `hindi`, `dutch`, or any file in `languages/` | `english` | Language Claude explains in |
| `script` | `roman`, `native`, `default` | `default` | Script in the terminal |
| `github_script` | `roman`, `native`, `default` | same as `script` | Script in PR comments |
| `roles` | list of `dev`, `qa`, `devops`, `po`, `pm`, `support` | `["dev"]` | Who you are. The first role leads; each extra role adds one line |
| `length` | `short`, `medium`, `detailed` | `short` | How long answers are |
| `keep_english_terms` | `true` / `false` | `true` | Keep words like *query* or *deploy* in English |
| `cli_open` | `translated`, `english` | `translated` | Which language the terminal shows first |
| `github_open` | `english`, `translated` | `english` | Which language PR comments show open |
| `explain_commands` | `danger`, `caution`, `off` | `danger` | Which shell commands get a plain explanation in the approval prompt (see below) |
| `explain_failures` | `true` / `false` | `true` | Explain failing tests and builds in one plain line first |
| `quality_guard` | `remind`, `fix`, `off` | `remind` | What happens when a reply slips (see below) |
| `layers` | `story`, `technical`, `technical-only` | `story` | What a reply leads with. `story`: plain story, technical part folded. `technical`: technical part, story folded. `technical-only`: no story. Each role has its own technical part (`roles/*.md`) |
| `term_hints` | `on`, `off` | `on` | Claude marks up to 5 technical terms you may not know; the display mod underlines them in the answer and a hover (a click outside the terminal) opens a short card. `glossary_hover: "off"` (0.2.0) still turns it off |
| `apply_to.chat` | `true` / `false` | `true` | Shape chat replies |
| `apply_to.pr_comments` | `true` / `false` | `true` | Bilingual PR comments |
| `apply_to.artifacts` | `true` / `false` | `true` | Shape artifacts and pages |
| `apply_to.commit_messages` | `true` / `false` | `false` | Translate commit messages (leave off for mixed teams) |
| `apply_to.code_comments` | `true` / `false` | `false` | Translate comments written into code (leave off) |
| `artifacts.switch_languages` | list like `["mine", "english", "urdu:native"]` | `["mine", "english"]` | Language switch on pages |
| `artifacts.role_switch` | `true` / `false` | `false` | Add a “View as” role switch on pages |

## Approval explanations (`explain_commands`)

Without the display mod, Shoga-Speaks shows the explanation as the reason in Claude Code's approval prompt. To make sure you see it, the prompt is shown **even for commands you have allowed**:

- `danger` (default): only commands that can lose work or data, such as force push, `reset --hard`, `rm -r`, `DROP TABLE` and `terraform destroy`
- `caution`: also pushes, migrations, rebases and PR comments
- `off`: never

In headless runs (`claude -p`, CI), a forced prompt cannot be answered, so the command is held. Set `explain_commands` to `off` there.

With the display mod (Claude Code 2.1.287 or later), the explanation is drawn under the dialog and the tool row instead, and your permission rules are not touched.

## Quality check (`quality_guard`)

After every reply, Shoga-Speaks checks it against your language file and settings: words from the avoid list, characters from another script mixed into roman text, length over your setting, and code blocks shown to a PO, PM or support role.

- `remind` (default): the next prompt tells Claude what slipped. Nothing extra is shown.
- `fix`: a serious slip makes Claude rewrite the reply once, straight away.
- `off`: no checks.

`shoga status` shows how many replies were checked and how many slipped.

## Example

```json
{
  "language": "urdu",
  "script": "roman",
  "github_script": "native",
  "roles": ["qa", "dev"],
  "length": "short",
  "quality_guard": "fix",
  "explain_commands": "caution"
}
```
