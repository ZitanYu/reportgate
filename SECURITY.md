# Security policy

Security maintainer: Zitan Yu

安全维护者：Zitan Yu

Zitan Yu receives, confirms, and publishes security fixes for this project.

## Reporting a vulnerability in reportgate

Reports about this tool go privately to Zitan Yu, and not in a public issue, before a fix is released.

Send them to Zitan Yu in either of these ways:

- email: <security@zitanyu.com>
- GitHub private vulnerability reporting:
  <https://github.com/ZitanYu/reportgate/security/advisories/new>

A report needs:

1. the reportgate version or commit;
2. a minimal reproduction;
3. the impact you expect.

Receipt is acknowledged within 7 days. After that, Zitan Yu confirms the issue, prepares a fix, publishes it as a separate security release, and credits you if you wish.

## What counts

reportgate reads untrusted reports and a local checkout, so these are in scope:

- reading, or revealing anything about, a file outside the checkout given with `--repo` (for example a path-escape or symbolic-link bypass);
- any network access, code execution, or write to the checkout caused by a report;
- a report file that makes reportgate hang or use unbounded memory;
- output that injects content a maintainer would not expect when pasted (for example breaking out of a reply block).

Out of scope:

- the intentional flaw in `examples/pastebox`, which exists so the examples have something to point at;
- disagreeing with a verdict, which is a normal bug: open a "Wrong verdict" issue instead.

## Supported versions

Security fixes are made for the latest released version.

---

## 安全策略（中文）

安全维护者：Zitan Yu

Zitan Yu 负责接收、确认并发布本项目的安全修复。

关于 reportgate 本身的漏洞报告，请私下发送给 Zitan Yu，在修复发布之前不要提交公开 issue。可以通过以下任一方式发送：

- 电子邮件：<security@zitanyu.com>
- GitHub 私密漏洞报告：<https://github.com/ZitanYu/reportgate/security/advisories/new>

报告需要包含：reportgate 的版本或提交、最小复现，以及预期影响。我们会在 7 天内确认收到。之后 Zitan Yu 会确认问题、准备修复，并以单独的安全版本发布；如你愿意，我们会在发布说明中致谢。

`examples/pastebox` 中的缺陷是有意保留的示例，不属于安全问题；对分诊结论有异议请提交普通的 “Wrong verdict” issue。
