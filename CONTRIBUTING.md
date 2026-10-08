# Contributing to reportgate

Thank you for helping. reportgate is maintained by Zitan Yu, and it is meant to stay
small, local, and predictable; [VISION.md](VISION.md) explains what that rules in and out.

You do not need to write code to contribute. These are just as welcome:

- **Reproduction.** A minimal report that gets the wrong verdict is the most valuable
  thing you can send. Remove anything secret or undisclosed first, then open a
  "Wrong verdict" issue. If you can, add it to a test as well.
- **Triage.** Reproduce and label incoming issues, and point out duplicates.
- **Translation.** Improve the Chinese or English replies and README, or add a language.
- **Documentation.** If any step here or in the README did not work exactly as written,
  that is a bug; please report or fix it.

Starter tasks with scope, acceptance criteria, and files are in
[docs/good-first-issues.md](docs/good-first-issues.md).

Security problems in reportgate itself do not go in issues; see [SECURITY.md](SECURITY.md).
Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## Set up

You need Python 3.10 or newer and git. reportgate has no runtime dependencies; the only
development tool is the formatter, locked to one version in `requirements-dev.txt`.

```sh
git clone https://github.com/ZitanYu/reportgate
cd reportgate
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

On Windows, use `py -m venv .venv` and `.venv\Scripts\activate`, then the same commands
with `python` instead of `python3`.

## The commands

These are exactly the commands CI runs on every pull request.

```sh
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m unittest discover -s tests -v
python3 -m reportgate examples/reports --repo examples/pastebox
```

To fix formatting instead of checking it:

```sh
python3 -m ruff format .
```

To run one test file:

```sh
python3 -m unittest discover -s tests -p "test_paths.py" -v
```

## When you change the output

The files in `examples/expected/` are the real output for the examples, and the README's
sample output is checked against them. If your change alters the output on purpose,
regenerate them and commit the result:

```sh
python3 -m reportgate examples/reports --repo examples/pastebox --out examples/expected
```

Read the diff before committing: it should show only the change you meant. If the README
sample is part of what changed, copy the new text into the README too; the test
`test_readme_sample_output_is_real` tells you if they disagree.

Changes to the JSON output must keep the promise in [docs/SCHEMA.md](docs/SCHEMA.md):
add fields, never remove or rename them, and document every new field in the same pull
request (`tests/test_schema.py` fails otherwise).

## Pull requests

- Keep each pull request to one change, with a test that fails without it.
- For a verdict change, include the minimal report that shows the before and after.
- Do not add dependencies, network access, model calls, or anything that runs a report's
  code. These will be declined; see VISION.md.
- Add a line to `CHANGELOG.md` under `Unreleased` for anything a user would notice.
- Replies are sent to real people. Keep them polite, specific, and honest that they are
  triage, and change English and Chinese together.

## Releasing (maintainer)

Zitan Yu cuts releases: bump `reportgate/_version.py`, move the `Unreleased` entries in
`CHANGELOG.md` under the new version, tag `vX.Y.Z`, and publish the GitHub release with
those notes.
