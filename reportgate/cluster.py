"""Group reports that describe the same issue.

Two reports are linked when any one of these holds:

1. they name the same file **and** share a CWE (always, whatever the titles say);
2. they name the same file and their text overlap is at least ``SAME_FILE_OVERLAP``;
3. they share a CWE and their text overlap is at least ``SAME_CWE_OVERLAP``;
4. their text overlap alone is at least ``TEXT_ONLY_OVERLAP``.

Links are transitive: if A links to B and B links to C, all three form one
cluster. "Same file" also matches a bare name against a longer path that ends
with it (``storage.py`` and ``app/storage.py``). Text overlap is the Jaccard
index of word sets (CJK text is compared as character pairs).

Within a cluster the *primary* report is the one with the highest reproduction
score, then a verified location, then the earliest by report id. Every other
member gets the verdict ``duplicate``.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from .model import Cluster, ClusterLink, Evidence, Report
from .text import jaccard, tokens

SAME_FILE_OVERLAP = 0.25
SAME_CWE_OVERLAP = 0.45
TEXT_ONLY_OVERLAP = 0.6


def same_file(a: str, b: str) -> bool:
    return a == b or a.endswith("/" + b) or b.endswith("/" + a)


def _shared_files(a: Sequence[str], b: Sequence[str]) -> List[str]:
    shared: List[str] = []
    for x in a:
        for y in b:
            if same_file(x, y):
                name = x if len(x) >= len(y) else y
                if name not in shared:
                    shared.append(name)
    return shared


def link_rule(
    files_a: Sequence[str],
    files_b: Sequence[str],
    cwe_a: Sequence[str],
    cwe_b: Sequence[str],
    overlap: float,
) -> Tuple[Optional[str], List[str], List[str]]:
    """Decide whether two reports link. Returns ``(rule or None, files, cwes)``."""
    files = _shared_files(files_a, files_b)
    cwes = [c for c in cwe_a if c in cwe_b]
    if files and cwes:
        return "same file and same CWE", files, cwes
    if files and overlap >= SAME_FILE_OVERLAP:
        return "same file and similar text", files, cwes
    if cwes and overlap >= SAME_CWE_OVERLAP:
        return "same CWE and similar text", files, cwes
    if overlap >= TEXT_ONLY_OVERLAP:
        return "near-identical text", files, cwes
    return None, files, cwes


def cluster_reports(reports: Sequence[Report], evidence: Sequence[Evidence]) -> Dict[str, Cluster]:
    """Return a mapping from report id to its cluster, for reports in a cluster."""
    n = len(reports)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    files = [[c.path for c in ev.candidates if not c.escapes_repo] for ev in evidence]
    words = [tokens(r.title + "\n" + r.body) for r in reports]
    links: List[Tuple[int, int, ClusterLink]] = []
    for i in range(n):
        for j in range(i + 1, n):
            overlap = jaccard(words[i], words[j])
            rule, shared, cwes = link_rule(
                files[i], files[j], reports[i].cwe, reports[j].cwe, overlap
            )
            if rule is None:
                continue
            links.append(
                (
                    i,
                    j,
                    ClusterLink(
                        between=(reports[i].id, reports[j].id),
                        rule=rule,
                        shared_files=shared,
                        shared_cwe=cwes,
                        text_overlap=round(overlap, 2),
                    ),
                )
            )
            root_i, root_j = find(i), find(j)
            if root_i != root_j:
                parent[max(root_i, root_j)] = min(root_i, root_j)

    groups: Dict[int, List[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    clusters: Dict[str, Cluster] = {}
    number = 0
    for root in sorted(groups):
        members = groups[root]
        if len(members) < 2:
            continue
        number += 1
        primary = min(
            members,
            key=lambda k: (
                -evidence[k].reproduction.score,
                0 if evidence[k].path_exists else 1,
                k,
            ),
        )
        member_set = set(members)
        cluster = Cluster(
            id="C%d" % number,
            primary=reports[primary].id,
            members=[reports[k].id for k in members],
            links=[link for i, j, link in links if i in member_set and j in member_set],
        )
        for k in members:
            clusters[reports[k].id] = cluster
    return clusters
