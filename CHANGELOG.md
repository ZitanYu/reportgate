# Changelog

All notable changes to reportgate are recorded here. The project follows
[Semantic Versioning](https://semver.org/) and the format of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Changes to the JSON
output are called out separately, because other programs depend on it.

## [0.1.0]

First public release, by Zitan Yu (author and security maintainer).

### Added

- `reportgate` command and importable `reportgate` library that run the same rules.
- Readers for Markdown, plain text, and JSON reports, replaceable per file extension.
- Six verdicts: duplicate; not in the current tree; missing location; missing minimal
  reproduction; worth human review; needs human judgment.
- Evidence for every report: extracted path, whether it exists, whether the line is in
  range, whether a quoted snippet matches, reproduction score from 0 to 3, and cluster.
- Clustering on shared files, identical CWE, and text overlap; the same file plus the
  same CWE always clusters.
- Rejection of paths that escape the repository, including through symbolic links.
- Ready-to-paste replies in English and Chinese.
- Patch notes only for "worth human review" and "needs human judgment", with the reason
  for every other verdict.
- Markdown and JSON output; JSON output schema version 1, documented in docs/SCHEMA.md.
- Exit code 2 for a missing or empty reports directory or a bad checkout; 0 on success.
- Examples that produce all six verdicts, with their expected output checked by tests.

[0.1.0]: https://github.com/ZitanYu/reportgate/releases/tag/v0.1.0
