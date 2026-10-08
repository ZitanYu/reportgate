# How reportgate decides

reportgate is deliberately simple: a handful of text rules that a maintainer can read
in ten minutes and predict. This page describes all of them. If a verdict surprises
you, the evidence table in the output tells you which rule produced it, and the
"Wrong verdict" issue template is the place to say so.

Nothing here runs a report, contacts a server, or asks a model. Everything is
deterministic: the same reports and checkout always give the same output.

## 1. Reading reports

Files are read recursively from the reports directory in path order. Hidden files and
directories are skipped. The reader is chosen by extension (`.md`, `.markdown`, `.txt`,
`.json`); other files are listed under "Skipped files". A file over 2 MB is skipped.

For Markdown and plain text, the first non-empty line is the title. A section headed
"Suggested fix", "Fix", "Remediation", "Mitigation", "Patch", "修复建议" or similar is set
aside as the reporter's suggested fix. It is used to find file paths but is never scored
as a reproduction or compared as a quote, because a fix is new code, not current code.

For JSON, `description` and `body` form the text; `poc` and `proof_of_concept` are added
as a proof-of-concept block; `files` and `affected_files` are *declared* paths; `cwe`
accepts `"CWE-22"`, `"22"`, `22`, or a list. A JSON array yields one report per element.
Code: `reportgate/readers.py`.

## 2. Finding the location

Paths are collected from declared fields first, then from the text. In the text, only
prose and inline code are searched; fenced code blocks are skipped, because a path in a
proof of concept is a payload (`../../x`), not a location. URLs are removed first.

A path with a directory part (`src/app.py`) is accepted with any extension. A bare name
(`server.py`) is accepted only with a source-code extension, so that `example.com` and
`e.g.` are not mistaken for files. A line number is read from `path:12`, `path#L12`,
`path (line 12)`, `path line 12`, `path 第 12 行`, or `line 12 of path`.

The **extracted path** is the first of these that applies: a path that exists in the
checkout; then a declared path; then a path given with a line number; then the first
path mentioned. Paths that escape the repository are only used if nothing else is left,
so that the output can show what was rejected. Code: `reportgate/extract.py`.

## 3. Checking against the checkout

A path **escapes the repository** if it is absolute (`/etc/passwd`, `C:\...`, `~/...`),
climbs above the root with `..`, or resolves through a symbolic link to somewhere outside
the checkout. Such a path is never opened.

For the extracted path, reportgate records whether the file exists, its line count, and
whether the given line is between 1 and that count.

A **quoted snippet** is a fenced code block that is neither a diff nor a proof of
concept. A block counts as a proof of concept when it is marked `sh`, `bash`, `console`,
`http`, `poc` and similar, starts with a shell prompt or a command such as `curl`, or
contains a recognisable payload. Each quote is reduced to its lines of six or more
characters, with whitespace collapsed. The quote **matches** a file when at least 60% of
those lines occur in it. If it does not match the extracted path, the rest of the
checkout is searched (text files up to 1 MB, skipping `.git`, `node_modules`, build
directories and hidden directories) and up to five other files containing it are listed.
Code: `reportgate/tree.py`, `reportgate/core.py`.

## 4. Scoring the reproduction

| Score | Meaning | Rule |
|---|---|---|
| 0 | nothing | none of the signals below |
| 1 | only a mention | words such as reproduce, PoC, proof of concept, exploit, trigger, 复现; or a payload in prose |
| 2 | steps or a code block, but incomplete | two or more numbered steps (or bullets under a steps heading), or a fenced code block |
| 3 | a code block plus steps or a payload | a fenced code block, and steps or a payload |

A `diff` or `patch` block is not a code block for this purpose. Payload shapes are
detected in text the reporter already wrote; reportgate never generates one.
Code: `reportgate/repro.py`.

## 5. Clustering

Two reports are linked if any of these holds:

| Rule | Condition |
|---|---|
| same file and same CWE | they name the same file and share a CWE, whatever the titles say |
| same file and similar text | same file, text overlap at least 0.25 |
| same CWE and similar text | shared CWE, text overlap at least 0.45 |
| near-identical text | text overlap at least 0.6 |

"Same file" also matches a bare name against a longer path ending with it. Text overlap
is the Jaccard index of the two reports' word sets, ignoring very common words; Chinese,
Japanese and other CJK text is compared as character pairs. Links are transitive.

In each cluster the **primary** report is the one with the highest reproduction score,
then one whose file exists, then the first by id. Every other member is a duplicate.
Code: `reportgate/cluster.py`.

## 6. Choosing the verdict

The first rule that applies wins.

1. **duplicate**: in a cluster and not its primary.
2. **missing location**: no path at all, or every path escapes the repository.
3. **not in the current tree** (checkout given): the extracted file does not exist and
   the quoted code is nowhere in the checkout; or the file exists, the line is past its
   end, and the quoted code is nowhere in the checkout.
4. **missing minimal reproduction**: reproduction score 0 or 1.
5. **needs human judgment**: the file exists but the quote does not match it; the line is
   past the end of the file and no quote confirms the location; the file is gone but the
   quote appears elsewhere; or the reproduction scores 2.
6. **worth human review**: everything else, which means a usable location and a
   reproduction scoring 3.

Without a checkout, rules 3 and the location checks in rule 5 cannot run. Every result
then carries the reason `tree_not_checked`, and the output says the tree was not checked.
The severity a reporter claims is shown but never used. Code: `reportgate/decide.py`.

## 7. Replies and patch notes

Each verdict has a fixed reply in English and in Chinese that asks for exactly what is
missing. Replies never name another reporter's report, never confirm a vulnerability, and
always say that this is triage. They are signed "The maintainers" / "维护者" unless you
pass `--signature`.

A patch note is written only for **worth human review** and **needs human judgment**.
It states that exploitability is not confirmed, where untrusted input enters (the
reporter's own sentence, quoted and marked unverified, or a note that the report does not
say), which path would be fixed, and that the fix should ship as a separate security
release. For the other verdicts the output gives the reason no patch note was written.
Code: `reportgate/replies.py`.

## Limits

These rules read text; they do not understand code. reportgate will sometimes cluster
two different issues in one file, miss a duplicate written in different words, or call a
report incomplete when its reproduction is in an attachment. That is why the output is
labelled triage: it orders a maintainer's work, it does not replace the maintainer.
