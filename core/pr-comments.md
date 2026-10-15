# Shoga-Speaks: PR and issue comments

Applies whenever you draft text that will be posted on GitHub (PR review comments,
PR descriptions, issue comments) via `gh` or any other tool.

## Who it is for
Write for the PR author at developer level, not for the local user's role.
The reader on GitHub may be anyone on the team.

## Format
Put the `github_open` language first, fully readable. Put the other language in a
collapsed block right below it:

```markdown
<open-language text>

<details><summary>LABEL</summary>

<other-language text>
</details>
```

- LABEL is the other language's display name (for example `Roman-Urdu`, `اردو`, `English`).
- Use `github_script` for the translated part.
- Both versions say the same thing. Same code references, same suggestion.
- Keep each comment short: the problem, why it matters, the suggested fix.
- Code suggestions go in code blocks or GitHub ```suggestion blocks, never translated.

## Before posting
Show the user the draft and ask before posting. Posting is public.
