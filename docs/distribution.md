# Distribution and compatibility

One skill directory is the source of truth. It contains the instructions,
framework, checker, and renderer; installing only `SKILL.md` is insufficient.

| Route | Package | Validation |
| --- | --- | --- |
| `npx skills` | `skills/do-i-need-ai-for-this/` | Local discovery and isolated installation smoke test |
| Claude Code | `.claude-plugin/plugin.json` plus shared skill | CLI manifest/marketplace validation; host conversation testing remains a release check |
| Codex plugin | `.codex-plugin/plugin.json` plus shared skill | Compatibility manifest included; host import remains a release check |
| ChatGPT, Claude chat/mobile, Cowork | Host-specific plugin import | Not end-to-end tested; requires Python execution and writable files |

Supported Python baseline: 3.10+. CI is configured for Python 3.10, 3.12, and 3.14
on Windows and Linux. A configured job is not evidence it has run: consult the
repository's Actions results for the published revision.

## Claude marketplace

The marketplace name is `dinaift`. Its single plugin uses the repository root as
its source. The plugin name is `do-i-need-ai-for-this`; its only skill has the same
name, so the plugin invocation is
`/do-i-need-ai-for-this:do-i-need-ai-for-this`.

Reference: [Claude marketplace documentation](https://code.claude.com/docs/en/plugin-marketplaces).

## Codex compatibility

The repository retains the `.codex-plugin/plugin.json` compatibility layout with
`skills: "./skills/"`. Users can also install the skill through `npx skills`.
Plugin import interfaces depend on the host. Inclusion of a manifest does not
mean the plugin is listed in an official directory.

Reference: [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins).

## Prepare a ZIP

From a clean, committed release revision:

```sh
python -c "from pathlib import Path; Path('dist').mkdir(exist_ok=True)"
git archive --format=zip --output=dist/do-i-need-ai-for-this.zip HEAD .claude-plugin/plugin.json .codex-plugin/plugin.json skills README.md LICENSE CHANGELOG.md CONTRIBUTING.md docs/distribution.md docs/assets examples
```

This archives committed files only. Keep `.claude-plugin/plugin.json` at the
archive root and retain all files under `skills/`. The marketplace catalog is
for Git-based distribution and is not needed in the plugin ZIP.

## Public release checklist

1. Run the Python tests, example check/render, and both Claude validation commands
   from CONTRIBUTING.md. Confirm CI passes on the release commit.
2. Smoke-test the shared skill in the hosts you intend to claim as tested.
   Exercise both modes and open the resulting report.
3. Review the exact branches, tags, history, and packaged files to be made public.
   Scan for secrets and private inputs; do not publish local task reports.
4. Keep manifest versions aligned; finalize the changelog date when releasing.
5. Enable GitHub private vulnerability reporting and confirm the reporting link
   works before advertising it. Configure branch protection for the CI checks.
6. Set the GitHub description to "Find the smallest safe architecture for your
   automation. An agent skill with checked HTML reports." Suggested topics:
   `agent-skills`, `claude-code`, `codex`, `automation`, `architecture`.
7. Push the reviewed revision, change repository visibility when ready, and verify
   installation from a fresh directory without private-repository credentials.
8. Create a version tag and GitHub release, attach the ZIP, and include the
   changelog and any remaining host-compatibility limitations.

Repository visibility, official directory submissions, branch protection, and
releases are GitHub/account operations separate from preparing these files.
