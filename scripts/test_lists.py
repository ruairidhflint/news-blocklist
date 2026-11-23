#!/usr/bin/env python3
"""Checks the built lists against sites that must and must not be blocked.

Run after build.py. Exits 1 if a major news site is missing from any list, or if a
site that isn't news is blocked. CI runs this before publishing rebuilt lists, so a
bad Wikidata edit or a mistaken curated entry can't ship.
"""

from __future__ import annotations

import sys

from common import LISTS, covered_by

# Major outlets, as the hostnames people actually visit. Every list must block these.
MUST_BLOCK = """
www.bbc.co.uk www.bbc.com news.sky.com www.theguardian.com www.telegraph.co.uk www.thetimes.com
www.independent.co.uk inews.co.uk www.dailymail.co.uk www.mirror.co.uk www.express.co.uk www.thesun.co.uk
metro.co.uk www.standard.co.uk www.ft.com www.economist.com www.spectator.co.uk www.newstatesman.com
www.gbnews.com www.lbc.co.uk www.private-eye.co.uk www.heraldscotland.com www.scotsman.com
www.manchestereveningnews.co.uk www.liverpoolecho.co.uk www.walesonline.co.uk www.belfasttelegraph.co.uk
www.irishtimes.com www.independent.ie www.rte.ie www.thejournal.ie www.irishexaminer.com
news.google.com news.yahoo.com uk.news.yahoo.com www.msn.com www.newsnow.co.uk ground.news apple.news flipboard.com
www.nytimes.com www.washingtonpost.com www.wsj.com www.cnn.com edition.cnn.com www.foxnews.com
www.nbcnews.com abcnews.go.com www.cbsnews.com www.npr.org apnews.com www.reuters.com
www.bloomberg.com www.cnbc.com www.politico.com thehill.com www.axios.com www.usatoday.com www.latimes.com
www.nypost.com www.theatlantic.com www.newyorker.com time.com www.newsweek.com www.vox.com www.huffpost.com
www.breitbart.com www.dailywire.com www.newsmax.com www.propublica.org www.businessinsider.com
www.marketwatch.com www.drudgereport.com
www.cbc.ca www.ctvnews.ca globalnews.ca www.theglobeandmail.com www.thestar.com nationalpost.com
www.abc.net.au www.smh.com.au www.theage.com.au www.news.com.au www.theaustralian.com.au www.sbs.com.au
www.nzherald.co.nz www.stuff.co.nz www.rnz.co.nz
www.lemonde.fr www.lefigaro.fr www.liberation.fr www.francetvinfo.fr www.bfmtv.com www.france24.com
www.spiegel.de www.zeit.de www.faz.net www.sueddeutsche.de www.bild.de www.tagesschau.de www.welt.de
www.t-online.de www.dw.com www.nzz.ch www.20min.ch www.blick.ch www.derstandard.at www.krone.at
nos.nl www.nu.nl www.telegraaf.nl www.hln.be www.lesoir.be www.corriere.it www.repubblica.it www.ansa.it
elpais.com www.elmundo.es www.abc.es www.rtve.es www.publico.pt www.vg.no www.nrk.no www.aftonbladet.se
www.svt.se www.dr.dk yle.fi www.hs.fi www.euronews.com www.politico.eu wyborcza.pl www.onet.pl
www.idnes.cz index.hu www.hurriyet.com.tr kyivindependent.com www.pravda.com.ua meduza.io www.rt.com
tass.ru ria.ru www.kommersant.ru
www.aljazeera.com www.alarabiya.net www.haaretz.com www.timesofisrael.com www.ynet.co.il
www.thenationalnews.com timesofindia.indiatimes.com www.ndtv.com www.thehindu.com www.hindustantimes.com
www.indiatoday.in www.dawn.com
www.scmp.com www.xinhuanet.com www.globaltimes.cn news.yahoo.co.jp www3.nhk.or.jp www.asahi.com
www.nikkei.com www.japantimes.co.jp news.naver.com www.chosun.com www.koreaherald.com www.straitstimes.com
www.channelnewsasia.com www.inquirer.net www.kompas.com www.bangkokpost.com
www.news24.com www.iol.co.za nation.africa www.premiumtimesng.com punchng.com
g1.globo.com www1.folha.uol.com.br www.estadao.com.br www.clarin.com www.lanacion.com.ar www.infobae.com
www.eluniversal.com.mx www.milenio.com www.eltiempo.com www.emol.com
""".split()

# Sites that aren't news, including services that share a domain with a news site, and
# specialist outlets Wikidata calls news sites (gaming, weather, trade press, crypto, motoring).
MUST_NOT_BLOCK = """
www.google.com mail.google.com www.youtube.com en.wikipedia.org www.wikipedia.org www.gov.uk www.nhs.uk
www.amazon.co.uk www.apple.com www.microsoft.com outlook.live.com login.yahoo.com mail.yahoo.com
search.yahoo.com www.reddit.com www.facebook.com x.com www.linkedin.com github.com
www.skysports.com www.sky.com www.espn.com www.theverge.com www.wired.com techcrunch.com www.ign.com
www.imdb.com www.netflix.com open.spotify.com www.itv.com www.channel4.com www.pbs.org www.zdf.de
www.france.tv www.tf1.fr www.marca.com www.lequipe.fr weather.com www.metoffice.gov.uk www.accuweather.com
poczta.onet.pl email.t-online.de www.paypal.com www.ebay.co.uk www.booking.com
www.cricbuzz.com www.goal.com www.premierleague.com www.nature.com www.sciencedirect.com
www.eurogamer.es www.pcgames.de www.gamekult.com www.theweather.com www.yourweather.co.uk www.ilmeteo.net
www.fiercepharma.com www.healthcaredive.com www.travelweekly.com www.bondbuyer.com www.techmeme.com
cryptotimes.io www.spaziocrypto.com www.motorcyclenews.com onlinecasino.amsterdam www.autosport.com
""".split()


def load(path) -> set[str]:
    names = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and line[0] not in "#![":
            names.add(line.split()[-1])
    return names


def main() -> int:
    failures = 0
    for variant in ("news", "news-lite"):
        wildcard = load(LISTS / "wildcard" / f"{variant}.txt")
        exact = load(LISTS / "domains" / f"{variant}.txt")
        checks = [
            ("missing from the wildcard formats", [h for h in MUST_BLOCK if not covered_by(h, wildcard)]),
            ("missing from the hosts formats", [h for h in MUST_BLOCK if h not in exact]),
            ("blocked but shouldn't be", [h for h in MUST_NOT_BLOCK if covered_by(h, wildcard) or h in exact]),
        ]
        for problem, hosts in checks:
            if hosts:
                failures += len(hosts)
                print(f"{variant}: {len(hosts)} {problem}: {' '.join(hosts)}")
    if failures:
        return 1
    print(f"OK: all {len(MUST_BLOCK)} major sites blocked and {len(MUST_NOT_BLOCK)} other sites left alone, in both lists")
    return 0


if __name__ == "__main__":
    sys.exit(main())
