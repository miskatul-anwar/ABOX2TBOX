"""Vocabulary and descriptive mining helpers; none are calibrated truth probabilities."""

from typing import Any, Callable
import math
import difflib
import os
from rdflib.namespace import RDF, RDFS, OWL, XSD

standard_vocabulary_prefixes: tuple[str, ...] = (
    "http://www.w3.org/",
    "http://purl.org/dc/",
    "http://xmlns.com/",
)
meta_vocabulary_prefixes: tuple[str, ...] = (str(RDF), str(RDFS), str(OWL), str(XSD))
is_meta_uri: Callable[[str], bool] = lambda uri: any(
    (uri.startswith(p) for p in meta_vocabulary_prefixes)
)
local_name: Callable[[str], str] = lambda uri: (
    uri.rsplit("#", 1)[-1]
    if "#" in uri
    else uri.rsplit("/", 1)[-1]
    if "/" in uri
    else uri.rsplit(":", 1)[-1]
)
rdf_type_str: str = str(RDF.type)
wilson_lower: Callable[[int, int, float], float] = lambda k, n, z=1.28: (
    0.0
    if n <= 0
    else float(
        min(
            1.0,
            max(
                0.0,
                (
                    k / n
                    + z**2 / (2 * n)
                    - z
                    * math.sqrt(max(0.0, k / n * (1.0 - k / n) / n + z**2 / (4 * n**2)))
                )
                / (1.0 + z**2 / n),
            ),
        )
    )
)
celoe_heuristic: Callable[[float, float, int, float, float], float] = (
    lambda q_parent, q_ref, length, lam=0.2, beta=0.03: float(
        q_ref + lam * (q_ref - q_parent) - beta * float(length)
    )
)
lexical_similarity: Callable[[str, str], float] = lambda s1, s2: float(
    min(
        1.0,
        max(
            0.0,
            difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
            + min(4, len(os.path.commonprefix([s1.lower(), s2.lower()])))
            * 0.1
            * (1.0 - difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()),
        ),
    )
)
inferred_namespace = "urn:abox2tbox:inferred:"
