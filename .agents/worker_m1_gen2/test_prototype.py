import rdflib
from rdflib import RDF, RDFS, OWL, Namespace, Literal, URIRef
import networkx as nx
import sqlite3
import re
from collections import defaultdict

def test_domain(turtle_path, ns_str):
    g = rdflib.Graph()
    g.parse(turtle_path, format="turtle")
    print(f"Loaded {len(g)} triples from {turtle_path}")
    
    # 1. Classes
    classes = set(g.objects(None, RDF.type))
    print(f"Explicit classes: {len(classes)}")
    
    # 2. Untyped entities
    subjects = set(g.subjects())
    typed = set(g.subjects(RDF.type, None))
    untyped = subjects - typed
    print(f"Total subjects: {len(subjects)}, Untyped subjects: {len(untyped)}")
    
    # 3. Characteristic sets
    cs_map = defaultdict(list)
    for u in untyped:
        out_preds = sorted(set(g.predicates(u, None)))
        in_preds = sorted(set(g.predicates(None, u)))
        sig = (tuple(str(p) for p in out_preds), tuple(str(p) for p in in_preds))
        cs_map[sig].append(u)
    print(f"Untyped clusters: {len(cs_map)}")
    for sig, ents in cs_map.items():
        print(f"  Cluster of {len(ents)} entities: out={len(sig[0])}, in={len(sig[1])}")
        
    return len(g), len(classes), len(untyped), len(cs_map)

print("Test prototype helper ready.")
