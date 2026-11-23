#!/usr/bin/env python3
"""Refreshes the machine-generated files in data/generated/. Needs network access.

1. Asks Wikidata for news outlets (the classes in data/wikidata-classes.txt) and
   their official websites.
2. Drops sites that the curated lists already cover, that data/allow.txt protects,
   that sit on government or education domains, or whose website is only a page
   on a shared host (`example.com/news`).
3. Never adds a site on a popular domain (Tranco top N) automatically: those go to
   data/generated/review.txt for a person to decide.
4. Keeps only sites that still resolve in DNS.
5. Probes common subdomains (www, m, amp, edition, …) of every entry so the
   hosts-format lists, which can only block exact names, cover the names people use.

Usage:
  refresh.py                  full refresh (Wikidata, DNS, review queue)
  refresh.py --curated-only   only probe curated entries that have no DNS data yet
  --dns-rate N                DNS queries per second (default 50, gentle on a home
                              connection; a full refresh makes about 70,000)
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import datetime as dt
import http.client
import io
import json
import random
import re
import socket
import string
import struct
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from common import (
    ALLOW_FILE, CLASSES_FILE, HOSTNAMES_FILE, PSL_FILE, REVIEW_FILE, WIKIDATA_FILE,
    PublicSuffixList, covered_by, normalize_host, read_curated, read_entries,
    read_hostnames, www_twin,
)

USER_AGENT = "news-blocklist-refresh/1.0 (Python urllib)"
SPARQL_URL = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
TRANCO_URL = "https://tranco-list.eu/top-1m.csv.zip"
PSL_URL = "https://publicsuffix.org/list/public_suffix_list.dat"

# Sites on a registrable domain ranked this high need a person to approve them.
GUARD_RANK = 25_000
# Ranks are recorded down to here; build.py puts Wikidata sites ranked this high in news-lite.
RECORD_RANK = 200_000
# A host claimed by this many Wikidata items is probably a platform or publisher hub.
SHARED_HOST_ITEMS = 5
# Refuse to write a Wikidata list that shrank this much: it usually means an outage.
MIN_KEEP_RATIO = 0.8
# If fewer curated entries than this resolve, DNS itself is failing: write nothing.
MIN_CURATED_ALIVE = 0.7

# Public-suffix labels that mark government, military and education domains.
INSTITUTIONAL_LABELS = {
    "gov", "govt", "gob", "gouv", "go", "gv", "gc", "mil", "edu", "ac", "sch",
    "k12", "nhs", "police", "int",
}

# A website URL counts as the outlet's own site only with one of these paths.
SITE_ROOT_PATH = re.compile(
    r"^/?(index\.(html?|php|aspx?|jsp)|default\.aspx?|home|[a-z]{2}([-_][a-z]{2,4})?/?)?$", re.I)

# Hostnames containing these words are sports, music, film or games outlets: out of scope.
# Only applied to sites added automatically from Wikidata.
OFF_TOPIC_WORDS = re.compile(
    r"sport|soccer|football|futbol|fussball|cricket|rugby|golf|tennis|baseball|basketball|hockey|"
    r"racing|motorsport|music|metal|movie|cinema|kino|anime|manga|gaming|videogame")

PROBE_PREFIXES = ["www", "m", "mobile", "amp", "edition", "news", "lite", "en", "uk", "us", "feeds", "rss"]


# MARK: HTTP

def fetch(url: str, data: bytes | None = None, accept: str = "*/*", attempts: int = 5) -> bytes:
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    delay = 5.0
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(request, timeout=180) as response:
                return response.read()
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, ConnectionError) as error:
            status = getattr(error, "code", None)
            if attempt == attempts or (status is not None and status < 500 and status != 429):
                raise
            retry_after = getattr(error, "headers", None) and error.headers.get("Retry-After")
            wait = float(retry_after) if retry_after and retry_after.isdigit() else delay
            print(f"  retrying after {error} (wait {wait:.0f}s)", file=sys.stderr)
            time.sleep(wait)
            delay *= 2
    raise AssertionError("unreachable")


def sparql(query: str) -> list[dict]:
    body = urllib.parse.urlencode({"query": query}).encode()
    result = json.loads(fetch(SPARQL_URL, data=body, accept="application/sparql-results+json"))
    return result["results"]["bindings"]


def qid(binding: dict, key: str) -> str:
    return binding[key]["value"].rsplit("/", 1)[-1]


# MARK: Wikidata

def read_class_spec():
    """data/wikidata-classes.txt: `Q1`, `Q1+` (with subclasses), `-Q1` (exclude, with subclasses),
    `genre Q1` (include by genre), `-subject Q1` (exclude by genre or main subject)."""
    include, include_tree, exclude_tree, genres, subjects = set(), set(), set(), set(), set()
    for raw in CLASSES_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("genre "):
            genres.add(line.split()[1])
        elif line.startswith("-subject "):
            subjects.add(line.split()[1])
        elif line.startswith("-"):
            exclude_tree.add(line[1:])
        elif line.endswith("+"):
            include_tree.add(line[:-1])
        else:
            include.add(line)
    return include, include_tree, exclude_tree, genres, subjects


def subclasses(roots: set[str]) -> set[str]:
    if not roots:
        return set()
    values = " ".join(f"wd:{q}" for q in sorted(roots))
    rows = sparql(f"SELECT DISTINCT ?c WHERE {{ VALUES ?root {{ {values} }} ?c wdt:P279* ?root . }}")
    return {qid(r, "c") for r in rows} | roots


ITEM_QUERY = """
SELECT ?item ?site ?links WHERE {
  VALUES ?v { %(values)s }
  ?item wdt:%(prop)s ?v .
  ?item p:P856 ?st .
  ?st ps:P856 ?site ; wikibase:rank ?rank .
  FILTER(?rank != wikibase:DeprecatedRank)
  FILTER NOT EXISTS { ?st pq:P582 [] }
  FILTER NOT EXISTS { ?item wdt:P576 [] }
  FILTER NOT EXISTS { ?item wdt:P2669 [] }
  ?item wikibase:sitelinks ?links .
}"""


def fetch_items(values: list[str], prop: str) -> list[tuple[str, str, int]]:
    """(item, website, sitelink count) for items whose `prop` is one of `values`."""
    rows: list[tuple[str, str, int]] = []
    batch: list[str] = []

    def run(chunk: list[str]):
        query = ITEM_QUERY % {"values": " ".join(f"wd:{q}" for q in chunk), "prop": prop}
        for r in sparql(query):
            rows.append((qid(r, "item"), r["site"]["value"], int(r["links"]["value"])))

    # The biggest classes go alone; the long tail of small ones in batches.
    for q in values:
        if q in {"Q11032", "Q1153191", "Q17232649", "Q1110794"}:
            run([q])
        else:
            batch.append(q)
            if len(batch) == 40:
                run(batch)
                batch = []
    if batch:
        run(batch)
    return rows


def excluded_items(classes: set[str], subjects: set[str]) -> set[str]:
    """Items with a website that are instances of `classes` or whose genre or main subject is in `subjects`."""
    found: set[str] = set()
    for values, path in ((sorted(classes), "wdt:P31"), (sorted(subjects), "wdt:P136|wdt:P921")):
        for i in range(0, len(values), 60):
            chunk = " ".join(f"wd:{q}" for q in values[i:i + 60])
            rows = sparql(f"SELECT DISTINCT ?item WHERE {{ VALUES ?x {{ {chunk} }} ?item {path} ?x ; wdt:P856 [] . }}")
            found |= {qid(r, "item") for r in rows}
    return found


def labels(items: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for i in range(0, len(items), 50):
        query = urllib.parse.urlencode({
            "action": "wbgetentities", "ids": "|".join(items[i:i + 50]), "props": "labels", "format": "json"})
        entities = json.loads(fetch(f"{WIKIDATA_API}?{query}"))["entities"]
        for key, entity in entities.items():
            names = entity.get("labels", {})
            pick = names.get("en") or names.get("mul") or next(iter(names.values()), None)
            result[key] = pick["value"] if pick else key
    return result


def site_host(url: str) -> tuple[str | None, bool]:
    """(hostname, is the outlet's own site) for an official-website URL."""
    try:
        parts = urllib.parse.urlsplit(url.strip())
    except ValueError:
        return None, False
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return None, False
    host = normalize_host(parts.hostname)
    if host is None:
        return None, False
    if host.startswith("www.") and host.count(".") >= 2:
        host = host[4:]
    return host, bool(SITE_ROOT_PATH.match(parts.path))


# MARK: Reference data

def load_tranco(limit: int) -> dict[str, int]:
    archive = zipfile.ZipFile(io.BytesIO(fetch(TRANCO_URL)))
    ranks: dict[str, int] = {}
    with archive.open(archive.namelist()[0]) as f:
        for line in io.TextIOWrapper(f, encoding="utf-8"):
            rank, _, domain = line.strip().partition(",")
            if int(rank) > limit:
                break
            ranks[domain] = int(rank)
    return ranks


def load_psl() -> PublicSuffixList:
    """Downloads the Public Suffix List and keeps a copy for build.py's offline checks."""
    text = fetch(PSL_URL).decode("utf-8")
    PSL_FILE.write_text(text, encoding="utf-8")
    return PublicSuffixList(text)


# MARK: DNS

class Resolver:
    """Asks public resolvers directly so the local hosts file and ISP rewriting don't skew results.
    Queries are paced to `rate` per second so a refresh doesn't swamp a home router."""

    SERVERS = ("1.1.1.1", "8.8.8.8", "9.9.9.9")

    def __init__(self, rate: float):
        self.interval = 1.0 / rate
        self.workers = max(4, min(96, int(rate // 4)))
        self.lock = threading.Lock()
        self.next_slot = time.monotonic()

    def _pace(self):
        with self.lock:
            slot = max(time.monotonic(), self.next_slot)
            self.next_slot = slot + self.interval
        delay = slot - time.monotonic()
        if delay > 0:
            time.sleep(delay)

    def exists(self, name: str) -> bool | None:
        """True if `name` has an A record (directly or through a CNAME), False if it doesn't,
        None if no server gave a usable answer."""
        try:
            question = b"".join(bytes([len(p)]) + p.encode("ascii") for p in name.split(".")) + b"\0"
        except (UnicodeEncodeError, ValueError):
            return False
        for attempt in range(4):
            server = self.SERVERS[attempt % len(self.SERVERS)]
            ident = random.randrange(65536)
            packet = struct.pack(">HHHHHH", ident, 0x0100, 1, 0, 0, 0) + question + struct.pack(">HH", 1, 1)
            self._pace()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2.5)
            try:
                sock.sendto(packet, (server, 53))
                while True:
                    reply = sock.recv(4096)
                    if len(reply) >= 12 and struct.unpack(">H", reply[:2])[0] == ident:
                        break
            except OSError:
                continue
            finally:
                sock.close()
            rcode = reply[3] & 0x0F
            answers = struct.unpack(">H", reply[6:8])[0]
            if rcode == 0:
                return answers > 0
            if rcode == 3:
                return False
        return None

    def many(self, names: set[str]) -> dict[str, bool | None]:
        names = sorted(names)
        if len(names) > 1000:
            print(f"  {len(names):,} DNS queries (about {len(names) * self.interval / 60:.0f} min)")
        with futures.ThreadPoolExecutor(max_workers=self.workers) as pool:
            return dict(zip(names, pool.map(self.exists, names)))


def random_label() -> str:
    return "nbl-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=12))


def probe(entries: list[str], resolver: Resolver) -> dict[str, list[str]]:
    """For each entry, the names among it, its www twin and common news subdomains that resolve.
    Domains with wildcard DNS (any name resolves) and www. entries only get the entry and its twin."""
    wildcard_tests = {e: f"{random_label()}.{e}" for e in entries if not e.startswith("www.")}
    wild = resolver.many(set(wildcard_tests.values()))
    candidates: dict[str, set[str]] = {}
    for e in entries:
        names = {e, www_twin(e)}
        # A www. entry is deliberately narrow (the domain has other services): don't widen it.
        if e in wildcard_tests and not wild.get(wildcard_tests[e]):
            names |= {f"{p}.{e}" for p in PROBE_PREFIXES if not e.startswith(f"{p}.")}
        candidates[e] = names
    found = resolver.many(set().union(*candidates.values()) if candidates else set())
    return {e: sorted(n for n in names if found.get(n)) for e, names in candidates.items()}


# MARK: Output

def write_hostnames(names: dict[str, list[str]]):
    lines = [
        "# Generated by scripts/refresh.py. Do not edit.",
        "# entry: the names under it that resolved in DNS (used to expand the hosts-format lists).",
    ]
    lines += [f"{entry}: {' '.join(found)}" for entry, found in sorted(names.items())]
    HOSTNAMES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_wikidata_file() -> dict[str, str]:
    if not WIKIDATA_FILE.exists():
        return {}
    entries, _ = read_entries(WIKIDATA_FILE)
    return {e.host: e.note for e in entries}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--curated-only", action="store_true", help="only probe curated entries without DNS data")
    parser.add_argument("--force", action="store_true", help="write the Wikidata list even if it shrank a lot")
    parser.add_argument("--dns-rate", type=float, default=50, help="DNS queries per second (default 50)")
    args = parser.parse_args()

    curated, errors = read_curated()
    allow, allow_errors = read_entries(ALLOW_FILE)
    if errors or allow_errors:
        print("\n".join(errors + allow_errors), file=sys.stderr)
        return 1
    curated_hosts = {e.host for e in curated}
    allowed = {e.host for e in allow}
    resolver = Resolver(args.dns_rate)
    hostnames = read_hostnames()

    if args.curated_only:
        missing = sorted(curated_hosts - hostnames.keys())
        print(f"Probing {len(missing)} new curated entries")
        found = probe(missing, resolver)
        if len(missing) >= 20 and sum(1 for e in missing if found[e]) < len(missing) * MIN_CURATED_ALIVE:
            print("Most new entries don't resolve: DNS looks broken, so nothing was written", file=sys.stderr)
            return 3
        hostnames.update(found)
        keep = curated_hosts | set(read_wikidata_file())
        write_hostnames({k: v for k, v in hostnames.items() if k in keep})
        return 0

    print("Loading Public Suffix List and Tranco ranking")
    psl = load_psl()
    tranco = load_tranco(RECORD_RANK)

    print("Querying Wikidata")
    include, include_tree, exclude_tree, genres, subjects = read_class_spec()
    excluded_classes = subclasses(exclude_tree)
    classes = (subclasses(include_tree) | include) - excluded_classes
    print(f"  {len(classes)} classes, {len(excluded_classes)} excluded, {len(genres)} genres")
    rows = fetch_items(sorted(classes), "P31") + fetch_items(sorted(genres), "P136")
    skip_items = excluded_items(excluded_classes, subjects)
    print(f"  {len(rows)} website claims; {len(skip_items)} items excluded by class")

    by_host: dict[str, dict] = {}
    for item, url, links in rows:
        if item in skip_items:
            continue
        host, own_site = site_host(url)
        if host is None:
            continue
        info = by_host.setdefault(host, {"items": set(), "links": 0, "own": False, "url": url})
        info["items"].add(item)
        info["links"] = max(info["links"], links)
        if own_site:
            info["own"] = True

    auto: dict[str, str] = {}
    review: dict[str, tuple[int, str, str]] = {}
    # Names Wikidata knows under curated entries (cn.nytimes.com under nytimes.com): the
    # hosts-format lists can only block exact names, so these extend the curated entry.
    known_under: dict[str, set[str]] = {}
    for host, info in by_host.items():
        parent = covered_by(host, curated_hosts) or (www_twin(host) if www_twin(host) in curated_hosts else None)
        if parent:
            known_under.setdefault(parent, set()).update({host, www_twin(host)})
            continue
        if covered_by(host, allowed):
            continue
        suffix = psl.public_suffix(host)
        if INSTITUTIONAL_LABELS & set(suffix.split(".")):
            continue
        registrable = psl.registrable(host)
        if registrable is None:
            continue
        first_item = sorted(info["items"], key=lambda q: int(q[1:]))[0]
        rank = tranco.get(registrable)
        if rank is not None and rank <= GUARD_RANK:
            # Popular domain: a person decides, whether the URL is the whole site or one section.
            review[host] = (rank, first_item, info["url"])
        elif info["own"] and len(info["items"]) < SHARED_HOST_ITEMS and not OFF_TOPIC_WORDS.search(host):
            # The URL is the site's root, and few items claim the host: it's the outlet's own site.
            # (On shared platforms such as x.blogspot.com that is still just this one site.)
            auto[host] = f"{first_item} rank {rank}" if rank else first_item

    print(f"Probing subdomains of {len(curated_hosts)} curated entries")
    names = probe(sorted(curated_hosts), resolver)
    dead = sorted(e for e in curated_hosts if not names.get(e))
    if len(dead) > len(curated_hosts) * (1 - MIN_CURATED_ALIVE):
        print(f"{len(dead)} of {len(curated_hosts)} curated entries don't resolve: DNS looks broken, "
              "so nothing was written", file=sys.stderr)
        return 3

    print(f"Checking DNS for {len(auto)} sites")
    alive = resolver.many(set(auto) | {www_twin(h) for h in auto} | set().union(*known_under.values()))
    previous = read_wikidata_file()
    kept: dict[str, str] = {}
    for host, item in auto.items():
        status = [alive.get(host), alive.get(www_twin(host))]
        if True in status or (None in status and host in previous):
            kept[host] = item
    print(f"  {len(kept)} resolve")

    if previous and len(previous) >= 1000 and len(kept) < len(previous) * MIN_KEEP_RATIO and not args.force:
        print(f"Refusing to shrink the Wikidata list from {len(previous)} to {len(kept)} sites "
              "(use --force if this is expected)", file=sys.stderr)
        return 2

    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    lines = [
        "# Generated by scripts/refresh.py from Wikidata (CC0). Do not edit by hand:",
        "# add sites to data/curated/, or stop one being blocked with data/allow.txt.",
        f"# Updated: {today}",
    ]
    lines += [f"{host}  # {item}" for host, item in sorted(kept.items())]
    WIKIDATA_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    for parent, known in known_under.items():
        names[parent] = sorted(set(names.get(parent, [])) | {n for n in known if alive.get(n)})
    for host in kept:
        names[host] = sorted(n for n in (host, www_twin(host)) if alive.get(n))
    write_hostnames(names)
    if dead:
        print(f"  {len(dead)} curated entries don't resolve: {' '.join(dead)}")

    print(f"Writing review queue ({len(review)} popular sites)")
    named = labels(sorted({item for _, item, _ in review.values()}))
    lines = [
        "# Generated by scripts/refresh.py. Popular sites that Wikidata lists as news outlets,",
        "# not yet in data/curated/ or data/allow.txt. Add each to a curated file (block it) or to",
        "# allow.txt (don't). rank = Tranco rank of the registrable domain.",
        f"# Updated: {today}",
    ]
    for host, (rank, item, url) in sorted(review.items(), key=lambda kv: kv[1][0]):
        lines.append(f"{host}  # rank {rank} · {named.get(item, item)} ({item}) · {url}")
    REVIEW_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
