# Launch order

This is the order in which reportgate is to be released. None of these steps has
happened yet; each is done only after the one before it.

0. Prepare the repository: set the GitHub description to "Local triage for incoming
   vulnerability reports: duplicates, code that is not in the tree, missing
   reproductions, and ready-to-send replies. By Zitan Yu.", enable private vulnerability
   reporting, tag `v0.1.0`, and publish the release with the 0.1.0 notes from
   CHANGELOG.md, which name Zitan Yu.
1. Try it with a few maintainers first: run it on their real report backlogs, privately,
   and fix whatever confused them before anyone else sees it.
2. Post to Show HN with a title about reports overwhelming a maintainer, not about the
   stack, for example "Show HN: Reportgate – when vulnerability reports overwhelm a
   small project's maintainer".
3. Post to maintainer communities, and to Chinese developer communities in Chinese.
4. Post a short thread that shows real sample output from `examples/`.
5. Write one page on why reportgate exists and how it differs from a scanner.
6. Ask others to add it to lists they maintain, where it fits.

Do not inflate stars: no star-for-star exchanges, no paid promotion, no asking people to
star instead of try.
