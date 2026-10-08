## What this changes

<!-- One change per pull request. Link the issue it closes, if any. -->

## How to check it

<!-- For a verdict change: the minimal report, and the verdict before and after. -->

## Checklist

- [ ] `python3 -m ruff format --check .` and `python3 -m ruff check .` pass
- [ ] `python3 -m unittest discover -s tests -v` passes, with a test for this change
- [ ] If the output changed on purpose, `examples/expected/` is regenerated and the diff is only that change
- [ ] If the JSON changed, fields were only added and `docs/SCHEMA.md` documents them
- [ ] English and Chinese replies changed together, if either changed
- [ ] `CHANGELOG.md` has an `Unreleased` entry, if a user would notice
- [ ] No new dependency, network access, model call, or execution of report content
