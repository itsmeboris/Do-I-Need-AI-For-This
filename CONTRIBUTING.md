# Contributing

Bug reports, clearer examples, and improvements to the decision framework are welcome.
For substantial changes, open an issue describing the use case and intended behavior first.

## Local development

Use Python 3.10 or newer. The tools and tests use only the standard library.

```sh
git clone https://github.com/itsmeboris/Do-I-Need-AI-For-This.git
cd Do-I-Need-AI-For-This
python -m unittest discover -s tests -v
```

The shared skill lives in `skills/do-i-need-ai-for-this/`. Both plugin manifests
point to the same content. Framework documents define the patterns, labels, and
report sections used by the checker and renderer.

For packaging changes, also run:

```sh
npx skills add . --list
claude plugin validate .
claude plugin validate .claude-plugin/plugin.json
```

`npx` requires Node.js/npm; plugin validation requires Claude Code. These tools
are optional for working on the Python report pipeline.

## Pull requests

- Explain the problem, observable behavior change, and how you tested it.
- Add a regression test for checker or renderer behavior changes.
- Keep the report tools dependency-free and the HTML safe to open offline.
- Use fictional or sanitized inputs in examples and tests.
- Keep versions synchronized across manifests when preparing a release.
- Document user-visible changes under `Unreleased` in the changelog.

For skill-instruction changes, exercise both an idea review and an implementation
audit in an actual host agent. Python tests cannot verify model behavior. Record
the host/version, input, and observed result in the PR without including private data.

Please keep discussions constructive and focused on the work. Contributions are
provided under the repository's Apache-2.0 license.
