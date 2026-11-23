# Contributing

Thanks for helping. Most changes are a single line in a text file; you don't need to run
anything. When a change lands on `main`, GitHub Actions validates it, checks DNS for new
sites and rebuilds every list.

## Add a site

1. Open the file for its region in [`data/curated/`](data/curated). Each file is grouped
   by country.
2. Add one line with the hostname and a comment naming the outlet:

   ```
   theguardian.com  # The Guardian
   ```

Rules for entries:

- **Lowercase hostnames only**: no `https://`, no paths, no trailing dot. Write
  internationalised domains in punycode (`xn--…`).
- **Use the registrable domain** (`theguardian.com`) when the whole domain is the
  outlet. It covers every subdomain in the adblock, wildcard and dnsmasq formats, and the
  build adds `www.` and other subdomains to the hosts formats automatically.
- **Use the specific news hostnames** (`news.yahoo.com`, `www.t-online.de`) when the
  domain also runs services that aren't news on other subdomains, such as email, logins,
  streaming or shopping. Never list the bare domain in that case.
- **Paths can't be blocked.** If news is only `example.com/news` on a site that's mostly
  something else, it can't go on the list. If the host is mostly news, list it and say
  what else it breaks with a `mixed:` comment, which appears in the README:

  ```
  www.bbc.co.uk  # BBC; mixed: also blocks iPlayer, BBC Sounds and Bitesize
  ```

- **In scope:** general, political, world, business and local news, opinion and
  commentary on current affairs, news agencies, broadcasters' news sites, news
  magazines, fact-checkers and aggregators. **Out of scope:** sport-only, entertainment,
  technology, gaming, science, lifestyle and trade publications.

## Report a site blocked by mistake

[Open an issue](../../issues/new/choose), or add the domain to
[`data/allow.txt`](data/allow.txt) with a comment saying what it is. Anything in
`allow.txt` is never blocked, and nothing under it is added automatically from Wikidata.

If the site came from Wikidata (it appears in `data/generated/wikidata.txt` with a
`Q…` item ID), you can also fix the item on Wikidata itself: set the right "instance of",
add an end date to an old "official website", or mark a defunct outlet as dissolved.

## Review queue

[`data/generated/review.txt`](data/generated/review.txt) lists sites that Wikidata calls
news outlets but that aren't added automatically, because their domain is popular or they
look like specialist outlets (gaming, tech, trade press, weather …). None of them is blocked
until someone decides: add it to a curated file if it's general news, or to `allow.txt` if
it isn't. Pull requests that clear part of the queue are very welcome.

## Running the scripts

Python 3.10 or later, standard library only.

```sh
python3 scripts/build.py --check   # validate data/ only (quick)
python3 scripts/build.py           # rebuild lists/ and the README stats
python3 scripts/test_lists.py      # check major sites are blocked and others aren't
python3 scripts/refresh.py         # full refresh from Wikidata and DNS (slow, needs network)
```

Don't edit `lists/` or `data/generated/` by hand. They're rebuilt from `data/`.
