# reportgate

**reportgate runs on a maintainer's own computer and sorts a batch of incoming vulnerability reports into duplicates, reports that do not match the current code, and reports with no minimal reproduction, then writes a reply that can be sent as-is, plus a patch note only when one should be written.**

**reportgate 在维护者自己的电脑上运行，把收到的一批漏洞报告分成重复的、与当前代码对不上的、没有最小复现的几类，然后写好可以直接发送的回复，并且只在确实应该写的时候才写补丁说明。**

Author and security maintainer: Zitan Yu.

[English](#english) · [中文](#中文)

<a id="english"></a>

## Try it in 30 seconds

```sh
git clone https://github.com/ZitanYu/reportgate && cd reportgate && python3 -m reportgate examples/reports --repo examples/pastebox
```

That is the whole setup: Python 3.10 or newer and nothing else to install. On Windows, type `py` instead of `python3`.

The six example reports in `examples/reports` come out as **worth human review**, **duplicate**, **not in the current tree**, **missing minimal reproduction**, **missing location**, and **needs human judgment**, one each. `examples/pastebox` is a tiny sample project they point at.

## Sample output

This is the start of the real output of the command above. The full output is in [`examples/expected/reportgate.md`](examples/expected/reportgate.md), and a test checks that this sample matches it.

<!-- sample-output:start -->
````text
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
[...]
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
````
<!-- sample-output:end -->

## Install

reportgate has no dependencies. Install it from the repository:

```sh
python3 -m pip install git+https://github.com/ZitanYu/reportgate
```

or from a clone:

```sh
git clone https://github.com/ZitanYu/reportgate
cd reportgate
python3 -m pip install .
```

Both give you the `reportgate` command and the `reportgate` library. You can also run it without installing, from a clone, with `python3 -m reportgate`.

## Use it on your own reports

Put the reports you received in one directory, one file per report (Markdown, plain text, or JSON), and point reportgate at it and at your checkout:

```sh
reportgate ~/inbox/security --repo ~/src/myproject --out triage/
```

This writes `triage/reportgate.md` for you to read and `triage/reportgate.json` for scripts. Without `--out`, the Markdown is printed; add `--json` to print JSON instead.

| Option | Meaning |
|---|---|
| `REPORTS_DIR` | Directory of `.md`, `.markdown`, `.txt`, and `.json` reports. Read recursively; hidden files are ignored. |
| `--repo PATH` | Your local checkout. Without it, reportgate says the tree was not checked and cannot tell whether code still exists. |
| `--out DIR` | Write `reportgate.md` and `reportgate.json` into `DIR`. |
| `--json` | Print JSON instead of Markdown. |
| `--project NAME` | Project name used in replies. Defaults to the checkout's directory name. |
| `--signature TEXT` | How replies are signed. Defaults to "The maintainers" and "维护者". |

Exit code 0 means the run succeeded, whatever the verdicts. Exit code 2 means the reports directory is missing or holds no reports, or `--repo` is not a directory.

JSON reports may use these fields: `title`, `body`, `description`, `severity`, `cwe`, `files`, `affected_files`, `poc`, `proof_of_concept`, `suggested_fix`. A file may hold one object or an array of objects.

## What it decides

Every report gets exactly one verdict, the evidence behind it, a reply in English and in Chinese, and either a patch note or the reason there is none.

| Verdict | Meaning | Patch note |
|---|---|---|
| duplicate | Same issue as another report in the batch. | No; it belongs to the primary report. |
| not in the current tree | The named file or the quoted code is not in your checkout. | No; there is nothing to fix yet. |
| missing location | No file path, or only paths outside the repository. | No. |
| missing minimal reproduction | A location, but a reproduction score of 0 or 1. | No. |
| needs human judgment | The signals conflict, or the reproduction is incomplete. | Yes. |
| worth human review | A real location and a full reproduction. | Yes. |

For every report the evidence shows the extracted path, whether it exists, whether the line is in range, whether the quoted snippet matches, the reproduction score from 0 to 3, and which reports it was clustered with. Reports are clustered on shared files, identical CWE, and text overlap; two reports that name the same file and the same CWE are always clustered, whatever their titles. The exact rules and thresholds are in [docs/RULES.md](docs/RULES.md), and the JSON format in [docs/SCHEMA.md](docs/SCHEMA.md).

A patch note states that exploitability is not confirmed, where untrusted input enters (quoting the reporter, unverified), which path would be fixed, and that the fix should ship as a separate security release.

## How this differs from a scanner

A scanner reads your code and looks for bugs. reportgate does not look for bugs at all. It reads reports that other people already sent you and helps you decide which ones deserve your time today: which are repeats, which describe code you no longer have, and which give you nothing to reproduce.

It is also not a vulnerability database, a bug-bounty platform, a dependency bot, or a hosted service. It never uses the network, never calls a model, never runs or writes attack code, never changes your code, never opens issues, and never confirms a vulnerability. Its output says so: **this is triage, not confirmation.** See [VISION.md](VISION.md) for what it will not become.

## Use it as a library

The command and the library run the same code, so another project can depend on reportgate and get the same verdicts.

```python
import reportgate

run = reportgate.triage("reports/", repo=".")
for result in run.results:
    print(result.report.id, result.verdict, result.evidence.reproduction.score)

print(reportgate.render_json(run))  # the documented, stable JSON
```

Report formats are replaceable functions. A reader takes the file's text and its id and returns a list of `Report` objects:

```python
from reportgate import DEFAULT_READERS, Report, triage


def read_eml(text, report_id):
    subject, _, body = text.partition("\n\n")
    return [Report(id=report_id, title=subject.strip(), body=body)]


run = triage("reports/", repo=".", readers={**DEFAULT_READERS, ".eml": read_eml})
```

Reports you already hold in memory go through `reportgate.triage_reports(reports, repo=...)`.

## First contribution

You do not need to write code to help. Documentation, translation, reproduction, and triage are all welcome:

- **Reproduction:** if reportgate gave one of your real reports the wrong verdict, strip anything secret, then open a "Wrong verdict" issue with a minimal version of it. A minimal report that reproduces a wrong verdict is the most useful contribution there is.
- **Translation:** the replies and README are in English and Chinese; improvements from native readers of either are welcome, and so are new languages.
- **Documentation:** if a step in this README did not work for you, that is a bug.
- **Triage:** help reproduce and label incoming issues.

Five scoped starter tasks, each with acceptance criteria and the files to touch, are in [docs/good-first-issues.md](docs/good-first-issues.md). [CONTRIBUTING.md](CONTRIBUTING.md) has the exact commands for tests and formatting; they are the same commands CI runs.

## Security: response within 7 days

To report a vulnerability in reportgate itself, do not open a public issue. Report it privately to Zitan Yu by email to [security@zitanyu.com](mailto:security@zitanyu.com), or through [GitHub private vulnerability reporting](https://github.com/ZitanYu/reportgate/security/advisories/new). Include the version or commit, a minimal reproduction, and the impact you expect. Receipt is acknowledged within 7 days. Details are in [SECURITY.md](SECURITY.md).

## License

MIT. Copyright (c) 2026 Zitan Yu. See [LICENSE](LICENSE).

Author and security maintainer: Zitan Yu.

---

<a id="中文"></a>

## 中文

**reportgate 在维护者自己的电脑上运行，把收到的一批漏洞报告分成重复的、与当前代码对不上的、没有最小复现的几类，然后写好可以直接发送的回复，并且只在确实应该写的时候才写补丁说明。**

作者兼安全维护者：Zitan Yu。

### 30 秒试用

```sh
git clone https://github.com/ZitanYu/reportgate && cd reportgate && python3 -m reportgate examples/reports --repo examples/pastebox
```

只需要 Python 3.10 或更新版本，不需要安装任何其他东西。Windows 上请用 `py` 代替 `python3`。

`examples/reports` 里的六份示例报告会分别得到：**值得人工审查**（worth human review）、**重复**（duplicate）、**不在当前代码树中**（not in the current tree）、**缺少最小复现**（missing minimal reproduction）、**缺少位置**（missing location）和**需要人工判断**（needs human judgment）。`examples/pastebox` 是它们所指向的一个小型示例项目。上面的[示例输出](#sample-output)就是这条命令的真实输出。

### 安装

reportgate 没有任何依赖：

```sh
python3 -m pip install git+https://github.com/ZitanYu/reportgate
```

或者在克隆下来的目录里运行 `python3 -m pip install .`。安装后可以使用 `reportgate` 命令和 `reportgate` 库；不安装也可以在克隆目录中直接运行 `python3 -m reportgate`。

### 用在你自己的报告上

把收到的报告放进一个目录（每份报告一个文件，支持 Markdown、纯文本和 JSON），然后运行：

```sh
reportgate ~/inbox/security --repo ~/src/myproject --out triage/
```

会生成供人阅读的 `triage/reportgate.md` 和供脚本使用的 `triage/reportgate.json`。不加 `--repo` 时，输出会明确说明没有检查代码树。退出码 0 表示运行成功（与结论无关）；报告目录不存在、为空，或 `--repo` 不是目录时，退出码为 2。

### 它会给出什么结论

每份报告只得到一个结论，并附上证据、中英文回复，以及补丁说明或不写补丁说明的原因。证据包括：提取到的路径、文件是否存在、行号是否在范围内、引用的代码片段是否一致、0 到 3 分的复现评分，以及与哪些报告归为一组。只有“值得人工审查”和“需要人工判断”会写补丁说明；补丁说明会写明尚未确认可利用性、不可信输入从哪里进入、需要修复的路径，以及安全修复应单独发布。规则细节见 [docs/RULES.md](docs/RULES.md)，JSON 格式见 [docs/SCHEMA.md](docs/SCHEMA.md)。

### 它和扫描器有什么不同

扫描器读你的代码、寻找漏洞。reportgate 完全不找漏洞：它读别人已经发给你的报告，帮你判断今天哪些值得花时间，哪些是重复的，哪些描述的代码已经不存在，哪些根本无法复现。它不联网、不调用模型、不运行或编写攻击代码、不修改你的代码、不开 issue，也不确认任何漏洞。**这是分诊，不是确认。**

### 第一次贡献

不写代码也可以贡献：文档、翻译、复现和分诊都非常欢迎。如果 reportgate 对你的某份真实报告给出了错误结论，请先删去所有敏感信息，再用 “Wrong verdict” 模板提交一个最小化的版本。五个适合新手的任务（含范围、验收标准和涉及的文件）见 [docs/good-first-issues.md](docs/good-first-issues.md)，测试和格式化命令见 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 安全问题：7 天内回复

如果你发现的是 reportgate 本身的漏洞，请不要公开提 issue，而是通过电子邮件 [security@zitanyu.com](mailto:security@zitanyu.com) 或 [GitHub 私密漏洞报告](https://github.com/ZitanYu/reportgate/security/advisories/new)私下报告给 Zitan Yu，并附上版本或提交、最小复现和预期影响。我们会在 7 天内确认收到。详见 [SECURITY.md](SECURITY.md)。

### 许可证

MIT 许可证，版权所有 (c) 2026 Zitan Yu。

作者兼安全维护者：Zitan Yu。
