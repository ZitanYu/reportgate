# reportgate triage

> **This is triage, not confirmation. reportgate compared the reports with each other and, when a checkout was given, with the code; it did not run, exploit, or confirm anything.**
>
> **这是分诊，不是确认。reportgate 只是把报告相互比较，并在提供了代码检出时与代码对照；它没有运行、利用或确认任何内容。**

- Reports: `examples/reports` (6)
- Tree: `examples/pastebox` (checked)
- reportgate 0.1.0, output schema 1

## Summary

| Verdict | Reports |
|---|---|
| duplicate | 1 |
| not in the current tree | 1 |
| missing location | 1 |
| missing minimal reproduction | 1 |
| worth human review | 1 |
| needs human judgment | 1 |

| Report | Verdict | Path | Exists | Line in range | Snippet | Repro | Clustered with |
|---|---|---|---|---|---|---|---|
| `01-upload-path-traversal.md` | worth human review | `pastebox/storage.py:16` | yes | yes | matches | 3/3 | `02-crafted-filename-write.json` |
| `02-crafted-filename-write.json` | duplicate | `pastebox/storage.py` | yes | n/a | none quoted | 3/3 | `01-upload-path-traversal.md` |
| `03-title-html-injection.md` | not in the current tree | `pastebox/templates.py:22` | no | n/a | not found | 3/3 | none |
| `04-large-paste.txt` | missing minimal reproduction | `pastebox/server.py` | yes | n/a | none quoted | 0/3 | none |
| `05-urgent-no-details.md` | missing location | none | n/a | n/a | none quoted | 1/3 | none |
| `06-link-regex-backtracking.json` | needs human judgment | `pastebox/render.py:6` | yes | yes | no match | 3/3 | none |

## 1. `01-upload-path-traversal.md`: worth human review（值得人工审查）

**Title:** Path traversal in upload storage · **Severity (as reported):** high · **CWE:** CWE-22

| Evidence | |
|---|---|
| Extracted path | `pastebox/storage.py` |
| Exists | yes |
| Line | 16 (in range; file has 27 lines) |
| Quoted snippet | matches |
| Reproduction score | 3/3: a code block plus steps or a payload |
| Clustered with | `02-crafted-filename-write.json` (C1, primary: same file and same CWE) |

**Why**

- `pastebox/storage.py` exists, line 16 is in range, and the quoted code matches.
- Reproduction score 3/3: a code block plus steps or a payload.

**Reply (English)**

```text
Hi,

Thank you for reporting "Path traversal in upload storage" to pastebox.

We ran an initial triage. The report points to `pastebox/storage.py` (line 16), which exists in the current code. The code you quoted matches that file, and the report includes a reproduction. A maintainer will now review it by hand.

This is triage, not confirmation: we have not confirmed whether the issue is exploitable. Please keep the details private until a fix is released; we will coordinate disclosure and credit with you.

— The maintainers
```

**回复（中文）**

```text
你好，

感谢你向 pastebox 报告「Path traversal in upload storage」。

我们做了初步分诊：报告指向 `pastebox/storage.py` 第 16 行，该位置在当前代码中存在，你引用的代码也与之一致，并且报告附带了复现。接下来会由维护者人工审查。

这是分诊，不是确认：我们尚未确认该问题是否可被利用。在修复发布之前，请不要公开细节；披露时间和致谢方式我们会与你商定。

—— 维护者
```

**Patch note**

```text
Patch note (draft) for: Path traversal in upload storage
Report: 01-upload-path-traversal.md
Also covers duplicates: 02-crafted-filename-write.json

- Exploitability: not confirmed. This note comes from triage; confirm the issue by hand before changing code.
- Where untrusted input enters: as described by the reporter, unverified: "The `X-Filename` request header is passed straight to `save_upload()`, so the filename is attacker-controlled."
- Path to fix: `pastebox/storage.py` (line 16)
- Weakness: CWE-22 (as reported)
- Release: publish the fix as a separate security release, not bundled with unrelated changes, and credit the reporter as agreed.
```

## 2. `02-crafted-filename-write.json`: duplicate（重复）

**Title:** Arbitrary file write via crafted X-Filename · **Severity (as reported):** critical · **CWE:** CWE-22

| Evidence | |
|---|---|
| Extracted path | `pastebox/storage.py` |
| Exists | yes |
| Line | none given |
| Quoted snippet | none quoted |
| Reproduction score | 3/3: a code block plus steps or a payload |
| Clustered with | `01-upload-path-traversal.md` (C1, duplicate of `01-upload-path-traversal.md`: same file and same CWE) |

Other paths in the report: `../owned.txt` (rejected: escapes the repository)

**Why**

- Clustered with `01-upload-path-traversal.md` (same file and same CWE); `01-upload-path-traversal.md` is the primary report.

**Reply (English)**

```text
Hi,

Thank you for reporting "Arbitrary file write via crafted X-Filename" to pastebox.

This appears to describe the same issue as a report we have already received, so we will track the two together rather than separately. If you have details the other report may not cover, such as another entry point, another affected version, or a smaller reproduction, please reply with them and we will add them.

This is an initial triage, not a confirmation or a rejection of the issue. Please keep the details private for now.

— The maintainers
```

**回复（中文）**

```text
你好，

感谢你向 pastebox 报告「Arbitrary file write via crafted X-Filename」。

这份报告描述的问题似乎与我们已经收到的另一份报告相同，因此我们会把两者合并跟踪，而不是分开处理。如果你掌握对方可能没有提到的细节，例如其他入口、其他受影响的版本，或更小的复现，请回复告诉我们，我们会补充进去。

这只是初步分诊，既不是确认，也不是否定。目前请不要公开细节。

—— 维护者
```

**Patch note:** No patch note: this report duplicates 01-upload-path-traversal.md; any patch note belongs to that report.

## 3. `03-title-html-injection.md`: not in the current tree（不在当前代码树中）

**Title:** HTML injection in paste titles · **Severity (as reported):** medium · **CWE:** CWE-79

| Evidence | |
|---|---|
| Extracted path | `pastebox/templates.py` |
| Exists | no |
| Line | 22 (not checked: file does not exist) |
| Quoted snippet | not compared (file missing); not found elsewhere in the tree |
| Reproduction score | 3/3: a code block plus steps or a payload |
| Clustered with | none |

**Why**

- `pastebox/templates.py` does not exist in the checkout.
- The quoted code does not appear anywhere in the checkout.

**Reply (English)**

```text
Hi,

Thank you for reporting "HTML injection in paste titles" to pastebox.

We compared the report with the current source tree and could not find what it describes: `pastebox/templates.py` does not exist in the current tree, and the code you quoted does not appear anywhere else. The code may have changed, moved, or been fixed since the version you tested.

Could you tell us which version or commit you tested, and whether the issue still reproduces on the latest code? If it does, please point us to the current file and line.

This is an initial triage, not a confirmation or a rejection of the issue.

— The maintainers
```

**回复（中文）**

```text
你好，

感谢你向 pastebox 报告「HTML injection in paste titles」。

我们把报告与当前源代码树做了对照，没有找到报告所描述的内容：当前代码树中不存在 `pastebox/templates.py`，你引用的代码也没有出现在其他任何位置。自你测试的版本以来，相关代码可能已被修改、移动或修复。

能否告诉我们你测试的是哪个版本或哪个提交，以及在最新代码上是否仍能复现？如果仍能复现，请告诉我们当前对应的文件和行号。

这只是初步分诊，既不是确认，也不是否定。

—— 维护者
```

**Patch note:** No patch note: the reported code is not in the current tree, so there is nothing here to fix yet.

## 4. `04-large-paste.txt`: missing minimal reproduction（缺少最小复现）

**Title:** Possible denial of service in pastebox/server.py

| Evidence | |
|---|---|
| Extracted path | `pastebox/server.py` |
| Exists | yes |
| Line | none given |
| Quoted snippet | none quoted |
| Reproduction score | 0/3: nothing |
| Clustered with | none |

**Why**

- Reproduction score 0/3: the report contains no reproduction.

**Reply (English)**

```text
Hi,

Thank you for reporting "Possible denial of service in pastebox/server.py" to pastebox.

We found the location the report refers to (`pastebox/server.py`), but the report does not include a minimal reproduction. Before a maintainer can review it, could you reply with:

- the exact steps that trigger the behaviour;
- the smallest input, request, or file that triggers it;
- what you expected to happen and what happened instead;
- the version or commit you tested.

This is an initial triage, not a confirmation or a rejection of the issue.

— The maintainers
```

**回复（中文）**

```text
你好，

感谢你向 pastebox 报告「Possible denial of service in pastebox/server.py」。

我们找到了报告所指的位置（`pastebox/server.py`），但报告没有附上最小复现。在维护者审查之前，能否回复以下信息：

- 触发该行为的确切步骤；
- 能触发它的最小输入、请求或文件；
- 你预期的结果，以及实际发生的结果；
- 你测试的版本或提交。

这只是初步分诊，既不是确认，也不是否定。

—— 维护者
```

**Patch note:** No patch note: without a minimal reproduction there is no basis for a fix yet.

## 5. `05-urgent-no-details.md`: missing location（缺少位置）

**Title:** URGENT: critical security vulnerability in your website

| Evidence | |
|---|---|
| Extracted path | none |
| Exists | n/a |
| Line | none given |
| Quoted snippet | none quoted |
| Reproduction score | 1/3: only a mention |
| Clustered with | none |

**Why**

- The report names no file path.

**Reply (English)**

```text
Hi,

Thank you for reporting "URGENT: critical security vulnerability in your website" to pastebox.

We could not find a file path in the report, so we cannot yet check it against the code. Could you reply with:

- the file path, relative to the repository root, and the line number if you can;
- where untrusted input enters, such as a request field, a file, or a command-line argument;
- the version or commit you tested.

This is an initial triage, not a confirmation or a rejection of the issue.

— The maintainers
```

**回复（中文）**

```text
你好，

感谢你向 pastebox 报告「URGENT: critical security vulnerability in your website」。

我们在报告中没有找到文件路径，因此暂时无法与代码对照。能否回复以下信息：

- 文件路径（相对于仓库根目录），如有可能请附上行号；
- 不可信输入从哪里进入，例如某个请求字段、某个文件或某个命令行参数；
- 你测试的版本或提交。

这只是初步分诊，既不是确认，也不是否定。

—— 维护者
```

**Patch note:** No patch note: the report gives no usable location in the repository.

## 6. `06-link-regex-backtracking.json`: needs human judgment（需要人工判断）

**Title:** Catastrophic backtracking in link detection · **Severity (as reported):** medium · **CWE:** CWE-1333

| Evidence | |
|---|---|
| Extracted path | `pastebox/render.py` |
| Exists | yes |
| Line | 6 (in range; file has 14 lines) |
| Quoted snippet | does not match; not found elsewhere in the tree |
| Reproduction score | 3/3: a code block plus steps or a payload |
| Clustered with | none |

**Why**

- `pastebox/render.py` exists, but the quoted code does not match it.

**Reply (English)**

```text
Hi,

Thank you for reporting "Catastrophic backtracking in link detection" to pastebox.

Our initial triage could not settle this report automatically:

- `pastebox/render.py` exists, but the quoted code does not match it.

A maintainer will look at it by hand and may come back with questions. If you can tell us which version or commit you tested, that will help.

This is triage, not confirmation: we have not confirmed whether the issue is exploitable. Please keep the details private while we review it.

— The maintainers
```

**回复（中文）**

```text
你好，

感谢你向 pastebox 报告「Catastrophic backtracking in link detection」。

初步分诊无法自动得出结论：

- `pastebox/render.py` 存在，但引用的代码与它不一致。

维护者会人工查看，之后可能会向你提问。如果你能告诉我们测试的版本或提交，会很有帮助。

这是分诊，不是确认：我们尚未确认该问题是否可被利用。审查期间请不要公开细节。

—— 维护者
```

**Patch note**

```text
Patch note (draft) for: Catastrophic backtracking in link detection
Report: 06-link-regex-backtracking.json

- Exploitability: not confirmed. This note comes from triage; confirm the issue by hand before changing code.
- Where untrusted input enters: not stated in the report; establish it before writing a fix.
- Path to fix: `pastebox/render.py` (line 6)
- Weakness: CWE-1333 (as reported)
- Open questions: `pastebox/render.py` exists, but the quoted code does not match it.
- Release: publish the fix as a separate security release, not bundled with unrelated changes, and credit the reporter as agreed.
```
