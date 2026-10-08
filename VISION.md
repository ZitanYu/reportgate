# Vision

reportgate exists for one person: the maintainer of a small project who opens their
inbox to a pile of vulnerability reports and cannot tell which ones deserve the
evening. Some repeat each other. Some describe code that was rewritten a year ago. Some
are a scanner's output pasted with "URGENT" on top and nothing to reproduce. Reading all
of them carefully is the right thing to do and also impossible.

reportgate makes that first pass on the maintainer's own computer: it groups the
duplicates, checks every report against the code that exists today, scores how much of
a reproduction each one contains, and writes the reply the maintainer would have written
anyway. The maintainer still makes every decision. reportgate decides only where to look
first.

## What it will not become

reportgate **will not become a scanner.** It does not search code for bugs. Scanners are
good at that; reportgate starts after a report has already arrived.

reportgate **will not become a platform.** There will be no hosted service, no accounts,
no dashboard, no plugin store, and no bug-bounty workflow. It is a command and a library
that run where the code is.

reportgate **will not become a vulnerability oracle.** It will never say that something
is or is not a vulnerability, never rate exploitability, and never call a model to guess.
Every output says it is triage, not confirmation, and that stays true.

## Principles

- **Local and offline.** No network access, ever. Reports often contain undisclosed
  vulnerabilities; they should not leave the maintainer's machine.
- **Explainable.** Every verdict comes with the evidence and the rule that produced it.
  A maintainer should be able to predict reportgate after reading docs/RULES.md.
- **Deterministic.** The same input gives the same output, byte for byte.
- **Read-only.** reportgate never modifies the checkout, never runs a report's code, and
  never writes attack code.
- **Respectful replies.** Every reply is something a maintainer would be glad to have
  sent: polite, specific about what is missing, and honest that it is a first pass.
- **Small and dependency-free.** The standard library is enough. A tool that guards a
  maintainer's time should not cost them a dependency audit.
- **A stable contract.** The JSON schema is versioned so other projects can build on it.

## What a good change looks like

A good change makes a verdict more accurate on real reports, makes a reply clearer, adds
a report format, or adds a language. It comes with a minimal example report showing the
before and after. A change that adds network access, model calls, code execution, or a
hosted component will be declined, however useful it looks, because it would make
reportgate a different tool.
