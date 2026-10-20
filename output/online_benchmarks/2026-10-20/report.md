# Sequential online ABox benchmark

Started: 2026-10-20T17:38:43.813896+00:00

Original publisher responses; one subprocess at a time; models disabled.
Pass means execution and logical validation, not domain truth or human consensus.

| Dataset | Result | Normalized triples | Pipeline seconds | Accepted | Withheld | Type / role recall |
|---|---|---:|---:|---:|---:|---|
| [W3C SPARQL optional person data](https://www.w3.org/2001/sw/DataAccess/tests/data-r2/optional/complex-data-1.ttl) | passed | 12 | 5.47 | 0 | 6 | n/a / 0.000 |
| [Tim Berners-Lee public FOAF profile](https://www.w3.org/People/Berners-Lee/card) | passed | 86 | 4.88 | 0 | 90 | n/a / 0.000 |
| [DBpedia Leipzig](https://dbpedia.org/data/Leipzig.ttl) | pipeline_error | 12330 | 4.37 | — | — | n/a / n/a |
| [DBpedia Ada Lovelace](https://dbpedia.org/data/Ada_Lovelace.ttl) | pipeline_error | 828 | 1.62 | — | — | n/a / n/a |
| [DBpedia Berlin](https://dbpedia.org/data/Berlin.ttl) | pipeline_error | 52950 | 38.45 | — | — | n/a / n/a |
| [GeoNames Bangladesh](https://sws.geonames.org/1210997/about.rdf) | pipeline_error | 279 | 1.17 | — | — | n/a / n/a |
| [Wikidata Douglas Adams](https://www.wikidata.org/wiki/Special:EntityData/Q42.ttl) | pipeline_error | 17700 | 13.99 | — | — | n/a / n/a |
| [Nobel Prize Wilhelm Conrad Roentgen](https://data.nobelprize.org/resource/laureate/1) | download_error | — | — | — | — | n/a / n/a |

## Failure details

### DBpedia Leipzig

```text
Running initialize_transport
Tier=statistical, Decision=clef-flash:latest
Running parse_input
Loaded 12330 triples; training=10881, subjects=5838, untyped=5837
Running cluster_signatures
Consolidated clusters: 123
Running detect_namespace
Detected Namespace: http://dbpedia.org/resource/
Running name_concepts
Cluster 84ce8e69916bae70: Concept84ce8e (131 instances)
Cluster 589d309d446e1368: Concept589d30 (1 instances)
Cluster f9b3cc89d38eca7a: WikiPageWiki (4258 instances)
Cluster 07cd7ff96a425f58: Concept07cd7f (422 instances)
Cluster b1545784a9ddeefa: CityWikiPage (2 instances)
Cluster f4f9e72225f371f1: GarrisonWikiPage (3 instances)
Cluster fb756d2b5f2df951: WikiPageWiki_2 (154 instances)
Cluster 075d0d2007a183aa: WikiPageWiki_3 (59 instances)
Cluster 1a0cdc2effb36513: WikiPageWiki_4 (1 instances)
Cluster c8de5573f00a08eb: WikiPageWiki_5 (1 instances)
Cluster 31a7e63f8eb61222: CityWikiPage_2 (4 instances)
Cluster 9b6446aa9d876460: WikiPageWiki_6 (3 instances)
Cluster bf2036e82695154a: LocationWikiPage (19 instances)
Cluster 6cabc7b7d0c1b538: WikiPageWiki_7 (1 instances)
Cluster 40783a4fa142174b: WikiPageWiki_8 (1 instances)
Cluster f7799c4d3fa5a911: WikiPageWiki_9 (5 instances)
Cluster cda00c52777f3961: City (8 instances)
Cluster 49ff70ae6429c0a3: WikiPageWiki_10 (1 instances)
Cluster 9bc8f6be8b3f4fda: WikiPageWiki_11 (124 instances)
Cluster 9e4214c91fc3174b: BirthPlaceWiki (148 instances)
Cluster c72027fa51250a62: BirthPlaceWiki_2 (86 instances)
Cluster cf851aece003ad66: DeathPlaceWiki (62 instances)
Cluster 5e9f13c997387b08: WikiPageWiki_12 (17 instances)
Cluster 60ec99e5d9650503: DeathPlaceWiki_2 (26 instances)
Cluster 83311efacfeaed94: WikiPageWiki_13 (21 instances)
Cluster d96ca8edab0c529c: BirthPlaceDeath (12 instances)
Cluster c87ccdaed47327d9: LocationLocationTown (4 instances)
Cluster 12794397b9473ccd: HometownWikiPage (1 instances)
Cluster 089d59e595960cd4: BirthPlaceWiki_3 (5 instances)
Cluster 1894de6a5ff76c19: PopulationPlaceWiki (6 instances)
Cluster 845ae8875c19edec: LocationWikiPage_2 (8 instances)
Cluster cdc166aff9e75f36: WikiPageWiki_14 (1 instances)
Cluster 78c089fa7348791f: WikiPageWiki_15 (1 instances)
Cluster e03c39007f77fec4: HometownWikiPage_2 (4 instances)
Cluster f2ab2f21d12effc7: Assembly (12 instances)
Cluster 028334c0967b927b: PremierePlaceWiki (1 instances)
Cluster 53fded1ad9a474de: LocationObject (15 instances)
Cluster aa0e0360b679ebb0: PlaceWikiPage (1 instances)
Cluster 7734eec7d99bca3a: DistrictWikiPage (1 instances)
Cluster a93f1ad0125ca242: Concepta93f1a (1 instances)
Cluster 33daa5dae616f35d: CapitalWikiPage (1 instances)
Cluster bb6906249f760109: CityWikiPage_3 (2 instances)
Cluster 0c5711a17f0f9f60: RouteEndWiki (1 instances)
Cluster 081b6717e6d656e7: WikiPageWiki_16 (1 instances)
Cluster 0f0163e7ca47eaf0: HeadquarterWikiPage (1 instances)
Cluster 36fcd10d3d366077: DeathPlaceWiki_3 (1 instances)
Cluster 949f013ad7e5e405: Concept949f01 (2 instances)
Cluster 5836aeacbb0de117: Concept5836ae (1 instances)
Cluster e234a31d4d9589ec: Concepte234a3 (1 instances)
Cluster 4b8341ad656db8a2: ResidenceWikiPage (1 instances)
Cluster 05f1af6804d83652: Concept05f1af (1 instances)
Cluster af9e58181349ba54: WikiPageWiki_17 (1 instances)
Cluster 9dc97ce1a25047bc: WikiPageRedirects (13 instances)
Cluster 10e8beeff39d597d: AwardWikiPage (1 instances)
Cluster 02e9605691a3317c: WikiPageWiki_18 (1 instances)
Cluster 128016220dd4559f: Concept128016 (1 instances)
Cluster 399a152b273e5c9a: CountryCountry (3 instances)
Cluster f4ec115f6973ecaa: WikiPageWiki_19 (1 instances)
Cluster 257081d3c2f3dfa4: StadiumWikiPage (1 instances)
Cluster 0a3cde4ffef08f2e: Concept0a3cde (2 instances)
Cluster 25bd0635df954566: BirthPlaceClub (5 instances)
Cluster 723bd9a05f5cb4e6: DeathPlaceWiki_4 (1 instances)
Cluster 900a6213383d199b: EducationWikiPage (2 instances)
Cluster 725b024686e36bbc: HeadquarterWikiPage_2 (5 instances)
Cluster 2d332b329f6f0832: Concept2d332b (1 instances)
Cluster 9a96fbc9c8a14c45: HeadquarterLocation (1 instances)
Cluster dc38e464bdf18b93: WikiPageWiki_20 (1 instances)
Cluster d0c39ce6e18787c4: WikiPageWiki_21 (2 instances)
Cluster 7c84be61aca10757: BirthPlaceDeath_2 (7 instances)
Cluster ac2eda051c2be235: WikiPageWiki_22 (1 instances)
Cluster 571c217c347e31d7: WikiPageWiki_23 (3 instances)
Cluster 9f21b59eac79f9d0: Concept9f21b5 (2 instances)
Cluster 7e1c2c4c67101691: LocationWikiPage_3 (3 instances)
Cluster a35cb7a1b75c6ddf: AlmaMaterWiki (2 instances)
Cluster d89c727234a58184: CityWikiPage_4 (2 instances)
Cluster aee23acb0ef45424: DeathPlaceResidence (1 instances)
Cluster 22eb80dc9751f2a4: DeathPlaceWiki_5 (2 instances)
Cluster 621f177da22806d3: ClubDeathPlace (1 instances)
Cluster 180e96814048d12d: HeadquarterWikiPage_3 (1 instances)
Cluster 506572096b9d39bf: WikiPageWiki_24 (2 instances)
Cluster eb2b61fb2d6652d0: EducationWikiPage_2 (1 instances)
Cluster af2e89497cd3ad6c: HeadquarterHeadquartersObject (1 instances)
Cluster 1b229992338e3d28: OccupationWikiPage (1 instances)
Cluster 04c56cb3ce0ad47a: LocationCityWiki (1 instances)
Cluster 1590413c666a1db5: NearestCityWiki (1 instances)
Cluster 55a5fcb17c0fdbf9: WikiPageWiki_25 (4 instances)
Cluster c4cc3b56ea242082: Borough (8 instances)
Cluster 8c215f7fafae3b3a: WikiPageWiki_26 (1 instances)
Cluster 43d43bb45359c734: WikiPageWiki_27 (1 instances)
Cluster 6991f82ae515af2f: WikiPageWiki_28 (1 instances)
Cluster 503ecdc53e9c06f2: Object (1 instances)
Cluster 041d2cc82bab9358: WikiPageWiki_29 (2 instances)
Cluster 77d38e5a8e0254e6: CityWikiPage_5 (1 instances)
Cluster 6e67747497752dbf: BirthPlaceWiki_4 (6 instances)
Cluster ee7579be7c49a521: LocationWikiPage_4 (1 instances)
Cluster 49bb73da38115586: CityLocationCity (1 instances)
Cluster 897dc36d36d0612f: WikiPageWiki_30 (1 instances)
Cluster 00bd3fcd1e780576: LocationPictureWiki (1 instances)
Cluster 1fa9c479710eeb08: WikiPageWiki_31 (1 instances)
Cluster c8ef87f25549d7cd: WikiPageWiki_32 (1 instances)
Cluster 646ab36b4a2dd215: RegionServedWiki (1 instances)
Cluster b8d1d7ecfcef3bc2: Hypernym (1 instances)
Cluster f082ca342307529a: WikiPageWiki_33 (2 instances)
Cluster 2c8c5f38af381ddc: Concept2c8c5f (48 instances)
Cluster 7580b47df40efbb2: PublisherWikiPage (2 instances)
Cluster 609397404b0e9a63: Owner (2 instances)
Cluster 15647fcf1dce2ff2: WikiPageWiki_34 (1 instances)
Cluster 5fadd8e41adcb55b: WikiPageWiki_35 (1 instances)
Cluster 42e0b769858b6016: CreatorWikiPage (1 instances)
Cluster 7c9a34413cf7baa8: WikiPageWiki_36 (1 instances)
Cluster e6894521a93be658: Concepte68945 (1 instances)
Cluster 75f382a4df112f95: GarrisonWikiPage_2 (1 instances)
Cluster 92a5c49aac1e3343: LocationOperatorWiki (1 instances)
Cluster 38866b141a846081: Concept38866b (1 instances)
Cluster 5cdea6112f946629: PrimaryTopic (1 instances)
Cluster 23fde4c4b70d6b9a: Concept23fde4 (1 instances)
Cluster 355f6a6e8c7e6941: Concept355f6a (1 instances)
Cluster 7ac0468ee6e353e5: Concept7ac046 (11 instances)
Cluster 4dcc4e81323bd334: Concept4dcc4e (1 instances)
Cluster eb540198970cd56a: Concepteb5401 (1 instances)
Cluster b63f1d80a82a9a37: Conceptb63f1d (1 instances)
Cluster f90a7eb2285f2d8f: Conceptf90a7e (5 instances)
Cluster 594aa9caef48060a: Concept594aa9 (2 instances)
Running mine_taxonomy
Taxonomic candidate pairs: 4451
Running mine_roles_and_restrictions
abox2tbox: ValueError: Property-chain join exceeds MAX_JOIN_EDGES; output preserved

```

### DBpedia Ada Lovelace

```text
Running initialize_transport
Tier=statistical, Decision=clef-flash:latest
Running parse_input
Loaded 828 triples; training=757, subjects=472, untyped=471
Running cluster_signatures
Consolidated clusters: 29
Running detect_namespace
Detected Namespace: http://dbpedia.org/resource/
Running name_concepts
Cluster 7ac0468ee6e353e5: Concept7ac046 (30 instances)
Cluster 84ce8e69916bae70: Concept84ce8e (16 instances)
Cluster 589d309d446e1368: Concept589d30 (1 instances)
Cluster f9b3cc89d38eca7a: WikiPageWiki (119 instances)
Cluster 2b1e52b9a6ff7383: WikiPageDisambiguates (1 instances)
Cluster 9dc97ce1a25047bc: WikiPageRedirects (18 instances)
Cluster 07cd7ff96a425f58: Concept07cd7f (162 instances)
Cluster 9bc8f6be8b3f4fda: WikiPageWiki_2 (36 instances)
Cluster a4a1d28ad2c424c2: ParentWikiPage (1 instances)
Cluster b68d13f8e46067b3: NotableStudentWiki (1 instances)
Cluster 949f013ad7e5e405: Concept949f01 (19 instances)
Cluster 5836aeacbb0de117: Concept5836ae (10 instances)
Cluster 10ddd5812e331c7c: Concept10ddd5 (1 instances)
Cluster 3ed254368871b635: KnownForWiki (2 instances)
Cluster 72404b8e8363ade6: Concept72404b (2 instances)
Cluster 10e8beeff39d597d: AwardWikiPage (1 instances)
Cluster 6231bda21929293a: ChildWikiPage (1 instances)
Cluster 8b85c426ba19fcf2: WikiPageWiki_3 (1 instances)
Cluster 9956e1b1b5eb006f: Concept9956e1 (1 instances)
Cluster 05f1af6804d83652: Concept05f1af (1 instances)
Cluster 746e143b5aada5cf: Concept746e14 (1 instances)
Cluster daeef4156335b7ea: Relative (1 instances)
Cluster 2c8c5f38af381ddc: Concept2c8c5f (39 instances)
Cluster 9ffc1a0b1bd405a5: Concept9ffc1a (1 instances)
Cluster 1719b724517ee6e2: NonFictionSubject (1 instances)
Cluster 1c3083b237cb1e2a: Concept1c3083 (1 instances)
Cluster 50716343a8335958: Concept507163 (1 instances)
Cluster 23fde4c4b70d6b9a: Concept23fde4 (1 instances)
Cluster 4dcc4e81323bd334: Concept4dcc4e (1 instances)
Running mine_taxonomy
Taxonomic candidate pairs: 455
Running mine_roles_and_restrictions
Scored restriction candidates: 90, property chains: 2
Running adjudicate_taxonomy
Evidence-admitted subclass hypotheses: 0
Running assess_disjointness
Withheld 36 disjointness proposals: absence is not negation
Running adjudicate_roles
Evidence decisions: {'withheld': 1056}
Running repair_taxonomy
Greedy repair removed 0 edges; reduced taxonomy has 0 edges
Running repair_consistency
Disjoint conflicts removed=0, remaining=0; irregular chains rejected=0
Running infer_domains_ranges
Running build_ontology
Running validate_and_export
abox2tbox: RuntimeError: Complete export validation failed (TBox + training ABox): Java error message is:
Exception in thread "main" org.semanticweb.HermiT.datatypes.UnsupportedDatatypeException: Literals can only use the datatypes from the OWL 2 datatype map, see
http://www.w3.org/TR/owl2-syntax/#Datatype_Maps.
The datatype 'http://www.w3.org/2001/XMLSchema#date' is not part of the OWL 2 datatype map and
HermiT cannot parse this literal.
	at org.semanticweb.HermiT.datatypes.DatatypeRegistry.parseLiteral(Unknown Source)
	at org.semanticweb.HermiT.model.Constant.create(Unknown Source)
	at org.semanticweb.HermiT.structural.OWLClausification$DataRangeConverter.visit(Unknown Source)
	at uk.ac.manchester.cs.owl.owlapi.OWLLiteralImplNoCompression.accept(OWLLiteralImplNoCompression.java:281)
	at org.semanticweb.HermiT.structural.OWLClausification$FactClausifier.visit(Unknown Source)
	at uk.ac.manchester.cs.owl.owlapi.OWLDataPropertyAssertionAxiomImpl.accept(OWLDataPropertyAssertionAxiomImpl.java:97)
	at org.semanticweb.HermiT.structural.OWLClausification.clausify(Unknown Source)
	at org.semanticweb.HermiT.structural.OWLClausification.preprocessAndClausify(Unknown Source)
	at org.semanticweb.HermiT.Reasoner.loadOntology(Reasoner.java:117)
	at org.semanticweb.HermiT.Reasoner.<init>(Reasoner.java:108)
	at org.semanticweb.HermiT.Reasoner.<init>(Reasoner.java:86)
	at org.semanticweb.HermiT.cli.CommandLine.main(CommandLine.java:830)


```

### DBpedia Berlin

```text
nces)
Cluster 7e1c2c4c67101691: LocationWikiPage_4 (22 instances)
Cluster f669144ccc1d9a73: FoundationPlaceFoundation (1 instances)
Cluster 1894de6a5ff76c19: PopulationPlaceWiki_2 (13 instances)
Cluster aeeafa9319807d14: WikiPageWiki_37 (3 instances)
Cluster eae6b1ab016e9f52: LocationRouteStart (1 instances)
Cluster 10e8beeff39d597d: AwardWikiPage (3 instances)
Cluster b31ccb7dd6703e3f: WikiPageWiki_38 (2 instances)
Cluster cf655754119aa50e: ResidenceWikiPage (7 instances)
Cluster 0bbf174ea7ebd2ab: CityStateWiki (1 instances)
Cluster af627591df4e4e86: WikiPageWiki_39 (4 instances)
Cluster 5389c9ebff4aa4ff: LocatedInArea (4 instances)
Cluster aaa8a6f6a6abba3a: LocationCityWiki (22 instances)
Cluster 9dc97ce1a25047bc: WikiPageRedirects (16 instances)
Cluster 9575da2a443b47ac: WikiPageWiki_40 (15 instances)
Cluster 0631adec0ef111b9: AsianPlaceWorld (1 instances)
Cluster 1e2711ea99da6604: WikiPageWiki_41 (2 instances)
Cluster 21a4ba9f7ca33937: WikiPageWiki_42 (11 instances)
Cluster b1545784a9ddeefa: CityWikiPage_3 (13 instances)
Cluster 440884ce5e2e7b38: WikiPageWiki_43 (3 instances)
Cluster 2b1e52b9a6ff7383: WikiPageDisambiguates (2 instances)
Cluster c41bd494553b8454: WikiPageWiki_44 (1 instances)
Cluster b37fd88048c90acc: WikiPageWiki_45 (8 instances)
Cluster d89c727234a58184: CityWikiPage_4 (6 instances)
Cluster 754d3d671e158cef: WikiPageWiki_46 (1 instances)
Cluster aa80c42dbdd224b7: LocationWikiPage_5 (2 instances)
Cluster bca04516bf025d94: PlaceWikiPage_2 (1 instances)
Cluster 934f51a7396588cc: PlaceWikiPage_3 (2 instances)
Cluster ac29aa7aeef59cbb: LocationWikiPage_6 (20 instances)
Cluster 853896b890fb5506: WikiPageWiki_47 (11 instances)
Cluster 8f7f9fce5ee682b9: SubdivisionWikiPage (1 instances)
Cluster eec2d916e8a85663: HeadquarterWikiPage_4 (1 instances)
Cluster 01632488b951b091: SpokenInWiki (1 instances)
Cluster 845ae8875c19edec: LocationWikiPage_7 (9 instances)
Cluster 28cbe6e205d0b77f: ParentOrganisation (1 instances)
Cluster f3d7ec75813fcea5: WikiPageWiki_48 (5 instances)
Cluster 008f661f9b852ba7: WikiPageWiki_49 (3 instances)
Cluster 8b8965e9872cac23: NamedAfterWiki (1 instances)
Cluster c8cc490ef7b832f2: Conceptc8cc49 (3 instances)
Cluster 51aca71b974bb0ef: WikiPageWiki_50 (2 instances)
Cluster b06d2c4304d2c032: RegionServedWiki (1 instances)
Cluster 70652cca5540c96f: HeadquarterWikiPage_5 (3 instances)
Cluster 479b99b0acd47963: RestingPlaceWiki (8 instances)
Cluster 9265794abbf62900: DeathPlaceMajor (2 instances)
Cluster c12fe6e365829a47: EmployerWikiPage_2 (1 instances)
Cluster d8fec6e81e4ce844: WikiPageWiki_51 (3 instances)
Cluster 695d8960d71a55eb: FoundingLocation (3 instances)
Cluster 101d98ac2e24ea37: ResidenceWikiPage_2 (17 instances)
Cluster 4a1f714f3f22a055: WikiPageWiki_52 (2 instances)
Cluster a3f8dc3b80a65587: CityFederalState (25 instances)
Cluster 5f9057ad0cc3d4ee: Concept5f9057 (1 instances)
Cluster b5feb3d261917801: WikiPageWiki_53 (2 instances)
Cluster 503bfaa05793f704: WikiPageWiki_54 (3 instances)
Cluster e510f58be7b2eb53: CityFederalState_2 (14 instances)
Cluster 78f990189d13a969: CityWikiPage_5 (2 instances)
Cluster 21cd121ccf7cf97c: WikiPageWiki_55 (4 instances)
Cluster cda9ae431ba3a0de: RouteStartWiki (1 instances)
Cluster 7d95d25fb24cf349: OriginWikiPage (2 instances)
Cluster 05f1af6804d83652: Concept05f1af (1 instances)
Cluster e1dfffdf52729843: Concepte1dfff (1 instances)
Cluster c516af0f8fa4be4d: DeathPlaceWiki_3 (2 instances)
Cluster 949f013ad7e5e405: Concept949f01 (10 instances)
Cluster 5836aeacbb0de117: Concept5836ae (3 instances)
Cluster 15f8297f7a0258bf: Concept15f829 (2 instances)
Cluster 707d428cdd7dd24e: Concept707d42 (1 instances)
Cluster 516190d2211e90c9: Concept516190 (1 instances)
Cluster 8c215f7fafae3b3a: Seat (5 instances)
Cluster d256fbc10348f7af: RestingPlaceWiki_2 (7 instances)
Cluster ac2eda051c2be235: WikiPageWiki_56 (8 instances)
Cluster 2ca2483f291aaf98: DestinationWikiPage (1 instances)
Cluster 51f9227fb2d8fcfc: AlmaMaterBirth (5 instances)
Cluster 575cf2e15fe1f1a4: CountryCountry (4 instances)
Cluster 7464a94572b0d1ba: WikiPageWiki_57 (1 instances)
Cluster 4196cc0984458a3c: WikiPageWiki_58 (1 instances)
Cluster c795ec2013ba6e70: MuseumWikiPage (1 instances)
Cluster 028334c0967b927b: PremierePlaceWiki (1 instances)
Cluster f1e03d58c8b936b0: LocationWikiPage_8 (10 instances)
Cluster 8b10e4e3ada5e4aa: MilitaryBranch (1 instances)
Cluster 39c719e894693ffb: InstitutionWikiPage (5 instances)
Cluster bc8ca13cc96f9600: MouthMountainMouth (1 instances)
Cluster 1622b1bb1a1fd504: CityWikiPage_6 (3 instances)
Cluster 9d04acaf4cba1a10: HeadquarterLocationWiki (1 instances)
Cluster 080fcc1349e8f1b0: WikiPageWiki_59 (1 instances)
Cluster b0ae85f15c4a059b: HeadquarterWikiPage_6 (2 instances)
Cluster 2f609e9ab58d1f7f: RouteStartWiki_2 (1 instances)
Cluster 23602a07910fac9f: HometownWikiPage_3 (1 instances)
Cluster 611b5f038fd18a5c: WikiPageWiki_60 (1 instances)
Cluster 94056f2143210e51: WikiPageWiki_61 (2 instances)
Cluster 79fd012a84405c52: WikiPageWiki_62 (1 instances)
Cluster aa0e0360b679ebb0: PlaceWikiPage_4 (1 instances)
Cluster abbe4015d96d189f: WikiPageWiki_63 (1 instances)
Cluster 0a530978b404b74c: WikiPageWiki_64 (1 instances)
Cluster 18e82c477df5758a: HeadquarterLocationWiki_2 (10 instances)
Cluster 421a243dd1cc83f4: HeadquarterLocationWiki_3 (4 instances)
Cluster 04c56cb3ce0ad47a: LocationCityWiki_2 (4 instances)
Cluster 76885a289e3f592a: PublisherWikiPage (1 instances)
Cluster 32353c6d46b04d19: WikiPageWiki_65 (2 instances)
Cluster 20a00317296269db: WikiPageWiki_66 (2 instances)
Cluster dfe3c103f70d3d29: LocationCountryHq (1 instances)
Cluster f2ab2f21d12effc7: AssemblyWikiPage (1 instances)
Cluster 5fe0615176187bb0: WikiPageWiki_67 (1 instances)
Cluster 5cc851583c730700: WikiPageWiki_68 (1 instances)
Cluster 77446655234179cb: WikiPageWiki_69 (1 instances)
Cluster 33daa5dae616f35d: CapitalWikiPage (4 instances)
Cluster 4550113671eff1cd: TargetAirport (1 instances)
Cluster 8619e99aa96d633e: LocationOwnerWiki (1 instances)
Cluster 5d0f380651bd2698: ConstituencyDistrict (3 instances)
Cluster c47917200114e993: BirthPlaceDeath_3 (1 instances)
Cluster 0e23f7bbf76a03fc: BirthPlaceDeath_4 (3 instances)
Cluster 967dd3cc6b46818b: BilledWikiPage (2 instances)
Cluster 0b337a3964ce5a59: RegionServedWiki_2 (1 instances)
Cluster 72c3689318095149: CountryObservedby (1 instances)
Cluster 537e98a7a6bfc998: Concept537e98 (1 instances)
Cluster 2af364a201619b50: Concept2af364 (1 instances)
Cluster b2296028fefd07cc: CapitalWikiPage_2 (3 instances)
Cluster c059edfd0842aa33: Conceptc059ed (1 instances)
Cluster ee85f199bfea4413: StadiumWikiPage (1 instances)
Cluster f71af887fe9ca331: WikiPageWiki_70 (1 instances)
Cluster 0e700a71b5c739a2: LocationPictureWiki (2 instances)
Cluster 398139ecf6e065ea: Concept398139 (1 instances)
Cluster 305f216a9f17cbf8: LocationNearestCity (1 instances)
Cluster 4e2ab33a79fd8cff: BirthPlaceOccupation (1 instances)
Cluster 54b7700bdd04811f: RestingPlaceWiki_3 (3 instances)
Cluster 5921eb9274a5123c: DeathPlaceResting (4 instances)
Cluster 058298989ea58c16: DeathPlaceSignificant (1 instances)
Cluster 6e67747497752dbf: BirthPlaceWiki_3 (1 instances)
Cluster 7571a0335466343a: TrainingWikiPage (2 instances)
Cluster 17b0610fe0682f36: CapitalLargestCity (1 instances)
Cluster 77cc0ffc94a150b7: NonFictionSubject (2 instances)
Cluster 26dd5b44e2a9df67: Concept26dd5b (1 instances)
Cluster 9b15e650cc1f1456: CityWikiPage_7 (1 instances)
Cluster 75f382a4df112f95: GarrisonWikiPage_2 (2 instances)
Cluster 5f1ac5903fc1ff79: WikiPageWiki_71 (1 instances)
Cluster 0ee45dfd15423792: WikiPageWiki_72 (1 instances)
Cluster 257633666e2a2d93: FoundedByHeadquarter (1 instances)
Cluster 07a32d5dea4db907: BirthPlaceHometown (1 instances)
Cluster 22e200e88301f1cd: Concept22e200 (1 instances)
Cluster 610700d135bf96e2: Foundation (1 instances)
Cluster c514e29e78e669fe: TrainingWikiPage_2 (2 instances)
Cluster 08be9020e5d0a3d5: WikiPageWiki_73 (1 instances)
Cluster 261df6f667a4c2b3: Concept261df6 (1 instances)
Cluster 900a6213383d199b: EducationWikiPage (3 instances)
Cluster 8cbb739e19b35d7b: AdministrativeDistrictCity (1 instances)
Cluster c6a97afa452c1d1c: BirthPlaceResidence (2 instances)
Cluster 21987f339ba0eeb0: WikiPageWiki_74 (1 instances)
Cluster 23aeb29a4219c95e: WikiPageWiki_75 (2 instances)
Cluster 4ddf14585e93fd7b: State (1 instances)
Cluster b81dfc0c47b4332c: AlmaMaterBirth_2 (2 instances)
Cluster a00aeab3d343bab5: WikiPageWiki_76 (1 instances)
Cluster 541b2e6940a32d78: WikiPageWiki_77 (1 instances)
Cluster d405b209be4d6270: WikiPageWiki_78 (2 instances)
Cluster 499c2838f8b245ea: Campus (1 instances)
Cluster f417fda4777461b1: PopulationPlaceWiki_3 (1 instances)
Cluster 6cb8cc460d543c11: RegionServedWiki_3 (1 instances)
Cluster eef0b3ac2e289189: RegionServedWiki_4 (1 instances)
Cluster 05e6c059ac123186: LocatedInArea_2 (1 instances)
Cluster 4cb0b4d3ca672036: WikiPageWiki_79 (1 instances)
Cluster 9e05de4c8aaf3f56: OwnerOwningCompany (1 instances)
Cluster 3bdc318eda76853c: BirthPlaceWiki_4 (1 instances)
Cluster e6894521a93be658: Concepte68945 (1 instances)
Cluster 1b18ebd3690ad3ea: Concept1b18eb (1 instances)
Cluster e7008dae7f68d04c: HometownWikiPage_4 (1 instances)
Cluster 6c8f4c870e1136a3: LocationOwnerWiki_2 (1 instances)
Cluster e1518a7d477cbe40: WikiPageWiki_80 (1 instances)
Cluster 04acbb9ae7d9542b: DeathPlaceWiki_4 (1 instances)
Cluster 11c7735c281e74fa: WikiPageWiki_81 (1 instances)
Cluster eb2b61fb2d6652d0: EducationWikiPage_2 (1 instances)
Cluster 57cce6e5043adc5b: LocationWikiPage_9 (1 instances)
Cluster 7580b47df40efbb2: PublisherWikiPage_2 (1 instances)
Cluster fd771ad235664c94: RecordedInWiki (1 instances)
Cluster ee7579be7c49a521: LocationWikiPage_10 (1 instances)
Cluster da1e40f2753cee72: WikiPageWiki_82 (1 instances)
Cluster 954bc72ad5c6b599: BirthPlaceClub (1 instances)
Cluster 17de1dc517434f81: WikiPageWiki_83 (1 instances)
Cluster 950a86fa6bb83e3b: BirthPlaceInstitution (1 instances)
Cluster 22eb80dc9751f2a4: DeathPlaceWiki_5 (1 instances)
Cluster 2e848c24e6f494c7: BirthPlaceDeath_5 (1 instances)
Cluster 0b1042effa904cd9: WikiPageWiki_84 (1 instances)
Cluster 543508fb871e9af3: WikiPageWiki_85 (1 instances)
Cluster 4866eb2d2fd49219: WikiPageWiki_86 (1 instances)
Cluster 7bca4e6b049f3415: WikiPageWiki_87 (1 instances)
Cluster e2f4cd33511c5545: OwnerWikiPage (1 instances)
Cluster e720cd2a91ca554e: WikiPageWiki_88 (1 instances)
Cluster d598565f8ab80d05: Today (1 instances)
Cluster 55a5fcb17c0fdbf9: WikiPageWiki_89 (1 instances)
Cluster bf72951e46f84fda: SubdivisionWikiPage_2 (1 instances)
Cluster 806989910fd154f6: WikiPageWiki_90 (1 instances)
Cluster 820572a04196b9bd: WikiPageWiki_91 (2 instances)
Cluster 9f1f46474a62fec9: BuilderWikiPage (1 instances)
Cluster 2c8c5f38af381ddc: Concept2c8c5f (52 instances)
Cluster 670e2fd792d82cbd: LocatedInArea_3 (1 instances)
Cluster 4602445aa35a8144: PremierePlaceWiki_2 (1 instances)
Cluster 1a558e78c8c7e7c3: CityOwnerWiki (1 instances)
Cluster 79b3f163c2d2dd1a: RecordedInWiki_2 (2 instances)
Cluster da47a5d65791b0ad: PopulationPlaceWiki_4 (1 instances)
Cluster 18f5ad059b7090cc: DivisionWikiPage (1 instances)
Cluster f606504ed2d53fe4: RegionWikiPage (1 instances)
Cluster 030ead2d98dd961e: Team (1 instances)
Cluster 82e2f6a19c9bd91a: OperatorOwnerWiki (1 instances)
Cluster bdafc46b9f2820e3: WikiPageWiki_92 (1 instances)
Cluster 10eb6ea8ef381b66: HeadquarterWikiPage_7 (1 instances)
Cluster ac8828ee6479dbd2: StateWikiPage (1 instances)
Cluster 50716343a8335958: Concept507163 (1 instances)
Cluster 23fde4c4b70d6b9a: Concept23fde4 (1 instances)
Cluster 355f6a6e8c7e6941: Concept355f6a (2 instances)
Cluster 7ac0468ee6e353e5: Concept7ac046 (3 instances)
Cluster d79ee7ce188a90a3: Conceptd79ee7 (1 instances)
Cluster eb540198970cd56a: Concepteb5401 (1 instances)
Cluster b63f1d80a82a9a37: Conceptb63f1d (1 instances)
Running mine_taxonomy
Taxonomic candidate pairs: 14406
Running mine_roles_and_restrictions
abox2tbox: ValueError: Property-chain join exceeds MAX_JOIN_EDGES; output preserved

```

### GeoNames Bangladesh

```text
Running initialize_transport
Tier=statistical, Decision=clef-flash:latest
Running parse_input
Loaded 279 triples; training=277, subjects=10, untyped=9
Running cluster_signatures
Consolidated clusters: 7
Running detect_namespace
Detected Namespace: http://www.geonames.org/ontology#
Running name_concepts
Cluster 4e865ea4ff57ace7: Concept4e865e (2 instances)
Cluster 10b92c1e493b3b00: Concept10b92c (2 instances)
Cluster 9b58269317f7b5ab: Concept9b5826 (1 instances)
Cluster 9b0a6c60c74da6d6: Concept9b0a6c (1 instances)
Cluster f2772f1d807eea61: Conceptf2772f (1 instances)
Cluster 109bea4def48627f: Concept109bea (1 instances)
Cluster 006c815d4d1e7602: Concept006c81 (1 instances)
Running mine_taxonomy
Taxonomic candidate pairs: 0
Running mine_roles_and_restrictions
Scored restriction candidates: 0, property chains: 0
Running adjudicate_taxonomy
Evidence-admitted subclass hypotheses: 0
Running assess_disjointness
Withheld 0 disjointness proposals: absence is not negation
Running adjudicate_roles
Evidence decisions: {}
Running repair_taxonomy
Greedy repair removed 0 edges; reduced taxonomy has 0 edges
Running repair_consistency
Disjoint conflicts removed=0, remaining=0; irregular chains rejected=0
Running infer_domains_ranges
Running build_ontology
Running validate_and_export
abox2tbox: RuntimeError: Complete export validation failed (TBox + training ABox): Java error message is:
Exception in thread "main" org.semanticweb.HermiT.datatypes.UnsupportedDatatypeException: Literals can only use the datatypes from the OWL 2 datatype map, see
http://www.w3.org/TR/owl2-syntax/#Datatype_Maps.
The datatype 'https://www.w3.org/2001/XMLSchema#date' is not part of the OWL 2 datatype map and
HermiT cannot parse this literal.
	at org.semanticweb.HermiT.datatypes.DatatypeRegistry.parseLiteral(Unknown Source)
	at org.semanticweb.HermiT.model.Constant.create(Unknown Source)
	at org.semanticweb.HermiT.structural.OWLClausification$DataRangeConverter.visit(Unknown Source)
	at uk.ac.manchester.cs.owl.owlapi.OWLLiteralImplNoCompression.accept(OWLLiteralImplNoCompression.java:281)
	at org.semanticweb.HermiT.structural.OWLClausification$FactClausifier.visit(Unknown Source)
	at uk.ac.manchester.cs.owl.owlapi.OWLDataPropertyAssertionAxiomImpl.accept(OWLDataPropertyAssertionAxiomImpl.java:97)
	at org.semanticweb.HermiT.structural.OWLClausification.clausify(Unknown Source)
	at org.semanticweb.HermiT.structural.OWLClausification.preprocessAndClausify(Unknown Source)
	at org.semanticweb.HermiT.Reasoner.loadOntology(Reasoner.java:117)
	at org.semanticweb.HermiT.Reasoner.<init>(Reasoner.java:108)
	at org.semanticweb.HermiT.Reasoner.<init>(Reasoner.java:86)
	at org.semanticweb.HermiT.cli.CommandLine.main(CommandLine.java:830)


```

### Wikidata Douglas Adams

```text
rn.abox2tbox:inferred:Concept174f36]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P9918 belongs to more than one entity types: [urn.abox2tbox:inferred:Concepta8dbda, owl.DatatypeProperty]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P3136 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Conceptb4187d]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P3136 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept152990]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P1810 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept152990]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P1149 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Conceptb4187d]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P1149 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P1149 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept152990]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P1810 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/direct/P1810 belongs to more than one entity types: [urn.abox2tbox:inferred:Concept174f36, owl.DatatypeProperty]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P1810 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Conceptb4187d]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/direct/P1284 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept174f36]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P11180 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept152990]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P11180 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P11180 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Conceptb4187d]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/direct/P1280 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept174f36]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P2093 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Conceptb4187d]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P2093 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept152990]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P1284 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P1284 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Conceptb4187d]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/direct/P9995 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept174f36]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P9995 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Conceptb4187d]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P9995 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P10135 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P577 belongs to more than one entity types: [urn.abox2tbox:inferred:Conceptb4187d, owl.DatatypeProperty]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P577 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept152990]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P1417 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept152990]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P1417 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P1417 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Conceptb4187d]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/direct/P1559 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept174f36]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P1559 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept152990]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P1559 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P1559 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Conceptb4187d]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P5034 belongs to more than one entity types: [urn.abox2tbox:inferred:Concept152990, owl.DatatypeProperty]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P14640 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P14640 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept152990]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P5337 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/direct/P5337 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept174f36]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P5337 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept152990]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P7071 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/direct/P7071 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept174f36]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/direct/P648 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept174f36]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P648 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept152990]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P648 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Conceptb4187d]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P648 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P10135 belongs to more than one entity types: [urn.abox2tbox:inferred:Conceptb4187d, owl.DatatypeProperty]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/reference/P1280 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept152990]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P1280 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concepta8dbda]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P1280 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Conceptb4187d]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/qualifier/P5034 belongs to more than one entity types: [urn.abox2tbox:inferred:Concepta8dbda, owl.DatatypeProperty]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/direct/P5034 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Concept174f36]; I'm trying to fix it...
* Owlready2 * WARNING: DataProperty http://www.wikidata.org/prop/statement/P5034 belongs to more than one entity types: [owl.DatatypeProperty, urn.abox2tbox:inferred:Conceptb4187d]; I'm trying to fix it...
abox2tbox: RuntimeError: Complete export validation failed (TBox + training ABox): Java error message is:
Exception in thread "main" org.semanticweb.HermiT.datatypes.UnsupportedDatatypeException: Literals can only use the datatypes from the OWL 2 datatype map, see
http://www.w3.org/TR/owl2-syntax/#Datatype_Maps.
The datatype 'http://www.opengis.net/ont/geosparql#wktLiteral' is not part of the OWL 2 datatype map and
HermiT cannot parse this literal.
	at org.semanticweb.HermiT.datatypes.DatatypeRegistry.parseLiteral(Unknown Source)
	at org.semanticweb.HermiT.model.Constant.create(Unknown Source)
	at org.semanticweb.HermiT.structural.OWLClausification$DataRangeConverter.visit(Unknown Source)
	at uk.ac.manchester.cs.owl.owlapi.OWLLiteralImplNoCompression.accept(OWLLiteralImplNoCompression.java:281)
	at org.semanticweb.HermiT.structural.OWLClausification$FactClausifier.visit(Unknown Source)
	at uk.ac.manchester.cs.owl.owlapi.OWLDataPropertyAssertionAxiomImpl.accept(OWLDataPropertyAssertionAxiomImpl.java:97)
	at org.semanticweb.HermiT.structural.OWLClausification.clausify(Unknown Source)
	at org.semanticweb.HermiT.structural.OWLClausification.preprocessAndClausify(Unknown Source)
	at org.semanticweb.HermiT.Reasoner.loadOntology(Reasoner.java:117)
	at org.semanticweb.HermiT.Reasoner.<init>(Reasoner.java:108)
	at org.semanticweb.HermiT.Reasoner.<init>(Reasoner.java:86)
	at org.semanticweb.HermiT.cli.CommandLine.main(CommandLine.java:830)


```

### Nobel Prize Wilhelm Conrad Roentgen

```text
ValueError: Publisher returned HTML rather than RDF (text/html; https://data.nobelprize.org/resource/laureate/1)
```

## Scope

This is a small, deliberately varied convenience sample. Resource descriptions
and standards fixtures are usually too small or too sparsely typed to establish
universal axioms. Missing hold-out denominators and zero recovery are preserved.
Download failures are distinct from pipeline failures; no source was cleaned to pass.
An accepted count of zero means vocabulary-only output, even when validation passed.
Acquisition URLs, timestamps, sizes, and SHA-256 hashes are recorded in report.json.
