"""Shared helpers for build.py and refresh.py. Standard library only."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CURATED = DATA / "curated"
GENERATED = DATA / "generated"
LISTS = ROOT / "lists"

ALLOW_FILE = DATA / "allow.txt"
CLASSES_FILE = DATA / "wikidata-classes.txt"
WIKIDATA_FILE = GENERATED / "wikidata.txt"
HOSTNAMES_FILE = GENERATED / "hostnames.txt"
REVIEW_FILE = GENERATED / "review.txt"
PSL_FILE = GENERATED / "public_suffix_list.dat"

REPO = "ruairidhflint/news-blocklist"
HOMEPAGE = f"https://github.com/{REPO}"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main"

_LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")


def normalize_host(text: str) -> str | None:
    """Returns `text` as a lowercase ASCII (punycode) hostname, or None if it isn't one."""
    s = text.strip().lower().rstrip(".")
    if not s or len(s) > 253:
        return None
    try:
        s = s.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    labels = s.split(".")
    if len(labels) < 2 or not all(_LABEL.match(label) for label in labels):
        return None
    tld = labels[-1]
    if not (tld.isalpha() or tld.startswith("xn--")):
        return None
    return s


def parents(host: str):
    """Yields `host` and every parent domain that still has at least two labels."""
    labels = host.split(".")
    for i in range(len(labels) - 1):
        yield ".".join(labels[i:])


def covered_by(host: str, domains: set[str] | dict) -> str | None:
    """The first of `host` or its parents found in `domains`, if any."""
    for p in parents(host):
        if p in domains:
            return p
    return None


def www_twin(host: str) -> str:
    return host[4:] if host.startswith("www.") else "www." + host


@dataclass(frozen=True)
class Entry:
    host: str
    note: str
    source: str

    @property
    def mixed(self) -> str | None:
        """Text after `mixed:` in the entry's comment: what else blocking this host breaks."""
        at = self.note.lower().find("mixed:")
        return self.note[at + 6:].strip() if at >= 0 else None


def read_entries(path: Path) -> tuple[list[Entry], list[str]]:
    """Parses a list file: one hostname per line, `#` starts a comment."""
    entries: list[Entry] = []
    errors: list[str] = []
    rel = path.relative_to(ROOT)
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        text, _, comment = raw.partition("#")
        text = text.strip()
        if not text:
            continue
        host = normalize_host(text)
        if host is None:
            errors.append(f"{rel}:{n}: not a valid hostname: {text!r}")
            continue
        if host != text:
            errors.append(f"{rel}:{n}: write {text!r} as {host!r} (lowercase, punycode, no trailing dot)")
            continue
        entries.append(Entry(host, comment.strip(), f"{rel}:{n}"))
    return entries, errors


def read_curated() -> tuple[list[Entry], list[str]]:
    entries: list[Entry] = []
    errors: list[str] = []
    for path in sorted(CURATED.glob("*.txt")):
        e, err = read_entries(path)
        entries += e
        errors += err
    return entries, errors


def read_hostnames() -> dict[str, list[str]]:
    """`data/generated/hostnames.txt`: `entry: name name …`, the DNS names that resolved for each entry."""
    result: dict[str, list[str]] = {}
    if not HOSTNAMES_FILE.exists():
        return result
    for line in HOSTNAMES_FILE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        entry, _, names = line.partition(":")
        result[entry.strip()] = names.split()
    return result


class PublicSuffixList:
    """Minimal implementation of https://publicsuffix.org/list/ matching rules."""

    def __init__(self, text: str):
        self.rules: set[str] = set()
        self.wildcards: set[str] = set()
        self.exceptions: set[str] = set()
        self.private: set[str] = set()
        in_private = False
        for line in text.splitlines():
            line = line.strip()
            if "===BEGIN PRIVATE DOMAINS===" in line:
                in_private = True
            if not line or line.startswith("//"):
                continue
            rule = line.split()[0]
            try:
                if rule.startswith("!"):
                    self.exceptions.add(rule[1:].encode("idna").decode())
                elif rule.startswith("*."):
                    self.wildcards.add(rule[2:].encode("idna").decode())
                else:
                    rule = rule.encode("idna").decode()
                    self.rules.add(rule)
                    if in_private:
                        self.private.add(rule)
            except UnicodeError:
                continue

    def public_suffix(self, host: str) -> str:
        labels = host.split(".")
        for i in range(len(labels)):
            candidate = ".".join(labels[i:])
            if candidate in self.exceptions:
                return ".".join(labels[i + 1:])
            if candidate in self.rules:
                return candidate
            if i + 1 < len(labels) and ".".join(labels[i + 1:]) in self.wildcards:
                return candidate
        return labels[-1]

    def registrable(self, host: str) -> str | None:
        """The registrable domain (e.g. `bbc.co.uk` for `www.bbc.co.uk`), or None for a bare suffix."""
        suffix = self.public_suffix(host)
        if host == suffix:
            return None
        rest = host[: -len(suffix) - 1]
        return rest.rsplit(".", 1)[-1] + "." + suffix
