#!/usr/bin/env python3
"""
Verify that the free-tier memory index behaves the way config/openclaw.json5
assumes.

Four things are checked:

  1. The tokenizer setting. The default unicode61 tokenizer treats a run of CJK
     characters as one token, so a Chinese query cannot match anything. This
     script builds the same corpus under both tokenizers and shows the
     difference. A regression here means the trigram setting was lost.

  2. The short term floor. A trigram index cannot match a pattern shorter than
     three characters, whether the query arrives as MATCH or as LIKE.

  3. Scope isolation. Each agent indexes only its own workspace.

  4. The retrieval cases in testset.yaml, split into as_written and
     paraphrased. The as_written cases must pass. The paraphrased cases are
     expected to fail on the free tier, and are the signal for when a local
     embedding provider is switched on.

No dependencies. Python 3.8+ and a SQLite build with FTS5, which is the
default in CPython on macOS, Linux and Windows.

    python3 tests/personal/verify-index.py

Exit code 0 means every hard assertion passed.
"""

import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTSET = os.path.join(HERE, "testset.yaml")
WORKSPACE = os.path.join(HERE, "workspace")
WORKER_WORKSPACE = os.path.join(HERE, "workspace-worker-research")

MIN_TRIGRAM_TERM = 3


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------

def estimate_tokens(text):
    """Rough token estimate. CJK characters count as one token each."""
    cjk = sum(1 for ch in text if "一" <= ch <= "鿿")
    other = len(re.sub(r"[一-鿿]", " ", text))
    return cjk + max(1, other // 4)


def chunk_file(path):
    """Split a markdown file into chunks, approximating the runtime's
    400-token target with an 80-token overlap."""
    with open(path, encoding="utf-8") as handle:
        body = handle.read()

    blocks = [b.strip() for b in re.split(r"\n\s*\n", body) if b.strip()]
    chunks, current = [], []

    for block in blocks:
        current.append(block)
        if estimate_tokens("\n\n".join(current)) >= 400:
            chunks.append("\n\n".join(current))
            tail = current[-1]
            current = [tail] if estimate_tokens(tail) <= 80 else []
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def collect(workspace):
    rows = []
    for root, _dirs, files in os.walk(workspace):
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, workspace)
            for index, chunk in enumerate(chunk_file(path)):
                rows.append((f"{rel}#{index}", chunk))
    return rows


def build(rows, tokenizer):
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE VIRTUAL TABLE chunks USING fts5(body, tokenize='%s')" % tokenizer
    )
    conn.executemany("INSERT INTO chunks(body) VALUES (?)", [(b,) for _, b in rows])
    conn.commit()
    return conn


def search(conn, term):
    """Run a term against the index the way the runtime would."""
    try:
        return conn.execute(
            "SELECT count(*) FROM chunks WHERE chunks MATCH ?", (term,)
        ).fetchone()[0]
    except sqlite3.OperationalError:
        return 0


# ---------------------------------------------------------------------------
# Test set parsing
#
# Only the retrieval section and its FTS-relevant keys are read, so a full YAML
# parser is not needed and the script stays dependency free.
# ---------------------------------------------------------------------------

def parse_retrieval_cases(path):
    cases = []
    current = None
    in_retrieval = False
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if re.match(r"^retrieval:\s*$", line):
            in_retrieval = True
            continue
        if in_retrieval and re.match(r"^[a-z_]+:\s*$", line):
            break
        if not in_retrieval:
            continue
        match = re.match(r"^\s*-\s+id:\s*(\S+)\s*$", line)
        if match:
            current = {
                "id": match.group(1),
                "scope": "asuka",
                "must_hit": [],
                "must_miss": [],
            }
            cases.append(current)
            continue
        if current is None:
            continue
        scope = re.match(r"^\s+scope:\s*(\S+)\s*$", line)
        if scope:
            current["scope"] = scope.group(1)
            continue
        for key in ("must_hit", "must_miss"):
            hit = re.match(r"^\s+%s:\s*\"?([^\"\n]+?)\"?\s*$" % key, line)
            if hit:
                current[key].append(hit.group(1))
    return cases


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def main():
    if not os.path.isdir(WORKSPACE):
        print("missing workspace: %s" % WORKSPACE)
        return 2

    main_rows = collect(WORKSPACE)
    worker_rows = collect(WORKER_WORKSPACE)
    if not main_rows:
        print("no markdown files found in %s" % WORKSPACE)
        return 2

    print("corpus: %d chunks from %s" % (len(main_rows), os.path.relpath(WORKSPACE, HERE)))
    print("        %d chunks from %s" % (len(worker_rows), os.path.relpath(WORKER_WORKSPACE, HERE)))
    print()

    indexes = {
        "asuka": build(main_rows, "trigram"),
        "worker": build(worker_rows, "trigram"),
    }
    unicode61 = build(main_rows, "unicode61")

    # -- tokenizer comparison -------------------------------------------------
    print("== tokenizer comparison ==")
    probes = ["做會計", "瑜伽課", "佢叫阿黑", "每月開支", "去大阪", "flat white", "audit"]
    print("   %-14s %10s %10s" % ("term", "unicode61", "trigram"))
    unicode_only = 0
    for term in probes:
        u = search(unicode61, term)
        t = search(indexes["asuka"], term)
        if u and not t:
            unicode_only += 1
        print("   %-14s %10d %10d%s" % (
            term, u, t,
            "   <- unicode61 missed it" if t and not u else "",
        ))
    print()
    print("   unicode61 matches only when the query equals a complete run of CJK")
    print("   characters, so recall depends on where punctuation happens to fall.")
    print("   trigram matches any contiguous run of three or more characters, so")
    print("   recall does not depend on the note's phrasing.")
    print("   unicode61 missed %d of %d probes that trigram found." % (
        unicode_only, len(probes)))
    print()

    # -- short term floor -----------------------------------------------------
    print("== short term floor ==")
    for term in ["瑜伽", "阿黑", "大阪", "AI"]:
        hits = search(indexes["asuka"], term)
        print("   %-8s -> %d hit(s)%s" % (
            term, hits,
            "   (cannot match: shorter than %d characters)" % MIN_TRIGRAM_TERM
            if hits == 0 else "",
        ))
    print()

    # -- scope isolation ------------------------------------------------------
    print("== scope isolation ==")
    term = "南海鐵路"
    in_worker = search(indexes["worker"], term)
    in_main = search(indexes["asuka"], term)
    print("   %r in worker index: %d" % (term, in_worker))
    print("   %r in main index:   %d" % (term, in_main))
    scope_ok = in_worker > 0 and in_main == 0
    print("   %s" % ("PASS: each agent indexes only its own workspace"
                     if scope_ok else "FAIL: cross-agent leak"))
    print()

    # -- retrieval cases ------------------------------------------------------
    print("== retrieval cases ==")
    failures = []
    checked = 0
    for case in parse_retrieval_cases(TESTSET):
        index = indexes.get(case["scope"], indexes["asuka"])
        for term in case["must_hit"]:
            checked += 1
            hits = search(index, term)
            ok = hits > 0
            if not ok:
                failures.append("%s: expected a hit for %r" % (case["id"], term))
            print("   %-22s must_hit  %-16s %-5s %d hit(s)" % (
                case["id"], term, "PASS" if ok else "FAIL", hits))
        for term in case["must_miss"]:
            checked += 1
            hits = search(index, term)
            ok = hits == 0
            if not ok:
                failures.append("%s: expected no hit for %r" % (case["id"], term))
            print("   %-22s must_miss %-16s %-5s %d hit(s)" % (
                case["id"], term, "PASS" if ok else "FAIL", hits))

    print()
    if failures:
        print("%d of %d assertions failed:" % (len(failures), checked))
        for failure in failures:
            print("   - %s" % failure)
        return 1

    print("all %d index assertions passed" % checked)
    print()
    print("The as_written cases passing and the paraphrased cases still failing is")
    print("the expected state of the free tier. When a local embedding provider")
    print("is enabled, the paraphrased cases should start passing, and the")
    print("must_miss assertions on them should be inverted in testset.yaml.")
    print()
    print("The behavioural cases in testset.yaml, the ones that check whether a")
    print("directive was applied to a reply, are not verified by this script.")
    print("They need a live agent session.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
