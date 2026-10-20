<p align="center">
  <img src="assets/banner.svg" width="100%" alt="A Claude Code window. A developer, a QA tester, a product owner and a support agent each ask about the same payment bug in their own language: Roman-Urdu, English, Dutch and Hinglish. Without Shoga-Speaks the answer is a 400-word wall of jargon. Shoga the parakeet flies over from the logo and flips the Shoga-Speaks switch on, and the answer becomes two plain lines in the asker's language: a highlighted term is clicked to show its meaning, and the technical part is folded under Technical. Beside it: Claude Code, explained for you. Seedhi baat, no bakwas: straight talk, no nonsense.">
</p>

<p align="center">
  <b>A Claude Code plugin that explains everything in your language, your script and for your role.</b><br>
  <i>Seedhi baat, no bakwas.</i> Straight talk, no nonsense.
</p>

<p align="center">
  <a href="https://github.com/Mir-Zairan/shoga-speaks/releases"><img src="https://img.shields.io/badge/version-0.3.3-3BB273" alt="Version 0.3.3"></a>
  <img src="https://img.shields.io/badge/Claude%20Code-plugin-0B2E2B" alt="Claude Code plugin">
  <img src="https://img.shields.io/badge/languages-4-2C7DA0" alt="4 languages">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="MIT license"></a>
</p>

---

Claude Code answers in developer English. If you are a QA tester, product owner or project manager, or you think in **Urdu, Hindi or Dutch**, that costs focus. **Shoga-Speaks** (*shoga* is Kashmiri for parrot) makes every answer land the first time:

> **You** (Product Owner, Roman-Urdu): *Kya yeh PR release ho sakta hai?*
>
> **Release mat karein.** Do problems hain: ek security risk, ek slow page.
> - Ek customer doosre customers ka data dekh sakta hai (<ins>SQL injection</ins>).
> - 500 orders wale customer ke liye page bahut slow hoga.
>
> **Aap ka decision:** fix hone tak release hold karein.
>
> ▸ Technical · ▸ English

The technical detail stays folded until you open it, and the underlined term shows its meaning when you hover over it.

## Install

```text
/plugin marketplace add Mir-Zairan/shoga-speaks
/plugin install shoga-speaks@shoga-speaks
/shoga-speaks:setup
```

Setup asks for your language, script and roles. You need Node.js 18 or later. The display features need Claude Code 2.1.287 or later.

## What you get

| | What happens | Works on |
|---|---|---|
| 🗣️ **Your language and script** | Every answer is in Roman-Urdu, Urdu, Hinglish, Hindi, Dutch or plain English | any version |
| 🎭 **Your role** | Dev gets the fix, QA gets test steps, a PO gets the decision | any version |
| ⚠️ **Plain-language approvals** | `rm -rf build` → *“These files are deleted for good.”* | any version |
| 🧪 **Failures explained** | A failing test or build gets one plain line for your role first | any version |
| ✅ **Quality check** | Each reply is checked for hard words, mixed scripts and length | any version |
| 📈 **Learns your level** | `huh` gives a simpler version; terms you know stop being explained | any version |
| 🔁 **Fold or unfold the other language** | Press `▸ English` under a reply, or type `en` | 2.1.287+ |
| 🧩 **Story first, tech folded** | The answer in plain words; the details for your role sit under `▸ Technical` until you open it. Or the other way round, or technical only (`layers`) | 2.1.287+ (`tech` on older) |
| 📖 **Term hints** | Technical terms like *idempotency key* or a project name are underlined in the answer; hover for a one-line meaning (click on desktop and VS Code) | 2.1.287+ |
| 💬 **Bilingual PR comments** | English on GitHub, your language folded underneath | any version |
| 📄 **Explainer pages** | `/shoga-speaks:page PR 482 for QA` gives a one-page summary with a language switch | any version |

## Shortcuts

Type these as the whole prompt. None of them uses a Claude turn, except `huh`, and `tech`, `story` and the language shortcuts on Claude Code versions without the display mod.

| Type | Does |
|---|---|
| `en` / `tr` | Show the last answer in English / in your language |
| `tech` / `story` | Unfold every folded technical part / story (without the display mod: ask for it) |
| `huh` | “I didn't get that”: explain it simpler, and keep it simpler. `??` works too, but its first `?` opens Claude Code's shortcut help |
| `shoga simpler` / `shoga deeper` | Change your level (−2 to +2) |
| `shoga know N+1, migration` | Stop explaining these terms |
| `shoga status` | Show your settings and stats |
| `shoga web on` / `shoga web off` | Reading in a browser (Remote Control from claude.ai)? No folding; type `tech` for the details. Cloud sessions do this by themselves |
| `shoga off` / `shoga on` | Turn it off or on for this session |

## Languages and roles

| Language | Scripts |
|---|---|
| Urdu | Roman-Urdu · اردو |
| Hindi | Hinglish · हिन्दी |
| Dutch | Nederlands |
| English | plain English |

**Roles:** `dev` · `qa` · `devops` · `po` · `pm` · `support`. You can pick several; the first one leads.

Missing your language? A language is one Markdown file. See **[Add a language](docs/languages.md)**. Kashmiri, Punjabi and Sindhi are very welcome.

## Settings

`/shoga-speaks:setup` writes them for you to `~/.claude/shoga-speaks.json`:

```json
{ "language": "urdu", "script": "roman", "roles": ["qa", "dev"], "length": "short" }
```

Every option is in **[docs/settings.md](docs/settings.md)**.

## Why not just a line in CLAUDE.md?

CLAUDE.md can only ask Claude to follow rules. Shoga-Speaks also **checks** each reply, **remembers** what you understand, **explains** approval prompts and failures, and **changes what is drawn** on screen. In a small side-by-side test it gave a Product Owner about half the code jargon of a CLAUDE.md rule, and no mixed-script slips. See **[docs/why.md](docs/why.md)**.

## Learn more

- [How it works](docs/how-it-works.md)
- [Settings](docs/settings.md)
- [Add a language or role](docs/languages.md)
- [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Security](SECURITY.md)

## License

[MIT](LICENSE) © Zairan Mir
