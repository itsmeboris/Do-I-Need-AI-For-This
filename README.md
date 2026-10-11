# Do I Need AI for This?

`Do I Need AI for This?` turns an automation idea or existing workflow into a
checked architecture verdict. It separates deterministic processing, model
judgment, and human authority; selects the smallest safe pattern; and returns a
polished, self-contained HTML report.

The plugin has two entry points:

- `verdict` evaluates an idea or specification before implementation.
- `audit` reviews an implementation already available in the active workspace.

## What it produces

The plugin first creates temporary structured Markdown, validates it with the
bundled deterministic checker, and then renders an Editorial Brief HTML file.
Users receive only the final `.html` report. Reports include the recommended
pattern, judgment count, model tiers, human-approval boundary, assumptions,
measurements, failure modes, and next action.

In a persistent workspace, reports are saved as:

```text
docs/verdicts/YYYY-MM-DD-<slug>.html
```

In Claude chat and mobile, the report is returned from the code-execution
sandbox as a downloadable file. Cowork writes it to the task's writable
workspace.

## Claude chat, mobile, and Cowork

Zip this plugin folder so `.claude-plugin/plugin.json` is at the archive root,
or inside the archive's single top-level folder. In Claude, open
**Customize > Plugins > Add > Upload plugin** and select the ZIP. Start a new
chat or Cowork task after installation.

Claude's current testing instructions are documented in
[Plugin structure and testing](https://claude.com/docs/plugins/build).

In chat, describe the automation or attach its supporting files. In Cowork,
select the local files or folder the audit may read. The plugin never retrieves
an unavailable target; it asks you to paste, upload, or select the material.

## Claude Code

Load the working copy directly:

```text
claude --plugin-dir .
```

Then invoke either command:

```text
/do-i-need-ai-for-this:verdict
/do-i-need-ai-for-this:audit
```

## Codex and ChatGPT

The repository includes the supported `.codex-plugin/plugin.json`
compatibility manifest and a root `skills/` directory. Install the packaged
plugin through the Plugins interface when plugin upload is available, or copy
`skills/do-i-need-ai-for-this/` into a personal Codex skills directory for
local-only use.

The packaging format is described in OpenAI's
[plugin documentation](https://developers.openai.com/plugins/build/plugins).

## Requirements

- Python 3 or an equivalent Python code-execution environment.
- Read/write access to a sandbox or workspace for the temporary verdict and
  final HTML report.
- No third-party Python packages.

If Python execution is unavailable, the plugin stops and explains why. It does
not replace deterministic validation with an unchecked model-only answer.

## Privacy and trust

The plugin reads only text and files supplied to the active conversation or
already available in its workspace. It does not access a remote repository,
make network requests, use telemetry, read ambient credentials, or send data to
another service. The generated report embeds its CSS and contains no JavaScript,
external fonts, trackers, or remote assets, so it can be opened offline.

## Status

Version `1.0.0` is in private validation. It is not yet listed in the Claude or
OpenAI plugin directories.

## License

Apache License 2.0. Copyright 2026 Boris Sobol. See [LICENSE](LICENSE).
