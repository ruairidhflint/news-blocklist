# News Blocklist

A DNS blocklist of news and current-affairs websites, for people who want a break from the news.

It covers newspapers, broadcasters' news sites, news agencies, news magazines, political
news and commentary, business news, local news and news aggregators, worldwide. Major and
regional outlets are curated in this repository. The long tail of smaller news sites is
pulled from Wikidata, filtered automatically, checked against DNS, and refreshed every week.

Works with Pi-hole, AdGuard Home, uBlock Origin, AdGuard, dnsmasq, hosts files and any
blocker that subscribes to a list by URL.

<!-- stats:start -->
| List | Sites | Hostnames (hosts format) |
| --- | ---: | ---: |
| `news` | 14,314 | 30,863 |
| `news-lite` | 6,762 | 15,936 |
<!-- stats:end -->

## Choose a list

| List | What's in it | Use it when |
| --- | --- | --- |
| **`news`** | Everything: the curated outlets plus news sites listed on Wikidata. | You want news gone, including local papers and niche outlets. **Recommended.** |
| **`news-lite`** | The curated outlets plus the more popular news sites from Wikidata (domains in the Tranco top 200,000). | You want the major and regional names blocked with a list half the size, or you're editing a hosts file by hand. |

Both block the same major sites. `news` adds thousands of smaller ones.

## Download

Each list comes in five formats. Use the URL as-is to subscribe; lists update when the
data changes and at least weekly.

<!-- links:start -->
| Format | `news` | `news-lite` |
| --- | --- | --- |
| hosts | [hosts/news.txt](https://raw.githubusercontent.com/ruairidhflint/news-blocklist/main/lists/hosts/news.txt) | [hosts/news-lite.txt](https://raw.githubusercontent.com/ruairidhflint/news-blocklist/main/lists/hosts/news-lite.txt) |
| domains | [domains/news.txt](https://raw.githubusercontent.com/ruairidhflint/news-blocklist/main/lists/domains/news.txt) | [domains/news-lite.txt](https://raw.githubusercontent.com/ruairidhflint/news-blocklist/main/lists/domains/news-lite.txt) |
| wildcard | [wildcard/news.txt](https://raw.githubusercontent.com/ruairidhflint/news-blocklist/main/lists/wildcard/news.txt) | [wildcard/news-lite.txt](https://raw.githubusercontent.com/ruairidhflint/news-blocklist/main/lists/wildcard/news-lite.txt) |
| adblock | [adblock/news.txt](https://raw.githubusercontent.com/ruairidhflint/news-blocklist/main/lists/adblock/news.txt) | [adblock/news-lite.txt](https://raw.githubusercontent.com/ruairidhflint/news-blocklist/main/lists/adblock/news-lite.txt) |
| dnsmasq | [dnsmasq/news.txt](https://raw.githubusercontent.com/ruairidhflint/news-blocklist/main/lists/dnsmasq/news.txt) | [dnsmasq/news-lite.txt](https://raw.githubusercontent.com/ruairidhflint/news-blocklist/main/lists/dnsmasq/news-lite.txt) |
<!-- links:end -->

- **adblock**, **wildcard** and **dnsmasq** entries block a domain *and all its
  subdomains*. Use one of these if your blocker supports it.
- **hosts** and **domains** list exact hostnames, because a hosts file can't match
  subdomains. Each site is expanded to the names people actually visit (`www.`, `m.`,
  `amp.`, `edition.` and so on) using DNS checks.

## How to use it

**Pi-hole** · *Lists* (v6) or *Adlists* (v5) → add
`https://raw.githubusercontent.com/ruairidhflint/news-blocklist/main/lists/adblock/news.txt`
→ run *Update Gravity*. Pi-hole v6 (and v5 with FTL 5.22 or later) reads the adblock
format and blocks subdomains; on older versions use `lists/domains/news.txt`.

**AdGuard Home** · *Filters → DNS blocklists → Add blocklist → Add a custom list* →
paste the `adblock/news.txt` URL.

**uBlock Origin** · *Dashboard → Filter lists → Import* (at the bottom) → paste the
`adblock/news.txt` URL → *Apply changes*. Blocked pages show uBlock's warning page.

**AdGuard (browser extension and apps)** · *Filters → Custom → Add custom filter* →
paste the `adblock/news.txt` URL.

**dnsmasq / OpenWrt** · download `lists/dnsmasq/news.txt` into `/etc/dnsmasq.d/` (or add
it as a `conf-file`) and restart dnsmasq.

**Hosts file (macOS, Linux, Windows)** · append `lists/hosts/news-lite.txt` (or `news.txt`)
to `/etc/hosts` (`C:\Windows\System32\drivers\etc\hosts` on Windows). Turn off your
browser's "secure DNS" / DNS-over-HTTPS, or it will skip the hosts file.

## What counts as news

**Blocked:** general news (national, regional and local), politics, world affairs,
business and economic news, opinion and commentary on current affairs, news agencies,
broadcasters' news sites and 24-hour news channels, news and current-affairs magazines,
tabloids, fact-checkers, news aggregators and the news sections of web portals.

**Not blocked:** sport-only, entertainment and celebrity, technology, gaming and science
publications, lifestyle magazines, trade press, academic journals, government sites, and
TV or radio streaming services (unless they're the same site as the news).

The curated lists follow this line. The part pulled from Wikidata is filtered to follow it,
but the filters rely on Wikidata's own descriptions and miss some sites (see
[Limitations](#limitations)). The line isn't always sharp either. If you think a site is on
the wrong side of it, open an issue.

## Sites that do more than news

DNS blocking works on whole hostnames. It can't block `example.com/news` and leave
`example.com/weather` working. When news is the main thing a host serves, it's blocked
anyway, and anything else on that host goes with it. Where a company runs other services
on separate hostnames (email, logins, streaming apps), only the news hostnames are listed.

These are the hosts where blocking news also blocks something else:

<!-- mixed:start -->
| Host | Outlet | Also blocks |
| --- | --- | --- |
| `13tv.co.il` | Reshet 13 | Reshet 13's entertainment shows and catch-up |
| `1tv.ru` | Channel One | Channel One shows, series and live stream |
| `5-tv.ru` | Channel 5 | Channel 5 shows and live stream |
| `abidjan.net` | Abidjan.net | News-led portal that also hosts directories and classifieds |
| `abs-cbn.com` | ABS-CBN News | ABS-CBN entertainment and programme pages |
| `apuntmedia.es` | À Punt | À Punt's TV and radio player |
| `au.finance.yahoo.com` | Yahoo Finance Australia | Stock quotes and portfolios |
| `au.yahoo.com` | Yahoo Australia homepage | The rest of the Yahoo Australia homepage; Mail and Search still work |
| `bfmtv.com` | BFM TV | RMC Sport and BFM's other channels' pages |
| `bhrt.ba` | BHRT | BHRT programme pages and streams |
| `bnr.bg` | BNR (Bulgarian National Radio) | BNR radio programme pages and streams |
| `ca.finance.yahoo.com` | Yahoo Finance Canada | Stock quotes and portfolios |
| `ca.yahoo.com` | Yahoo Canada homepage | The rest of the Yahoo Canada homepage; Mail and Search still work |
| `cascadepbs.org` | Cascade PBS | Cascade PBS TV programme pages |
| `crtvg.es` | CRTVG (G24) | CRTVG's TV and radio player |
| `dzen.ru` | Dzen | Dzen blogs and videos |
| `federalna.ba` | Federalna TV | FTV programme pages and streams |
| `finance.yahoo.com` | Yahoo Finance | Stock quotes and portfolios |
| `gmanetwork.com` | GMA Network (GMA News Online) | GMA entertainment pages |
| `ici.fr` | ICI (formerly France Bleu) | The ICI local radio player |
| `ici.radio-canada.ca` | Radio-Canada (ICI Info) | OHdio and Radio-Canada TV pages |
| `imedi.ge` | Imedi | Imedi TV shows and live stream |
| `kan.org.il` | Kan (Israeli Public Broadcasting) | Kan's TV catch-up and radio streams |
| `klankosova.tv` | Klan Kosova | Klan Kosova TV and entertainment pages |
| `kqed.org` | KQED | KQED's arts, science and TV pages |
| `ksl.com` | KSL | KSL Classifieds, Cars and Homes |
| `lasexta.com` | laSexta | LaSexta's programme pages |
| `lrt.lt` | LRT | LRT Mediateka streaming |
| `mediacongo.net` | MediaCongo | Also hosts job and classified listings |
| `mtv.com.lb` | MTV Lebanon | MTV Lebanon's entertainment shows and live stream |
| `mynet.com` | Mynet | Mynet games, video and horoscopes |
| `npr.org` | NPR | NPR Music (Tiny Desk) and podcast pages |
| `ntp.msn.com` | Microsoft Edge new-tab news feed | Edge's new-tab page content |
| `ntv.ru` | NTV | NTV shows, series and live stream |
| `nymag.com` | New York magazine | The Cut, Grub Street and Curbed |
| `nytimes.com` | The New York Times | NYT Games (Wordle, Connections), NYT Cooking and Wirecutter |
| `orf.at` | ORF.at | The wildcard/adblock formats also block ORF ON (on.orf.at) and ORF Sound |
| `pink.rs` | Pink portal | TV Pink entertainment pages |
| `pptvhd36.com` | PPTV News | PPTV programme pages |
| `pressreader.com` | PressReader (digital newspapers) | Its magazines |
| `ren.tv` | REN TV | REN TV shows and live stream |
| `rtcg.me` | RTCG | RTCG programme pages and streams |
| `rtl.hu` | RTL Hungary | RTL show pages |
| `rtrs.tv` | RTRS | RTRS programme pages and streams |
| `rts.rs` | RTS | RTS programme pages and live streams |
| `rtv.rs` | RTV (Radio-televizija Vojvodine) | RTV programme pages and streams |
| `rtvslo.si` | RTV Slovenija | RTV 365 streaming and radio/TV programme pages |
| `rustavi2.ge` | Rustavi 2 | Rustavi 2 shows and live stream |
| `sg.yahoo.com` | Yahoo Singapore homepage | The rest of the Yahoo Singapore homepage; Mail and Search still work |
| `skai.gr` | SKAI | SKAI TV programme pages |
| `star.gr` | Star | Star TV programme and lifestyle pages |
| `sverigesradio.se` | Sveriges Radio (Ekot) | Sveriges Radio's web player and podcasts |
| `telemadrid.es` | Telemadrid | Telemadrid's programme pages and live stream |
| `teletica.com` | Teletica (Telenoticias) | Also TV programme pages |
| `thaipbs.or.th` | Thai PBS | Thai PBS programme pages |
| `top-channel.tv` | Top Channel | Top Channel shows |
| `tvzvezda.ru` | Zvezda | Zvezda shows and live stream |
| `udn.com` | United Daily News | Udn blog and udn reading |
| `uk.finance.yahoo.com` | Yahoo Finance UK | Stock quotes and portfolios |
| `uk.yahoo.com` | Yahoo UK homepage | The rest of the Yahoo UK homepage; Mail and Search still work |
| `usnews.com` | U.S. News & World Report | Its college, hospital and travel rankings |
| `vice.com` | Vice | Vice's culture, music and lifestyle content |
| `whyy.org` | WHYY | WHYY's TV and radio programme pages |
| `wnyc.org` | WNYC | WNYC's culture shows and podcasts |
| `www.163.com` | NetEase portal homepage and articles | The NetEase portal front page (not 163 Mail) |
| `www.abc.net.au` | ABC (Australia) | ABC Kids, ABC Radio and program pages |
| `www.aol.com` | AOL homepage | AOL's homepage (Mail is unaffected) |
| `www.band.com.br` | Band (Grupo Bandeirantes) portal | Also carries entertainment and sport |
| `www.bbc.co.uk` | BBC | IPlayer, BBC Sounds, Bitesize and Weather |
| `www.bbc.com` | BBC (international site) | BBC Travel, Culture and other non-news sections |
| `www.br.de` | Bayerischer Rundfunk (BR24) | BR's programme pages and radio player |
| `www.cbc.ca` | CBC | CBC Radio, Kids and Arts pages on www.cbc.ca |
| `www.dr.dk` | DR Nyheder | DRTV and DR Lyd |
| `www.gazeta.pl` | Gazeta.pl | Portal homepage (email on poczta.gazeta.pl is not blocked) |
| `www.globo.com` | Globo.com portal homepage | Homepage also carries sport and entertainment |
| `www.interia.pl` | Interia | Portal homepage (email on poczta.interia.pl is not blocked) |
| `www.mdr.de` | MDR | MDR's programme pages |
| `www.msn.com` | MSN | MSN Weather, Money and Sports pages |
| `www.ndr.de` | NDR | NDR's programme pages and radio player |
| `www.nine.com.au` | nine.com.au (9News) | Nine's entertainment and lifestyle pages |
| `www.onet.pl` | Onet | Portal homepage (email on poczta.onet.pl is not blocked) |
| `www.qq.com` | Tencent portal homepage | The qq.com portal front page (not QQ, WeChat or QQ Mail) |
| `www.r7.com` | R7 portal homepage | Homepage also carries entertainment and sport |
| `www.rsi.ch` | RSI | RSI Play and RSI's programme pages |
| `www.rte.ie` | RTÉ | RTÉ Player and RTÉ Radio pages |
| `www.rtl.de` | RTL.de | RTL's entertainment pages (RTL+ is on plus.rtl.de) |
| `www.rtp.pt` | RTP | RTP Play |
| `www.rtr.ch` | RTR | RTR's Play and programme pages |
| `www.rts.ch` | RTS | RTS Play and RTS's programme pages |
| `www.rtve.es` | RTVE Noticias | RTVE Play |
| `www.sbs.com.au` | SBS | SBS On Demand and SBS Audio |
| `www.sina.com` | Sina portal homepage (international) | The Sina portal front page |
| `www.sina.com.cn` | Sina portal homepage | The Sina portal front page (not Weibo or Sina Mail) |
| `www.sohu.com` | Sohu portal homepage and articles | The Sohu portal front page |
| `www.sr.de` | Saarländischer Rundfunk | SR's programme pages |
| `www.srf.ch` | SRF News | Play SRF and SRF's programme pages |
| `www.svt.se` | SVT Nyheter | SVT's programme pages (SVT Play is on svtplay.se) |
| `www.swr.de` | SWR | SWR's programme pages |
| `www.terra.com.br` | Terra portal | Homepage also carries sport, entertainment and lifestyle |
| `www.tv2.no` | TV 2 (Norway) | TV 2's sport and entertainment pages (TV 2 Play is on play.tv2.no) |
| `www.uol.com.br` | UOL portal homepage | Homepage also carries sport and entertainment |
| `www.vrt.be` | VRT NWS | VRT MAX and VRT's other pages |
| `www.walla.co.il` | Walla! | The Walla portal homepage (Walla Mail and shopping are on other hosts and stay up) |
| `www.wp.pl` | Wirtualna Polska | Portal homepage (email on poczta.wp.pl is not blocked) |
| `www.yahoo.com` | Yahoo homepage | Yahoo's homepage (Mail and Search are unaffected) |
| `www1.wdr.de` | WDR | WDR's programme pages |
| `www3.nhk.or.jp` | NHK News Web and NHK World-Japan | NHK World-Japan programme pages |
| `yle.fi` | Yle | The wildcard/adblock formats also block Yle Areena (areena.yle.fi) |
<!-- mixed:end -->

To keep one of these working, add an exception for it in your blocker.

## Limitations

- **News inside other apps and sites isn't blocked**: social media feeds, search
  results ("Top stories"), YouTube, podcasts, and phone news widgets that use shared
  platform APIs. Pair this list with a social-media list if those are a problem.
- **Browsers with DNS-over-HTTPS** bypass hosts files and local DNS blockers. Turn it
  off or point it at your blocker.
- **The Wikidata part is filtered, not reviewed.** It adds about 10,000 smaller sites
  automatically. Outlets that Wikidata classes as gaming, sports or trade publications are
  dropped, and anything whose description, genre or hostname suggests a specialist outlet
  goes to a review queue instead of the list. Many Wikidata entries have no description, so
  some specialist, defunct or off-topic sites still get through. Popular domains are never
  added automatically. If something's wrong, [report it](../../issues/new/choose).
- **The curated core was compiled with an AI model**, not by a person working site by site.
  See [How it's built](#how-its-built). Expect some mistakes at this scale.

## How it's built

```
data/curated/*.txt     curated outlets, by region                 ─┐
data/generated/        news outlets from Wikidata, DNS results    ─┼─► scripts/build.py ─► lists/
data/allow.txt         domains never blocked                      ─┘
```

1. **Curated outlets** (`data/curated/`) are the core: major and regional news sites in
   every region, plus aggregators. The first version was compiled with an AI model (Claude).
   It went through the most popular domains that Wikidata lists as news outlets one by one,
   then added outlets Wikidata was missing from its own knowledge. Every hostname resolves in
   DNS (checked weekly), and most additions were checked against the site's live homepage.
   Entries are hostnames; a comment starting `mixed:` documents what else blocking that host
   breaks.
2. **Wikidata** supplies the long tail. `scripts/refresh.py` asks for everything that is a
   newspaper, news website, news agency, news magazine or news channel (the classes are in
   `data/wikidata-classes.txt`) and still has an official website. It then drops:
   - defunct outlets and old website addresses;
   - outlets Wikidata also classes as something out of scope: video game, sports and trade
     publications, academic journals, shops, databases and the like;
   - outlets whose Wikidata genre or main subject is sport, music, film, technology,
     science, fashion or similar;
   - government, military and education domains;
   - websites that are just a page on a shared host;
   - domains in `data/allow.txt`.

   Sites whose Wikidata description, genre or hostname only *suggests* a specialist outlet
   (gaming, tech, trade press, weather, crypto …) aren't added either. They go to
   `data/generated/review.txt`, because the same words turn up in real newspapers too (the
   Weatherford Democrat, the Daily Gamecock).
3. **A popularity guard.** A site on a domain in the [Tranco](https://tranco-list.eu)
   top 25,000 is never added automatically, so a bad Wikidata edit can't block a major
   site. Those go to the review queue too. Each queued site waits for a person to add it to
   a curated file or to `allow.txt`.
4. **DNS checks** remove dead sites and find the subdomains each site uses, for the
   hosts-format lists.
5. **Tests** check every build. A reference set of major news sites must be blocked in every list and
   format, and sites that aren't news (Google, the NHS, Sky Sports, Yahoo Mail and others)
   must not be. A build that fails isn't published.
6. **GitHub Actions** rebuilds the lists on every change and refreshes from Wikidata every
   Monday. A refresh that would shrink the list sharply is refused, so a Wikidata outage
   can't empty it.

Run it yourself with Python 3.10+ and no dependencies:

```sh
python3 scripts/refresh.py   # needs network: Wikidata, DNS, Tranco, Public Suffix List
python3 scripts/build.py     # offline: writes lists/ and the stats above
python3 scripts/test_lists.py
```

## Contributing

Missing a site, or a site blocked by mistake? [Open an issue](../../issues/new/choose) or
see [CONTRIBUTING.md](CONTRIBUTING.md): most changes are one line in `data/curated/` or
`data/allow.txt`.

## Credits and license

The list and scripts are [MIT licensed](LICENSE).

- Outlet data from [Wikidata](https://www.wikidata.org), available under
  [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
- Site popularity from the [Tranco list](https://tranco-list.eu) (Le Pochat et al., NDSS
  2019), used only to decide what needs review.
- Domain parsing with the [Public Suffix List](https://publicsuffix.org) (MPL 2.0),
  downloaded at build time.
