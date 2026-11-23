#!/usr/bin/env python3
"""Builds the lists in lists/ from data/. Offline and deterministic.

  build.py           validate data/, then write lists/ and the stats in README.md
  build.py --check   validate data/ only; exit 1 on errors (used for pull requests)

A list file is rewritten only when its entries change, so its "Last modified"
line means what it says.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys

from common import (
    ALLOW_FILE, HOMEPAGE, LISTS, PSL_FILE, RAW_BASE, ROOT, WIKIDATA_FILE, Entry,
    PublicSuffixList, covered_by, read_curated, read_entries, read_hostnames, www_twin,
)

README = ROOT / "README.md"

# Wikidata sites whose domain is in the Tranco top LITE_RANK go into news-lite too.
LITE_RANK = 200_000

VARIANTS = {
    "news": "Curated outlets plus every news site listed on Wikidata. The complete list.",
    "news-lite": f"Curated outlets plus Wikidata news sites in the Tranco top {LITE_RANK:,}.",
}

FORMATS = {
    # name: (comment prefix, syntax line, line template, uses exact names?)
    "hosts": ("#", "hosts file (0.0.0.0 hostname); exact names, subdomains listed separately", "0.0.0.0 {}", True),
    "domains": ("#", "one hostname per line; exact names, subdomains listed separately", "{}", True),
    "wildcard": ("#", "one domain per line; each entry also covers all its subdomains", "{}", False),
    "adblock": ("!", "Adblock Plus / uBlock Origin / AdGuard (||domain^)", "||{}^", False),
    "dnsmasq": ("#", "dnsmasq (local=/domain/); each entry also covers all its subdomains", "local=/{}/", False),
}


def fail(errors: list[str]) -> int:
    print("\n".join(errors), file=sys.stderr)
    print(f"\n{len(errors)} problem(s) found.", file=sys.stderr)
    return 1


def validate(curated: list[Entry], allow: list[Entry]) -> list[str]:
    errors: list[str] = []
    # An entry like `com.au` would block a whole country's sites in the wildcard formats.
    # refresh.py keeps a copy of the Public Suffix List for this check.
    if PSL_FILE.exists():
        psl = PublicSuffixList(PSL_FILE.read_text(encoding="utf-8"))
        for e in curated:
            if psl.registrable(e.host) is None:
                errors.append(f"{e.source}: {e.host} is a public suffix, not a site")
    seen: dict[str, Entry] = {}
    for e in curated:
        if e.host in seen:
            errors.append(f"{e.source}: {e.host} is already listed at {seen[e.host].source}")
        seen.setdefault(e.host, e)
    for e in curated:
        twin = www_twin(e.host)
        if e.host.startswith("www.") and twin in seen:
            errors.append(f"{e.source}: {e.host} is redundant: {twin} is listed at {seen[twin].source}")
    # A curated entry may block a specific host under an allowed domain (news.google.com under
    # google.com), but must not block an allowed host itself or a domain above one.
    for a in allow:
        parent = covered_by(a.host, seen)
        if parent:
            errors.append(f"{seen[parent].source}: {parent} would block {a.host}, which {a.source} says never to block")
    seen_allow: dict[str, str] = {}
    for a in allow:
        if a.host in seen_allow:
            errors.append(f"{a.source}: {a.host} is already in allow.txt at {seen_allow[a.host]}")
        seen_allow.setdefault(a.host, a.source)
    return errors


def rank_of(entry: Entry) -> int | None:
    """Tranco rank recorded by refresh.py in a Wikidata entry's comment (`Q123 rank 4567`)."""
    match = re.search(r"\brank (\d+)", entry.note)
    return int(match.group(1)) if match else None


def entries_for(curated: list[Entry], wikidata: list[Entry], allowed: set[str]) -> dict[str, list[str]]:
    curated_set = {e.host for e in curated}
    extra = [
        e for e in wikidata
        if not covered_by(e.host, curated_set)
        and www_twin(e.host) not in curated_set
        and not covered_by(e.host, allowed)
    ]
    popular = {e.host for e in extra if (rank_of(e) or LITE_RANK + 1) <= LITE_RANK}
    return {
        "news": sorted(curated_set | {e.host for e in extra}),
        "news-lite": sorted(curated_set | popular),
    }


def exact_names(entries: list[str], hostnames: dict[str, list[str]], allowed: set[str]) -> list[str]:
    """Every name to block for formats that can't match subdomains."""
    names: set[str] = set()
    for entry in entries:
        found = hostnames.get(entry)
        names.add(entry)
        names.update(found if found is not None else [www_twin(entry)])
    return sorted(n for n in names if n not in allowed)


def wildcard_roots(entries: list[str]) -> list[str]:
    """Entries not already covered by a parent entry."""
    entry_set = set(entries)
    return sorted(e for e in entries if covered_by(e, entry_set - {e}) is None)


def header(prefix: str, variant: str, fmt: str, syntax: str, count: int, modified: str) -> str:
    lines = []
    if fmt == "adblock":
        lines.append("[Adblock Plus]")
    title = "News Blocklist" + (" (lite)" if variant == "news-lite" else "")
    fields = [
        ("Title", title),
        ("Description", "Blocks news and current-affairs sites. " + VARIANTS[variant]),
        ("Homepage", HOMEPAGE),
        ("License", f"MIT ({HOMEPAGE}/blob/main/LICENSE)"),
        ("Syntax", syntax),
        ("Entries", f"{count:,}"),
        ("Last modified", modified),
    ]
    if fmt == "adblock":
        fields.append(("Expires", "1 day"))
    lines += [f"{prefix} {k}: {v}" for k, v in fields]
    return "\n".join(lines) + f"\n{prefix}\n"


def body_of(text: str, prefix: str) -> str:
    return "\n".join(l for l in text.splitlines() if l and not l.startswith(prefix) and l != "[Adblock Plus]")


def write_list(variant: str, fmt: str, items: list[str]) -> bool:
    prefix, syntax, template, _ = FORMATS[fmt]
    path = LISTS / fmt / f"{variant}.txt"
    body = "\n".join(template.format(i) for i in items)
    if path.exists() and body_of(path.read_text(encoding="utf-8"), prefix) == body:
        return False
    modified = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header(prefix, variant, fmt, syntax, len(items), modified) + body + "\n", encoding="utf-8")
    return True


def replace_block(text: str, name: str, content: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:start -->\n).*?(<!-- {name}:end -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"README.md is missing the <!-- {name}:start --> … <!-- {name}:end --> markers")
    return pattern.sub(lambda m: m.group(1) + content + m.group(2), text)


def update_readme(counts: dict[str, tuple[int, int]], curated: list[Entry]):
    rows = ["| List | Sites | Hostnames (hosts format) |", "| --- | ---: | ---: |"]
    for variant in VARIANTS:
        sites, names = counts[variant]
        rows.append(f"| `{variant}` | {sites:,} | {names:,} |")
    links = ["| Format | `news` | `news-lite` |", "| --- | --- | --- |"]
    for fmt in FORMATS:
        cells = [f"[{fmt}/{v}.txt]({RAW_BASE}/lists/{fmt}/{v}.txt)" for v in VARIANTS]
        links.append(f"| {fmt} | " + " | ".join(cells) + " |")
    mixed = ["| Host | Outlet | Also blocks |", "| --- | --- | --- |"]
    for e in sorted((e for e in curated if e.mixed), key=lambda e: e.host):
        also = re.sub(r"^also blocks\s+", "", e.mixed, flags=re.I)
        name = e.note[: e.note.lower().find("mixed:")].strip(" ;") or "–"
        mixed.append(f"| `{e.host}` | {name} | {also[:1].upper() + also[1:]} |")
    text = README.read_text(encoding="utf-8")
    text = replace_block(text, "stats", "\n".join(rows) + "\n")
    text = replace_block(text, "links", "\n".join(links) + "\n")
    text = replace_block(text, "mixed", "\n".join(mixed) + "\n")
    README.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="validate only")
    args = parser.parse_args()

    curated, errors = read_curated()
    allow, allow_errors = read_entries(ALLOW_FILE)
    wikidata, wikidata_errors = read_entries(WIKIDATA_FILE) if WIKIDATA_FILE.exists() else ([], [])
    errors += allow_errors + wikidata_errors + validate(curated, allow)
    if errors:
        return fail(errors)
    print(f"OK: {len(curated):,} curated entries, {len(allow):,} allowed domains, {len(wikidata):,} from Wikidata")
    if args.check:
        return 0

    allowed = {a.host for a in allow}
    hostnames = read_hostnames()
    counts: dict[str, tuple[int, int]] = {}
    for variant, entries in entries_for(curated, wikidata, allowed).items():
        exact = exact_names(entries, hostnames, allowed)
        roots = wildcard_roots(entries)
        counts[variant] = (len(entries), len(exact))
        for fmt, (_, _, _, uses_exact) in FORMATS.items():
            if write_list(variant, fmt, exact if uses_exact else roots):
                print(f"  wrote lists/{fmt}/{variant}.txt")
        print(f"{variant}: {len(entries):,} sites, {len(exact):,} hostnames, {len(roots):,} wildcard rules")
    update_readme(counts, curated)
    return 0


if __name__ == "__main__":
    sys.exit(main())
