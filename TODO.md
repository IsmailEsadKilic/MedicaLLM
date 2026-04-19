hasta, alerji, kronik hastalik, mevcut ilac bilgisi olsun
seçebilsin

scopus api, citation score.

yeni tool: overdose tool. (ayni etken madde kontrol)

pubmed den gelen data debug edilmeli(citations,

title olusturma isini cok erken yapiyo

query tipi : [yazar specific: score olmasin VEYA weight ler degissin (recency agirlikli)]

Drug search markdown format hatasi

makalenin impact score u, refere eden makalelerin impact
IMPACT LER EN YUKSEK WEIGHT
yeni makale ise reference sayısı daha az weight olsun
güvenilirlik score u

cache den alınca source göstermedi
Semaglutide alternatifi mounjaro bulunmalı
drugbank databaseden verilen bilgiler için source (debug)
güvenilirlik ve relevance source ları ayrı ayrı verin (score debug)


---

# Evidence hierarchy — higher = stronger evidence
_EVIDENCE_LEVELS = {
    "meta-analysis": 1.0,
    "systematic review": 0.9,
    "randomized controlled trial": 0.85,
    "clinical trial": 0.75,
    "controlled clinical trial": 0.75,
    "comparative study": 0.6,
    "multicenter study": 0.6,
    "cohort study": 0.55,
    "observational study": 0.5,
    "case-control study": 0.45,
    "review": 0.4,
    "case reports": 0.3,
    "editorial": 0.15,
    "comment": 0.1,
    "letter": 0.1,
}

--- garip garabet ozellikler ---

database de hasta hakkinda bilgiler, arka planda hastanin sormus oldugu drug i, kayitli bilgiler karsilastirmasi.

ayni sifreyi koyunca izin verdi degistirmeye

ai (or maybe user through an ui elemt) dynamically changes the article/doc count for toosl