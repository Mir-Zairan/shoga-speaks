# Contributing

Thanks for helping more people understand their tools. The most useful contributions:

1. **A language or script**: one Markdown file. See [Add a language](docs/languages.md).
2. **Better words**: if Shoga-Speaks keeps using a hard word, add it to the language file's simple-words list.
3. **A role**: see [Add a role](docs/languages.md#add-a-role).
4. **A risky command** it should explain: see [Add a risky command](docs/languages.md#add-a-risky-command).

## Before you open a pull request

```bash
node --test tests/node/*.test.mjs
claude plugin test .
claude plugin validate . --strict
```

Try it locally with `claude --plugin-dir .`.

## Style

- Plain, simple words in docs and in every language file. That is the whole point of the project.
- Keep the README short; details go in `docs/`.
- One change per pull request.

By contributing you agree that your contribution is licensed under the [MIT License](LICENSE) and that you follow the [Code of Conduct](CODE_OF_CONDUCT.md).
