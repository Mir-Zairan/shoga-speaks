# Add a language or role

Both are single Markdown files. No code changes.

## Add a language

1. Copy [`languages/_template.md`](../languages/_template.md) to `languages/<name>.md`.
2. Fill in the header: the scripts the language has (`native`, `roman`), a label for each, and `rtl.native: true` for right-to-left scripts.
3. In `## common`, describe how people actually speak at work: which English work words stay English, and what to avoid (formal, literary or rare words).
4. For each script, add:
   - **Spelling**: one fixed spelling for common words (roman scripts especially).
   - **Simple words**: `- hard word → word people actually say`. The quality check uses the left side as its avoid list, so every line counts.
5. Add translations for the risky-command explanations in [`data/commands.mjs`](../data/commands.mjs), keyed `language:script` (for example `"kashmiri:roman"`). English is used until you do.
6. Run `node --test tests/node/*.test.mjs` and open a pull request.

Native speakers write the best language files. Kashmiri, Punjabi and Sindhi are especially welcome.

## Add a role

Add `roles/<name>.md`:

```markdown
---
role: designer
label: Designer
---
Cares about: what users see, layout, flows, accessibility.
Jargon OK: design terms (component, spacing, contrast). Explain code terms in a few words.
Leave out: code internals.
End with: what changes on screen, and what to check.
```

## Add a risky command

Add an entry to [`data/commands.mjs`](../data/commands.mjs) with an `id`, a `risk` (`danger`, `caution` or `info`), a `match` regular expression and the `text` in each language. Add a case to `tests/node/pure.test.mjs`.
