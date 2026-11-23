# BibTeX corrections for 12outline.tex

Every entry in `refs.bib` started as a Google Scholar export.

- The five entries cited in Assignment 3 (`fan85debruijn`, `burns1993coding`, `berkowitz2016robust`, `schusselbauer2021dothraki`, `cooper2013generalized`) are the author's own Scholar exports from that assignment, where `burns1993coding` was already corrected from the 1992 HP report to the 1993 book chapter. Only the page range of `fan85debruijn` changed here.
- The other 26 entries are the Scholar exports in the class collection *de Bruijn Tori (References)*: `refs.bib`, except `gabric2025constructing`, which is in `refsRelated.bib`. Each keeps its collection key.

Each export was compared with the paper's PDF in the collection's `references` folder first, and with its Crossref record when the PDF did not show a field. Fields not listed below were checked and kept as Scholar gave them. Entries that were checked and needed no change are not listed.

Where the collection held two exports of one paper, the complete one was kept: `hurlbert1993bruijn` over `isaak1993bruijn` (which leaves out the first author) and `kreitzer2024alternating` over `kreitzer2024using`.

| key | field | Scholar value | corrected value | evidence |
|---|---|---|---|---|
| fan85debruijn | pages | `205--221` | `205--213` | Scan in the class references folder, On de Bruijn Arrays.pdf: first page 205, last page 213 (page numbers printed at the foot of the pages) |
| becher2024nested | author | `Becher, Veronica and Carton, Olivier` | `Becher, Ver{\'o}nica and Carton, Olivier` | Nested Perfect Arrays.pdf p.1 prints "Verónica Becher"; Crossref 10.1109/TIT.2024.3445122 gives "Becher, Verónica" (accent only) |
| becher2024nested | number | `4` | `10` | Nested Perfect Arrays.pdf p.1 header "VOL. 70, NO. 10, OCTOBER 2024"; Crossref 10.1109/TIT.2024.3445122 issue 10 |
| becher2024nested | pages | `2840--2851` | `7463--7471` | Nested Perfect Arrays.pdf p.1 (first page 7463) and p.9 (last page 7471); Crossref 10.1109/TIT.2024.3445122 page 7463-7471 |
| becher2024nested | year | `2024` | `2024` (kept) | Online first 16 Aug 2024 and printed issue Oct 2024 (PDF p.1 footnote); same year, no change |
| becher2024nested | doi | (missing) | `10.1109/TIT.2024.3445122` | Nested Perfect Arrays.pdf p.1 "Digital Object Identifier 10.1109/TIT.2024.3445122"; Crossref |
| bruckstein2012simple | author | `Bruckstein, Alfred M and ... Holt, Robert J and ...` | `Bruckstein, Alfred M. and ... Holt, Robert J. and ...` | Simple and Robust Binary Self-Location Patterns.pdf p.1 prints "Alfred M. Bruckstein", "Robert J. Holt"; Crossref 10.1109/TIT.2012.2191699 (periods on initials only; plain style would otherwise print "Alfred M Bruckstein") |
| bruckstein2012simple | journal | `IEEE transactions on information theory` | `IEEE Transactions on Information Theory` | Crossref 10.1109/TIT.2012.2191699 container-title (capitalization only; the PDF is the arXiv preprint and names no journal) |
| bruckstein2012simple | publisher | `Ieee` | `IEEE` | Crossref 10.1109/TIT.2012.2191699 publisher "Institute of Electrical and Electronics Engineers (IEEE)" (capitalization only) |
| bruckstein2012simple | doi | (missing) | `10.1109/TIT.2012.2191699` | Crossref 10.1109/TIT.2012.2191699 (volume 58, issue 7, pages 4884-4889, July 2012, all matching Scholar) |
| chee2022robust | volume | `51` | `49` | Crossref 10.1137/19M1253472 volume 49 |
| chee2022robust | number | `5` | `2` | Crossref 10.1137/19M1253472 issue 2 |
| chee2022robust | pages | `1621--1651` | `284--317` | Crossref 10.1137/19M1253472 page 284-317 |
| chee2022robust | year | `2022` | `2020` | Crossref 10.1137/19M1253472 published-print 2020 (online 23 Mar 2020, same year). A Crossref title search finds no SICOMP item at 51(5) p.1621 for this paper |
| chee2022robust | doi | (missing) | `10.1137/19M1253472` | Crossref 10.1137/19M1253472 |
| chee2022robust | note | | | The folder PDF "Binary Robust Positioning Patterns with Low Redundancy and.pdf" is the SODA 2019 conference version (different title, Copyright 2019 SIAM, pp. 2171-2184 per Crossref 10.1137/1.9781611975482.131). Its p.1 confirms the five authors and their order. Journal fields above come from Crossref only |
| cock1988toroidal | title | `Toroidal tilings from de Bruijn-Good cyclic sequences` | `Toroidal tilings from de {B}ruijn-{G}ood cyclic sequences` | Toroidal Tilings From de bruijn good cyclic sequences.pdf p.1 (scan, title "DE BRUIJN-GOOD", heading "De Bruijn-Good cyclic sequences"); brace protection of the surnames Bruijn and Good |
| cock1988toroidal | author | `Cock, John C` | `Cock, John C.` | Toroidal Tilings From de bruijn good cyclic sequences.pdf p.1 prints "John C. COCK"; Crossref 10.1016/0012-365X(88)90095-7 "Cock, John C." (period on initial only) |
| cock1988toroidal | journal | `Discrete mathematics` | `Discrete Mathematics` | Toroidal Tilings From de bruijn good cyclic sequences.pdf p.1 header "Discrete Mathematics 70 (1988) 209-210" (capitalization only) |
| cock1988toroidal | doi | (missing) | `10.1016/0012-365X(88)90095-7` | Crossref 10.1016/0012-365X(88)90095-7 (also confirms issue 2, which the PDF does not print) |
| etzion1988constructions | journal | `IEEE Transactions on information theory` | `IEEE Transactions on Information Theory` | Constructions for perfect maps and pseudorandom arrays.pdf p.1 header "IEEE TRANSACTIONS ON INFORMATION THEORY, VOL. 34, NO. 5, SEPTEMBER 1988" (capitalization only) |
| etzion1988constructions | doi | (missing) | `10.1109/18.21260` | Crossref 10.1109/18.21260 (volume 34, issue 5, pages 1308-1316, Sept 1988, matching the PDF p.1 and p.9) |
| etzion2024pseduo | title | `{Pseduo-random and de Bruijn array codes}` | `Pseduo-Random and de {B}ruijn Array Codes` | Double braces had frozen the lower case. Crossref ("Pseduo- Random and de Bruijn Array Codes") and the PDF capitalise the words. The misspelling "Pseduo" is in the published title, so it stays |
| etzion2024pseduo | doi | (missing) | `10.1109/ISIT57864.2024.10619645` | Crossref; also in the first-page footnote of paper 3 (p. 6204) |
| gabric2025constructing | doi | (missing) | 10.1007/s10623-025-01581-4 | Crossref |
| herout2013five | author | `... Zacharias, Michal ...` | `... Zachari{\'a}{\v{s}}, Michal ...` | Five Shades of Grey for Fast and Reliable Camera Pose Estimation.pdf p.1 author line "Michal Zachariáš" (Crossref 10.1109/CVPR.2013.182 strips diacritics, "Zacharia", so the PDF is followed) |
| herout2013five | doi | (missing) | `10.1109/CVPR.2013.182` | Five Shades of Grey for Fast and Reliable Camera Pose Estimation.pdf p.1 text layer "DOI 10.1109/CVPR.2013.182"; Crossref 10.1109/CVPR.2013.182 (proceedings-article, pages 1384-1390, 2013, matching Scholar) |
| horan2016locating | title | `Locating patterns in the de Bruijn torus` | `Locating patterns in the de {B}ruijn torus` | Locating patterns in the de Bruijn torus.pdf p.1; brace protection |
| horan2016locating | year | `2016` | `2016` (kept) | PDF p.1 "Available online 17 December 2015"; printed issue 339(4), April 2016 (Crossref 10.1016/j.disc.2015.11.015). Printed-issue year kept |
| horan2016locating | doi | (missing) | `10.1016/j.disc.2015.11.015` | Locating patterns in the de Bruijn torus.pdf metadata "doi:10.1016/j.disc.2015.11.015"; Crossref (also confirms issue 4, which the PDF does not print) |
| hostettler2016real | title | 2d | `2{D}` | PDF title "2D" |
| hostettler2016real | doi | (missing) | 10.1109/ICRA.2016.7487653 | Crossref |
| hostettler2016real | booktitle | `2016 IEEE international conference on robotics and automation (ICRA)` | `2016 IEEE International Conference on Robotics and Automation (ICRA)` | Official proceedings title (capitalization only) |
| hurlbert1993bruijn | title | `On the de Bruijn torus problem` | `On the de {B}ruijn torus problem` | On the de Bruijn Torus Problem.pdf p.1; brace protection |
| hurlbert1993bruijn | doi | (missing) | `10.1016/0097-3165(93)90087-O` | On the de Bruijn Torus Problem.pdf metadata "PII: 0097-3165(93)90087-O"; Crossref 10.1016/0097-3165(93)90087-O (also confirms issue 1) |
| hurlbert1995new | title | `New constructions for de Bruijn tori` | `New constructions for {D}e {B}ruijn tori` | New Constructions for De Bruijn Tori.pdf p.1 title and abstract print "De Bruijn" with capital D mid-sentence; Crossref 10.1007/BF01390770 title "New constructions for De Bruijn tori" |
| hurlbert1995new | publisher | `Springer` | `Springer` (kept) | PDF p.1 prints "Kluwer Academic Publishers" (1995 publisher); Crossref 10.1007/BF01390770 lists "Springer Science and Business Media LLC". Kept the Scholar value |
| hurlbert1995new | doi | (missing) | `10.1007/BF01390770` | Crossref 10.1007/BF01390770 (also confirms issue 1, which the PDF does not print) |
| kreitzer2024alternating | title | `Using alternating de Bruijn sequences to construct de Bruijn tori` | `Using alternating de {B}ruijn sequences to construct de {B}ruijn tori` | Capital protection only. PDF "Using alternating de Bruijn sequences to construct de Bruijn tori.pdf" p.1 title |
| kreitzer2024alternating | doi | (missing) | `10.1007/s10623-023-01351-0` | Same PDF p.1 header line; Crossref 10.1007/s10623-023-01351-0 |
| kreitzer2024alternating | (all other fields) | type, authors, journal, volume 92, pages 1439--1454, year 2024 | unchanged | PDF p.1 header "Designs, Codes and Cryptography (2024) 92:1439-1454". Issue 5 is not printed in the PDF; Crossref 10.1007/s10623-023-01351-0 gives issue 5 (print issue May 2024, online 6 Feb 2024, same year) |
| mao2025homomorphism | year | 2025 | 2026 | PDF header "Measurement 261 (2026) 119631"; Crossref issued 2026-02. Online 1 Dec 2025 (PDF p. 1). Key keeps 2025 |
| mao2025homomorphism | volume | (missing) | 261 | PDF header; Crossref |
| mao2025homomorphism | title | 3-DoF | `3-{DoF}` | protect capitals |
| mao2025homomorphism | doi | (missing) | 10.1016/j.measurement.2025.119631 | PDF p. 1; Crossref |
| maurice2011pattern | title | `... driven by the Hamming distance ...` | `... driven by the {H}amming distance ...` | plain.bst would print "hamming" |
| maurice2011pattern | doi | (missing) | `10.1109/CVPR.2011.5995490` | Crossref |
| mitchell1994decoding | author | `Mitchell, Chris J and Paterson, Kenneth G` | `Mitchell, Chris J. and Paterson, Kenneth G.` | Punctuation only (initials lacked periods, so plain style printed "Chris J Mitchell"). PDF "Decoding perfect maps.pdf" p.1; Crossref 10.1007/BF01388557 ("Chris J.", "Kenneth G.") |
| mitchell1994decoding | doi | (missing) | `10.1007/BF01388557` | Crossref 10.1007/BF01388557 (title, journal, volume, issue, pages match) |
| mitchell1994decoding | (all other fields) | volume 4, number 1, pages 11--30, year 1994 | unchanged | The PDF is the authors' preprint dated 19 March 1993 and prints no volume or pages; confirmed by Crossref 10.1007/BF01388557 only |
| morano1998structured | author | `... and Zietz, Stanley and Nissano, J` | `... and Zietz, Stanley and Nissanov, Jonathan` | Last author's surname was truncated and his given name reduced to an initial. PDF "Structured light using pseudorandom codes.pdf" p.1 [322] author line "and Jonathan Nissanov". Crossref 10.1109/34.667888 has the same wrong "J. Nissano", which is probably where Scholar got it; PDF takes priority |
| morano1998structured | author | `Morano, Raymond A` | `Morano, Raymond A.` | Punctuation only. PDF p.1 [322] "Raymond A. Morano" |
| morano1998structured | doi | (missing) | `10.1109/34.667888` | Crossref 10.1109/34.667888 (title, volume, issue, pages match) |
| morano1998structured | (all other fields) | volume 20, number 3, pages 322--327, year 1998 | unchanged | PDF p.1 header "VOL. 20, NO. 3, MARCH 1998", first page 322; PDF p.6 last page 327 |
| paterson1994perfect | author | `Paterson, Kenneth G` | `Paterson, Kenneth G.` | Punctuation only. PDF "Perfect Maps.pdf" p.1 [743] "Kenneth G. Paterson" |
| paterson1994perfect | doi | (missing) | `10.1109/18.335886` | Crossref 10.1109/18.335886 (title, volume, issue, pages match); the scanned PDF prints no DOI |
| paterson1994perfect | (all other fields) | volume 40, number 3, pages 743--753, year 1994 | unchanged | PDF p.1 header "VOL. 40, NO. 3, MAY 1994", first page 743; PDF p.11 last page 753 |
| scheinerman2001determining | doi | (missing) | 10.1109/70.976017 | Crossref (its title misspells "Brujin"; the PDF has "Bruijn", so the Scholar title is kept) |
| schmid2022determining | entry type | `@incollection` | `@inproceedings` | Crossref type proceedings-article; PDF p. 1 "SIGGRAPH '22 Posters" |
| schmid2022determining | author | Schmid, Wimmer, Lippl | Schmid, Lippl, Wimmer | PDF byline and ACM Reference Format, p. 1: "Andreas Schmid, Stefan Lippl, and Raphael Wimmer". Crossref has Schmid, Wimmer, Lippl; PDF followed |
| schmid2022determining | title | De-Bruijn ... CNN | `{D}e-{B}ruijn ... {CNN}` | protect capitals |
| schmid2022determining | doi | (missing) | 10.1145/3532719.3543259 | PDF p. 1; Crossref |
| shiu1997decoding | journal | ARS COMBINATORIA-WATERLOO THEN WINNIPEG- | Ars Combinatoria | PDF footer p. 33: "ARS COMBINATORIA 47(1997), pp. 33-48" |
| shiu1997decoding | author | Shiu, WC | Shiu, W. C. | PDF byline "W.C. Shiu"; "WC" would print as a single initial |
| shiu1997decoding | title | de Bruijn ... FFMS | `de {B}ruijn ... {FFMS}` | protect capitals |
| shiu1997decoding | doi | (missing) | unconfirmed, left out | no Crossref record found |
| stelldinger2024puzzleboard | title | `Puzzleboard: A new camera calibration pattern with position encoding` | `{PuzzleBoard}: A new camera calibration pattern with position encoding` | Scholar had the wrong case ("Puzzleboard"). PDF "PuzzleBoard - A New Camera Calibration Pattern with Position Encoding.pdf" p.1 title "PuzzleBoard"; Crossref 10.1007/978-3-031-85187-2_21 |
| stelldinger2024puzzleboard | booktitle | `DAGM German Conference on Pattern Recognition` | `Pattern Recognition: 46th DAGM German Conference, DAGM GCPR 2024, Munich, Germany, September 10--13, 2024, Proceedings, Part II` | Vague venue replaced by the proceedings volume title. Crossref book record 10.1007/978-3-031-85187-2 (title + subtitle); chapter record 10.1007/978-3-031-85187-2_21 (container "Pattern Recognition") |
| stelldinger2024puzzleboard | series | (missing) | `Lecture Notes in Computer Science` | Crossref 10.1007/978-3-031-85187-2_21 container-title |
| stelldinger2024puzzleboard | year | `2024` | `2025` | Crossref 10.1007/978-3-031-85187-2_21: published-print 2025, online 24 Apr 2025. The conference was held in 2024 (named in the booktitle) but the proceedings volume was published in 2025. Key keeps "2024" per rule 1 |
| stelldinger2024puzzleboard | organization / publisher | `organization={Springer}` | `publisher={Springer}` | Springer publishes the LNCS volume; it is not the conference organiser. Crossref 10.1007/978-3-031-85187-2_21 publisher "Springer Nature Switzerland". Printed output is the same in plain style |
| stelldinger2024puzzleboard | doi | (missing) | `10.1007/978-3-031-85187-2_21` | Crossref 10.1007/978-3-031-85187-2_21 |
| stelldinger2024puzzleboard | (authors, pages) | Stelldinger, Sch{\"o}nherr, Biermann; 332--347 | unchanged | Authors: PDF p.1 (arXiv:2409.20127v1 preprint) and Crossref. Pages: Crossref only (the preprint has no proceedings page numbers) |
| stelldinger2024puzzleboard | volume | (missing) | `15298` | Springer book page for DOI 10.1007/978-3-031-85187-2: "Lecture Notes in Computer Science (LNCS, volume 15298)" |
| szentandrasi2012uniform | title | `Uniform marker fields: Camera localization by orientable de bruijn tori` | `Uniform {M}arker {F}ields: Camera localization by orientable {D}e {B}ruijn tori` | Capital protection only; now matches the official title exactly. "Bruijn" was lowercase in Scholar. The title in the PDF metadata of "Uniform Marker Fields- Camera localization by orientable De Bruijn tori.pdf" and in Crossref 10.1109/ISMAR.2012.6402593 is "Uniform Marker Fields: Camera localization by orientable De Bruijn tori". The paper capitalises "Marker Field(s)" as a coined term throughout (PDF p.1 abstract) |
| szentandrasi2012uniform | author | `Szentandrasi, Istvan and ... Dubska, Marketa ...` | `Szentandr{\'a}si, Istv{\'a}n and ... Dubsk{\'a}, Mark{\'e}ta ...` | Missing diacritics. PDF p.1 author line "István Szentandrási", "Markéta Dubská" (Crossref lists ASCII-only names; PDF takes priority). The other four names already matched the PDF |
| szentandrasi2012uniform | doi | (missing) | `10.1109/ISMAR.2012.6402593` | PDF metadata (Subject field); Crossref 10.1109/ISMAR.2012.6402593 |
| szentandrasi2012uniform | (all other fields) | booktitle, pages 319--320, year 2012, organization IEEE | unchanged | PDF p.1 printed page 319, p.2 printed page 320; PDF p.1 footer "IEEE International Symposium on Mixed and Augmented Reality 2012 ... 5-8 November 2012"; Crossref container title identical to Scholar booktitle |
| wei2021nearly | year | `2021` | `2022` | Online-first year differs from print year. PDF "Nearly_Optimal_Robust_Positioning_Patterns, Hengjia We, 2022.pdf" p.1 [193] header "VOL. 68, NO. 1, JANUARY 2022"; footnote "Date of publication October 8, 2021". Crossref 10.1109/TIT.2021.3118905 published-print 2022-01. Volume 68(1) pages 193-203 belong to the January 2022 issue. Key keeps "2021" per rule 1 |
| wei2021nearly | doi | (missing) | `10.1109/TIT.2021.3118905` | PDF p.1 [193] footnote URL; Crossref 10.1109/TIT.2021.3118905 |
| wei2021nearly | (all other fields) | author, volume 68, number 1, pages 193--203 | unchanged | PDF p.1 [193]; PDF p.11 last page 203 |
| xu2007robust | title | `Robust dense depth acquisition using 2-D De Bruijn structured light` | `Robust dense depth acquisition using {2-D} {D}e {B}ruijn structured light` | Capital protection only (plain style would print "2-d de bruijn"). PDF "Robust dense depth acquisition using 2-D de Bruijn structured light.pdf" p.1 title; the abstract writes "2-D De Bruijn" mid-sentence |
| xu2007robust | booktitle | `International Conference on Entertainment Computing` | `Entertainment Computing -- ICEC 2007: 6th International Conference, Shanghai, China, September 15--17, 2007, Proceedings` | Vague venue replaced by the proceedings volume title. PDF p.1 footer "ICEC 2007, LNCS 4740, pp. 304-314, 2007"; Crossref book record 10.1007/978-3-540-74873-1 (title + subtitle) |
| xu2007robust | series | (missing) | `Lecture Notes in Computer Science` | PDF p.1 footer "LNCS"; Crossref 10.1007/978-3-540-74873-1_37 container-title |
| xu2007robust | volume | (missing) | `4740` | PDF p.1 footer "LNCS 4740" |
| xu2007robust | organization / publisher | `organization={Springer}` | `publisher={Springer}` | Springer publishes the LNCS volume; the conference copyright holder is IFIP (PDF p.1 footer). Crossref 10.1007/978-3-540-74873-1_37 publisher "Springer Berlin Heidelberg". Printed output is the same in plain style |
| xu2007robust | doi | (missing) | `10.1007/978-3-540-74873-1_37` | Crossref 10.1007/978-3-540-74873-1_37 (title, pages, authors match); not printed in the PDF |
| xu2007robust | (all other fields) | authors, pages 304--314, year 2007 | unchanged | PDF p.1 author line and footer; PDF p.11 last page 314 |
| zhu2022hydramarker | title | `HydraMarker: Efficient, flexible, and multifold marker field generation` | `{HydraMarker}: Efficient, flexible, and multifold marker field generation` | Capital protection only (plain style would print "Hydramarker"). PDF "HydraMarker_Efficient_Flexible_and_Multifold_Marker_Field_Generation.pdf" p.1 [5849] title |
| zhu2022hydramarker | year | `2022` | `2023` | Online-first year differs from print year. PDF p.1 [5849] header "VOL. 45, NO. 5, MAY 2023"; footnote "Date of publication 10 October 2022; date of current version 3 April 2023". Crossref 10.1109/TPAMI.2022.3212862 published-print 2023-05-01. Key keeps "2022" per rule 1 |
| zhu2022hydramarker | doi | (missing) | `10.1109/TPAMI.2022.3212862` | PDF p.1 [5849] "Digital Object Identifier no. 10.1109/TPAMI.2022.3212862"; Crossref |
| zhu2022hydramarker | (all other fields) | authors, volume 45, number 5, pages 5849--5861 | unchanged | PDF p.1 [5849] author line and header; PDF p.13 last page 5861 |
