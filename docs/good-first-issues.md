# Good first issues

Five starter tasks, each small enough for a first pull request. Comment on the matching
GitHub issue (or open one that links here) to say you are taking it, so two people do
not do the same work. Every task is done when its acceptance criteria hold and the
commands in CONTRIBUTING.md pass.

## 1. Add an email (`.eml`) report format

Many reports arrive as email. reportgate should read a saved `.eml` file directly.

**Scope.** Add `read_email(text, report_id)` to `reportgate/readers.py` using only the
standard library `email` package (`email.parser.Parser` with `email.policy.default`).
The title is the `Subject` header. The body is the `text/plain` part; if there is only an
HTML part, use it with tags removed. Register it as `".eml"` in `DEFAULT_READERS`. (The
README shows a two-line `.eml` reader as an illustration of replaceable readers; this
task replaces that sketch with a real, built-in one.)

**Acceptance criteria.**

- A test in `tests/test_readers.py` reads a multipart message (plain and HTML parts) and
  checks the title, the body, and that `format` is `"email"`.
- A test checks that a `.eml` file in a reports directory is picked up by `triage()`.
- `.eml` is listed with the other formats in `README.md` (both languages) and in
  section 1 of `docs/RULES.md`.
- `CHANGELOG.md` has an entry under a new `Unreleased` heading.

**Files.** `reportgate/readers.py`, `tests/test_readers.py`, `README.md`,
`docs/RULES.md`, `CHANGELOG.md`.

## 2. Test the path forms that have no test yet

`reportgate/extract.py` already understands several ways of writing a location that no
test covers. A test makes sure they keep working.

**Scope.** Add tests only; do not change `extract.py` unless a test shows a real bug.

**Acceptance criteria.** `tests/test_paths.py` has one test per form, each asserting the
exact `(path, line)` result:

- `src/app.py#L12` and `src/app.py#L12-L20` give line 12;
- `src/app.py 第 12 行` gives line 12;
- `src\app.py:5` (backslash) gives `src/app.py` and line 5;
- `src/app.py line 12` (no parentheses) gives line 12;
- `` `src/app.py`, line 3 `` gives line 3.

**Files.** `tests/test_paths.py`.

## 3. Translate the library section of the README into Chinese

The Chinese part of the README covers everything except "Use it as a library".

**Scope.** Add a `### 作为库使用` section to the Chinese part of `README.md`, right after
`### 它和扫描器有什么不同`, translating the English "Use it as a library" section.

**Acceptance criteria.**

- The code blocks are identical to the English ones; only the prose is translated.
- The terms match the rest of the Chinese text (for example 分诊, 结论, 报告格式).
- A second native Chinese reader approves the pull request.
- `python3 -m unittest discover -s tests -v` still passes (it checks the README sample).

**Files.** `README.md`.

## 4. Thank duplicate reporters for finding the issue independently

The duplicate reply tells the reporter their report is a repeat, but does not thank them
for finding the issue on their own, which matters to people who did real work.

**Scope.** Change the duplicate reply in `reportgate/replies.py`, in English and in
Chinese, so that it thanks the reporter for finding the issue independently. Keep
everything else it says, and keep it free of other reporters' names or report ids.

**Acceptance criteria.**

- Both languages say the same thing.
- `examples/expected/` is regenerated with
  `python3 -m reportgate examples/reports --repo examples/pastebox --out examples/expected`
  and the diff shows only the duplicate reply changing.
- All tests pass, including `test_duplicate_reply_does_not_reveal_the_other_report`.

**Files.** `reportgate/replies.py`, `examples/expected/reportgate.md`,
`examples/expected/reportgate.json`.

## 5. Test every recognised JSON field

`read_json` accepts several shapes for each field, but only some are tested.

**Scope.** Add tests only.

**Acceptance criteria.** `tests/test_readers.py` covers each of these:

- `description` and `body` both present: the body contains both, description first;
- `affected_files` as a comma-separated string, and `files` as a list of objects with a
  `path` key, together give the declared paths in order (`files` first);
- `cwe` as the string `"22"`, as `"CWE-22: Path traversal"`, and as a mixed list such as
  `[22, "CWE-79"]`;
- `proof_of_concept` behaves like `poc`, and both together are joined;
- `suggested_fix` is kept in `suggested_fix` and is not part of `body`;
- a missing `title` falls back to the first non-empty line of the body.

**Files.** `tests/test_readers.py`.
