# Output schema

reportgate writes the same data in two forms: `reportgate.json` for programs and
`reportgate.md` for people. This page documents the JSON. The library returns the
same structure from `reportgate.to_dict(run)`.

**Current version: `schema_version` 1.**

## Stability promise

- Within one `schema_version`, fields are only ever **added**. No field is removed,
  renamed, or changes type or meaning.
- The six verdict strings and every reason `code` keep their meaning for as long as
  the schema version stays the same.
- A breaking change increases `schema_version` and is listed in `CHANGELOG.md`.
- Programs should ignore fields they do not know.
- Output is deterministic: the same reports and the same checkout give the same
  bytes. There is no timestamp.
- `tests/test_schema.py` checks that every field below is present in real output and
  that no undocumented field appears, so this page cannot silently drift.

## Top level

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | integer | `1`. |
| `tool` | object | The program that wrote the file. |
| `tool.name` | string | Always `"reportgate"`. |
| `tool.version` | string | Semantic version, for example `"0.1.0"`. |
| `notice` | object | The statement that this output is triage, not confirmation. |
| `notice.en` | string | In English. |
| `notice.zh` | string | In Chinese. |
| `reports_dir` | string or null | The reports directory as given, with `/` separators. `null` for in-memory reports. |
| `tree` | object | Whether a checkout was compared. |
| `tree.checked` | boolean | `false` when no checkout was given. Every location field is then `null` and each result carries the reason `tree_not_checked`. |
| `tree.path` | string or null | The checkout as given, with `/` separators. |
| `summary` | object | Counts. |
| `summary.total` | integer | Number of reports. |
| `summary.by_verdict` | object | Each of the six verdict strings mapped to a count (zero included). |
| `results` | array | One entry per report, in the order the reports were read (sorted by path). |
| `skipped` | array | Files that were not read. |
| `skipped[].source` | string | Path relative to the reports directory. |
| `skipped[].reason` | string | Why it was skipped (unsupported type, invalid JSON, too large). |

## Each result

| Field | Type | Meaning |
|---|---|---|
| `results[].id` | string | Path relative to the reports directory. Reports from a JSON array get `#1`, `#2`, ... appended. |
| `results[].format` | string | `"markdown"`, `"text"`, `"json"`, or whatever a custom reader sets. |
| `results[].title` | string | The report's title, or its first line. |
| `results[].severity` | string or null | Severity as the reporter stated it. Never used to decide a verdict. |
| `results[].cwe` | array of strings | CWE ids such as `"CWE-22"`, from the `cwe` field or the text. |
| `results[].verdict` | string | One of the six verdicts below. |
| `results[].verdict_code` | string | The same verdict as a snake_case identifier. |
| `results[].verdict_zh` | string | The verdict in Chinese. |
| `results[].reasons` | array | Why this verdict, in rule order. |
| `results[].reasons[].code` | string | Stable machine code, listed below. |
| `results[].reasons[].en` | string | The reason in English. |
| `results[].reasons[].zh` | string | The reason in Chinese. |
| `results[].evidence` | object | What was observed. |
| `results[].evidence.path` | string or null | The extracted path: the best location the report names (see docs/RULES.md). Shown even when rejected. |
| `results[].evidence.path_exists` | boolean or null | Whether that file exists in the checkout. `null` when the tree was not checked or the path escapes. |
| `results[].evidence.path_escapes_repo` | boolean | `true` if the path is absolute, climbs out with `..`, or resolves through a link to outside the checkout. Such paths are never read. |
| `results[].evidence.line` | integer or null | Line number the report gives for that path. |
| `results[].evidence.line_in_range` | boolean or null | Whether the line is between 1 and the file's line count. `null` when there is no line, no file, or no checkout. |
| `results[].evidence.file_lines` | integer or null | Line count of the file, when it was read. |
| `results[].evidence.snippet_quoted` | boolean | Whether the report quotes code from the project (a fenced block that is not a proof of concept or a diff). |
| `results[].evidence.snippet_match` | boolean or null | Whether the quote matches the file at `path`. `null` when nothing is quoted, the file is missing, or the tree was not checked. |
| `results[].evidence.snippet_found_in` | array of strings | Other files in the checkout that contain the quote (at most five). |
| `results[].evidence.reproduction_score` | integer | 0 to 3. |
| `results[].evidence.reproduction_label` | string | `"nothing"`, `"only a mention"`, `"steps or a code block, but incomplete"`, or `"a code block plus steps or a payload"`. |
| `results[].evidence.reproduction_signals` | object | The signals behind the score. |
| `results[].evidence.reproduction_signals.mention` | boolean | Words such as reproduce, PoC, exploit, 复现. |
| `results[].evidence.reproduction_signals.steps` | boolean | Two or more numbered steps, or two or more bullets under a steps heading. |
| `results[].evidence.reproduction_signals.code_block` | boolean | A fenced code block that is not a diff. |
| `results[].evidence.reproduction_signals.payload` | boolean | A recognisable payload shape in the text. Detected, never generated. |
| `results[].evidence.entry_point` | string or null | The reporter's own sentence about where untrusted input enters. Quoted, not verified. |
| `results[].evidence.candidates` | array | Every path the report names, in order. |
| `results[].evidence.candidates[].path` | string | Normalised path. |
| `results[].evidence.candidates[].line` | integer or null | Line given with it. |
| `results[].evidence.candidates[].origin` | string | `"declared"` (a JSON `files` or `affected_files` entry) or `"text"`. |
| `results[].evidence.candidates[].escapes_repo` | boolean | Rejected as outside the repository. |
| `results[].evidence.candidates[].exists` | boolean or null | Exists in the checkout. |
| `results[].evidence.clustered_with` | array of strings | Ids of the other reports in the same cluster. Empty when alone. |
| `results[].evidence.duplicate_of` | string or null | The cluster's primary report, when this report is a duplicate. |
| `results[].evidence.cluster` | object or null | The cluster, when there is one. |
| `results[].evidence.cluster.id` | string | `"C1"`, `"C2"`, ... in order of first member. |
| `results[].evidence.cluster.primary` | string | Id of the primary report. |
| `results[].evidence.cluster.members` | array of strings | All member ids, in report order. |
| `results[].evidence.cluster.links` | array | Each pair that was linked directly. |
| `results[].evidence.cluster.links[].between` | array of two strings | The two report ids. |
| `results[].evidence.cluster.links[].rule` | string | `"same file and same CWE"`, `"same file and similar text"`, `"same CWE and similar text"`, or `"near-identical text"`. |
| `results[].evidence.cluster.links[].shared_files` | array of strings | Files both reports name. |
| `results[].evidence.cluster.links[].shared_cwe` | array of strings | CWE ids both reports give. |
| `results[].evidence.cluster.links[].text_overlap` | number | Jaccard overlap of the two texts, 0 to 1, two decimals. |
| `results[].reply` | object | Replies ready to paste. |
| `results[].reply.en` | string | In English. |
| `results[].reply.zh` | string | In Chinese. |
| `results[].patch_note` | string or null | Written only for `worth human review` and `needs human judgment`. |
| `results[].patch_note_reason` | string or null | When there is no patch note, why not. `null` when there is one. |

## Verdicts

| `verdict` | `verdict_code` | `verdict_zh` |
|---|---|---|
| duplicate | `duplicate` | 重复 |
| not in the current tree | `not_in_current_tree` | 不在当前代码树中 |
| missing location | `missing_location` | 缺少位置 |
| missing minimal reproduction | `missing_minimal_reproduction` | 缺少最小复现 |
| worth human review | `worth_human_review` | 值得人工审查 |
| needs human judgment | `needs_human_judgment` | 需要人工判断 |

## Reason codes

| Code | Appears with |
|---|---|
| duplicate_of | duplicate |
| no_path | missing location |
| all_paths_escape | missing location |
| path_missing | not in the current tree |
| snippet_not_found | not in the current tree |
| line_out_of_range | not in the current tree, needs human judgment, missing minimal reproduction |
| snippet_mismatch | needs human judgment, missing minimal reproduction |
| snippet_elsewhere | needs human judgment, missing minimal reproduction |
| code_moved | needs human judgment, missing minimal reproduction |
| no_reproduction | missing minimal reproduction |
| reproduction_mention_only | missing minimal reproduction |
| reproduction_incomplete | needs human judgment |
| location_verified | worth human review |
| reproduction_present | worth human review |
| tree_not_checked | any verdict except duplicate and missing location, when no checkout was given |
