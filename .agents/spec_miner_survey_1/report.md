# Specification Mining & Formal Requirements Report
# Neuro-Symbolic ABox-to-TBox Ontology Induction Notebook (`ABox2TBox.ipynb`)

**Document Version:** 1.0.0  
**Author:** Specification Investigator (`spec_miner_survey_1`)  
**Parent Orchestrator:** `0a10e674-c27e-47e5-ac70-e7b05332cf40`  
**Authoritative Source Documents:**
1. `/home/miskat/ABOX2TBOX/software_requirements_specification_abox_to_tbox_induction_notebook.md` (Version 1.0.0)
2. `/home/miskat/ABOX2TBOX/.agents/ORIGINAL_REQUEST.md` (Dated 2026-10-14T17:32:21Z)

---

## 1. Executive Summary & System Mission

The objective of `ABox2TBox.ipynb` is to implement a research-grade, reproducible, neuro-symbolic pipeline that induces a formal, logically sound OWL 2 / RDFS Terminological Box (`TBox.ttl`) from an arbitrary instance-level Assertion Box (`ABox.ttl`).

The central engineering challenge is the **Context Window Dilemma**: enterprise knowledge bases contain millions or billions of triples, while Large Language Models (LLMs) suffer from context limits, quadratic attention scaling, and syntactic hallucinations. `ABox2TBox.ipynb` resolves this via a **Map-Compress-Adjudicate-Repair** architecture:
1. **Map & Compress:** Deterministically compress unbounded ABox instance triples into structural equivalence classes (*Characteristic Sets*) using hashing (`xxhash64`) and streaming graph indexing (`rdflib`, `sqlite3`/`duckdb`). Downstream LLM prompt payloads scale as $O(1)$ with respect to KB size, strictly bounded to $\le 1,500$ tokens.
2. **Adjudicate:** Decompose semantic tasks between two ultra-lightweight co-resident models:
   - `tinyllama:latest` ($1.1\text{B}$ params via `/api/generate`): Open-vocabulary lexical abstraction, synthesizing candidate class identifiers (`PascalCase`) and natural language glosses (`rdfs:comment`) for untyped entity clusters.
   - `tev1:0.8b` ($752\text{M}$ params via `/v1/systemone`): Calibrated probabilistic decision-making (`noul`, `choice`, `score`) to verify formal axioms (`rdfs:subClassOf`, `owl:disjointWith`, `rdfs:domain`, `rdfs:range`, property characteristics).
3. **Repair & Materialize:** Apply graph-theoretic repair algorithms in `networkx` (Tarjan's SCC for equivalence collapsing, Minimum Feedback Arc Set for strict DAG cycle elimination, transitive reduction for minimal Hasse diagram, and reachability pruning for disjointness consistency) and serialize the clean schema to `TBox.ttl` with optional W3C PROV-O reification annotations.

---

## 2. Architecture & Strict Division of Labor

The pipeline enforces a strict separation of concerns across components to prevent semantic hallucination and memory exhaustion:

| Subsystem | Tool / Model | Permitted Operations | Prohibited Operations |
| :--- | :--- | :--- | :--- |
| **Ingestion & Indexing** | `rdflib` + Out-of-Core Store (`sqlite3` / `duckdb`) | Streaming chunk parse of `ABox.ttl`, URI namespace/local name normalization, frequency aggregation, Characteristic Set hashing. | Loading raw multi-gigabyte graphs into unindexed Python lists or dumping full graphs into LLM prompts. |
| **Graph Mining & Topology** | `networkx` | Directed graph construction, co-occurrence/inclusion statistics, Jaccard similarity, Tarjan's SCC, Hasse transitive reduction, Minimum Feedback Arc Set, disjointness reachability conflict detection. | Semantic disambiguation of polysemous URI labels or free-form text reasoning. |
| **Lexical Concept Synthesis** | `tinyllama:latest` (`/api/generate`) | Generating concise hypernym labels (`PascalCase` class identifiers) and 1-sentence glosses (`rdfs:comment`) for untyped Characteristic Set clusters. | Deciding formal logical axioms, generating raw Turtle syntax directly to `TBox.ttl`, or processing $>512$ tokens per call. |
| **Axiom Adjudication** | `tev1:0.8b` (`/v1/systemone`) | Evaluating binary (`noul`), multi-way taxonomic (`choice`), and rubric quality (`score`) queries over compact structural profiles. | Free-form text generation or evaluating $>24$ options in a single `choice` head. |
| **Evaluation & Visualization** | `pandas`, `matplotlib`, `networkx` | Computing OntoQA metrics ($RR, IR, CCR$), calibration error (ECE), token telemetry histograms, hierarchy DAG visualization. | Altering ontology axioms during the evaluation phase. |

---

## 3. Detailed Specification of the 8 Notebook Sections

The notebook `ABox2TBox.ipynb` must be organized into 8 modular, sequentially executable sections:

### Section 0: Environment Setup, Hyperparameters & Reproducibility Seeds
- **Purpose:** Configure deterministic execution, API connection parameters, token limits, and statistical thresholds.
- **Inputs:** Runtime constants, environment variables, random seeds.
- **Key Parameters & Defaults:**
  - Random seeds: `SEED = 42` (applied to `random`, `numpy`, hash seeds).
  - Ollama Base URL: `OLLAMA_BASE_URL = "http://localhost:11434"`.
  - Model tags: `MODEL_CONCEPT = "tinyllama:latest"`, `MODEL_ADJUDICATOR = "tev1:0.8b"`.
  - Token Limits: $C_{\max} = 1500$ (hard ceiling $2050$ tokens for `/v1/systemone`); Micro-prompt $\le 400$ input tokens, `num_predict: 64` output tokens for `tinyllama:latest`.
  - Statistical Pre-filtering Thresholds: $\tau_{\text{sub}} = 0.15$ (min conditional subsumption confidence), $\tau_{\text{sig}} = 0.40$ (min signature Jaccard similarity), $\epsilon_{\text{disj}} = 0.005$ (max overlap ratio for candidate disjointness).
  - Decision Gate Thresholds: $\theta_{\text{prob}} = 0.70$, $\theta_{\text{conf}} = 0.65$, $\theta_{\text{score}} = 1.80$, $\theta_{\text{noul}} = 0.80$, deadband $\delta_{\text{deadband}} = 0.15$.
  - Tournament Branching Factor: $b = 15$ ($15$ candidates $+ 1$ `"owl:Thing"` fallback $= 16$ choice keys).
  - Export Mode: `EXPORT_STRICT_OWL2_DL = False` (default: include research PROV-O annotations).
- **Outputs:** Global configuration dictionary, validated client session handles, initialized pseudo-random number generators.

### Section 1: Scalable ABox Ingestion & Characteristic Set Profiling (`rdflib`, relational index)
- **Purpose:** Ingest `ABox.ttl` in bounded memory, segregate instance data from pre-existing schema triples, and compute Characteristic Sets ($CS$) and property frequency tables.
- **Inputs:** `ABox.ttl` filepath.
- **Operations:**
  1. Chunked streaming parse via `rdflib` into disk-backed `sqlite3` or `duckdb` tables: `triples(subject, predicate, object, is_literal)`.
  2. URI normalization: Split URI into `(namespace, local_name)`; convert `camelCase` and `snake_case` tokens into clean lexical terms.
  3. Characteristic Set computation for every entity $v \in \mathcal{A}$ lacking `rdf:type`:
     $$CS(v) = \{p^+ \mid (v, p, o) \in \mathcal{A}\} \cup \{p^- \mid (s, p, v) \in \mathcal{A}\} \cup \{\tau \mid (v, \text{rdf:type}, \tau) \in \mathcal{A}\}$$
  4. 64-bit signature hashing:
     $$h(v) = \text{xxhash64}\left(\text{sort}(\{p^+\}) \parallel \text{sort}(\{p^-\})\right)$$
  5. Cluster untyped entities into Equivalence Clusters $K_i$ where signature Jaccard similarity $\ge 0.85$ or hashes match.
- **Outputs:** Relational triple tables, Characteristic Set catalog, untyped cluster prototypes $K_i$, predicate incoming/outgoing frequency tables.

### Section 2: Open-Vocabulary Concept Induction for Untyped Entities (`tinyllama:latest`)
- **Purpose:** Propose ontological class names and definitions for untyped entity clusters where explicit classes are missing or opaque.
- **Inputs:** Top $k=5$ representative instance local names, top $k=5$ outgoing predicates, top $k=5$ incoming predicates, sample literal datatypes per cluster $K_i$.
- **Operations:**
  1. Micro-prompt construction strictly $\le 400$ input tokens (target $\le 350$).
  2. Dispatch to `/api/generate` (`model: "tinyllama:latest"`, `stream: false`, `format: "json"`, `options: {"num_predict": 64, "temperature": 0.1}`).
  3. Output JSON Schema: `{"class_name": "PascalCaseIdentifier", "gloss": "Concise 1-sentence ontological definition."}`.
  4. Regex sanitization: `^[A-Z][a-zA-Z0-9]+$`.
  5. Fallback Naming: If model is offline, times out, or output violates regex, compute highest-TF-IDF predicate nouns and synthesize `PascalCase` class name (e.g. `CourseInstructor`) and template gloss.
- **Outputs:** Mapping from untyped cluster ID $K_i$ to synthesized class URI (`:ClassName`), `rdfs:label`, and `rdfs:comment`.

### Section 3: Candidate Axiom Generation & Graph Pruning (`networkx`)
- **Purpose:** Construct candidate taxonomy pairs and property profiles while pre-filtering statistically improbable assertions before neural adjudication.
- **Inputs:** Explicit classes, synthesized classes, instance extensions $I(C)$, property assertions.
- **Operations:**
  1. Compute empirical conditional inclusion probability and Jaccard similarity for all class pairs:
     $$\text{conf}(C_i \sqsubseteq C_j) = \frac{|I(C_i) \cap I(C_j)|}{|I(C_i)|}, \quad \text{Jacc}(C_i, C_j) = \frac{|I(C_i) \cap I(C_j)|}{|I(C_i) \cup I(C_j)|}$$
     Queue $(C_i, C_j)$ for taxonomic adjudication if $\text{conf}(C_i \sqsubseteq C_j) \ge 0.15$ OR $\text{Jacc}(C_i, C_j) \ge 0.40$.
  2. Disjointness Candidate Mining: Queue pairs sharing common superclasses or overlapping domains where:
     $$\frac{|I(C_i) \cap I(C_j)|}{\min(|I(C_i)|, |I(C_j)|)} \le \epsilon_{\text{disj}} = 0.005$$
  3. Property Empirical Metrics Calculation:
     - Empirical Transitivity: $\rho_{\text{trans}}(P) = \frac{|\{(x,y,z) \mid (x,P,y) \land (y,P,z) \land (x,P,z)\}|}{|\{(x,y,z) \mid (x,P,y) \land (y,P,z)\}|}$
     - Empirical Symmetry: $\rho_{\text{sym}}(P) = \frac{|\{(x,y) \mid (x,P,y) \land (y,P,x)\}|}{|\{(x,y) \mid (x,P,y)\}|}$
     - Empirical Functionality: $\rho_{\text{func}}(P) = \frac{|\{x \mid \text{out\_deg}_P(x) = 1\}|}{|\{x \mid \text{out\_deg}_P(x) \ge 1\}|}$
  4. Datatype vs. Object Property Classification: Inspect object node types. For literal objects, map `rdfs:range` to XSD datatypes (`xsd:string`, `xsd:integer`, `xsd:decimal`, `xsd:dateTime`, `xsd:boolean`).
- **Outputs:** Pruned candidate subsumption pair list, candidate disjointness pair list, property profile dictionary with empirical ratios and domain/range candidate distributions.

### Section 4: Hierarchical Tournament & Batch Axiom Verification (`tev1:0.8b` via `/v1/systemone`)
- **Purpose:** Adjudicate candidate axioms using single-pass probabilistic decisions with context bounds and tournament reduction.
- **Inputs:** Candidate axiom pool, property empirical profiles, structural summaries.
- **Operations:**
  1. Payload batch packaging: $\le 32$ questions per batch, $\le 16$ options per choice head, total token payload bounded strictly to $\le 1,500$ tokens.
  2. 5-way Taxonomic `choice`:
     - Options: `c1_sub_c2` ($C_1 \sqsubseteq C_2$), `c2_sub_c1` ($C_2 \sqsubseteq C_1$), `equivalent` ($C_1 \equiv C_2$), `disjoint` ($C_1 \sqcap C_2 \sqsubseteq \bot$), `none`.
  3. Parallel `noul` property verification:
     - Questions for `owl:TransitiveProperty`, `owl:SymmetricProperty`, `owl:AsymmetricProperty`, `owl:FunctionalProperty`, `owl:InverseFunctionalProperty`.
  4. 4-level `score` rubric ($0$ to $3$) measuring ontological rigor vs accidental data artifact.
  5. $k$-ary Tournament Tree for high-cardinality ($N > 15$) domain/range candidate classes:
     - Chunk size $b = 15$ candidates $+ 1$ `"owl:Thing"` fallback $= 16$ keys.
     - Multi-round elimination in $\lceil \log_{15}(N) \rceil$ passes until the winning domain/range emerges.
  6. Decision Acceptance Gate filtering:
     $$\begin{cases}
     P(\text{choice} = k^*) \ge 0.70 \land \text{confidence} \ge 0.65 \land \text{score} \ge 1.80 & (\texttt{choice}) \\
     \text{noul} \ge 0.80 \land |\text{noul} - 0.5| \ge 0.15 & (\texttt{noul})
     \end{cases}$$
  7. Resilient Heuristic Simulation Fallback: If `/v1/systemone` is unavailable, execute deterministic statistical rule simulation.
- **Outputs:** Adjudicated axiom pool with calibrated edge weights $w(u,v) = P(u \sqsubseteq v) \cdot \text{confidence}$, confidence metrics, and rejection audit log.

### Section 5: Graph-Theoretic TBox Repair & Consistency Enforcement (`networkx`)
- **Purpose:** Eliminate cycles, remove redundant edges, and resolve logical conflicts to ensure OWL 2 DL consistency and strict DAG hierarchy.
- **Inputs:** Adjudicated candidate axioms, edge scores $w(u,v)$.
- **Operations:**
  1. Directed subsumption graph construction $G_{\text{sub}} = (V_C, E_{\text{sub}})$.
  2. Tarjan's Strongly Connected Components (SCC):
     - For any SCC where mutual edges have high symmetric probability ($\min(w(u,v), w(v,u)) \ge 0.80$), collapse the nodes into an `owl:equivalentClass` set.
  3. Minimum Feedback Arc Set (MFAS):
     - For any remaining cycle, remove the minimum-weight edge(s) solving MFAS, ensuring $G_{\text{sub}}$ is a strict Directed Acyclic Graph (DAG) with $0$ directed cycles.
  4. Transitive Reduction (Hasse Diagram):
     - Compute `nx.transitive_reduction(G_sub)` to remove shortcut edges $(u, w)$ when directed path $u \rightarrow^+ v \rightarrow^+ w$ exists.
  5. Disjointness-Subsumption Consistency Check:
     - For each disjointness axiom $A \sqcap B \sqsubseteq \bot$, check if $\text{descendants}(A) \cap \text{descendants}(B) \ne \emptyset$.
     - If a shared descendant $X$ exists, compare the log-odds/confidence of the disjointness axiom against the weakest subsumption edge on the path to $X$, and prune the lower-confidence edge.
  6. Property Characteristic Mutex Check:
     - Enforce that no property is both `Symmetric` and `Asymmetric`, or `Transitive` and `Asymmetric`. Prune lower-confidence assertion.
- **Outputs:** Consistent, minimal subsumption DAG ($G_{\text{clean}}$), consistent disjointness list, validated property declarations.

### Section 6: `TBox.ttl` Materialization with W3C PROV-O Metadata (`rdflib`)
- **Purpose:** Export the repaired ontology into valid Turtle syntax, optionally injecting research provenance annotations.
- **Inputs:** Clean class graph, properties, disjointness pairs, reification telemetry, `EXPORT_STRICT_OWL2_DL` flag.
- **Operations:**
  1. Create `rdflib.Graph` and bind standard prefixes (`rdf`, `rdfs`, `owl`, `xsd`, `prov`, default `:`).
  2. Emit ontology header: `:Ontology a owl:Ontology`.
  3. Emit class declarations (`owl:Class`, `rdfs:label`, `rdfs:comment`).
  4. Emit subsumption axioms (`rdfs:subClassOf`) from the transitive reduction DAG.
  5. Emit equivalence sets (`owl:equivalentClass`) and disjointness pairs (`owl:disjointWith`).
  6. Emit property definitions (`owl:ObjectProperty`, `owl:DatatypeProperty`, `rdfs:domain`, `rdfs:range`, characteristics).
  7. Provenance Injection (when `EXPORT_STRICT_OWL2_DL = False`):
     - Reify axioms using `owl:Axiom` with `owl:annotatedSource`, `owl:annotatedProperty`, `owl:annotatedTarget`.
     - Annotate with `:decisionProbability` (`xsd:decimal`), `:decisionConfidence` (`xsd:decimal`), `:aboxSupportCount` (`xsd:integer`), and `prov:wasAttributedTo` (`"ollama:tev1:0.8b"` or `"ollama:tinyllama:latest"`).
  8. Serialize to `TBox.ttl`.
- **Outputs:** Valid, syntax-checked `TBox.ttl` file.

### Section 7: Research Evaluation, Ablation & Calibration Diagnostics
- **Purpose:** Compute quantitative OntoQA schema metrics, logical soundness checks, calibration diagnostics, and visualize the induced class hierarchy.
- **Inputs:** Ingested `ABox.ttl`, generated `TBox.ttl`, adjudication telemetry logs, graph repair logs.
- **Operations:**
  1. OntoQA Structural Metrics:
     - Relationship Richness ($RR$):
       $$RR = \frac{|P_{\text{obj}} \cup P_{\text{data}}|}{|P_{\text{obj}} \cup P_{\text{data}}| + |E_{\text{subClassOf}}|}$$
     - Inheritance Richness ($IR$):
       $$IR = \frac{\sum_{C_i \in \mathcal{C}} |\text{children}(C_i)|}{|\mathcal{C}|}$$
     - Class Coverage Ratio ($CCR$):
       $$CCR = \frac{|\{e \in \text{Entities}(\mathcal{A}) \mid \exists C \in \mathcal{T}: e \in I(C)\}|}{|\text{Entities}(\mathcal{A})|}$$
  2. Deductive Soundness Metrics:
     - Cycle Elimination Count (number of cyclic edges repaired).
     - Disjointness Violation Count ($DVC$):
       $$DVC = |\{e \in \text{Entities}(\mathcal{A}) \mid \exists (C_1, C_2) \in \text{DisjointPairs}: e \in I(C_1) \land e \in I(C_2)\}|$$
       Verify $DVC_{\text{post}} = 0$.
  3. Model Telemetry & Token Bounds:
     - Plot histograms of decision probabilities, confidence scores, and token lengths across all API calls.
     - Verify $100\%$ of payloads $\le 1,500$ tokens.
  4. Hierarchy Visualization:
     - Render Matplotlib tree/DAG diagram of the induced class taxonomy.
- **Outputs:** Tabular summary of OntoQA metrics, calibration histograms, token ceiling audit plot, rendered class hierarchy graph.

---

## 4. Formal Mathematical Definitions and Invariants

### 4.1 Characteristic Sets & Predicate Hashing
For any node $v \in \mathcal{A}$:
$$CS(v) = \{p^+ \mid (v, p, o) \in \mathcal{A}\} \cup \{p^- \mid (s, p, v) \in \mathcal{A}\} \cup \{\tau \mid (v, \text{rdf:type}, \tau) \in \mathcal{A}\}$$
The 64-bit compact signature hash is defined as:
$$h(v) = \text{xxhash64}\left(\text{sort}(\{p^+ \mid (v,p,o) \in \mathcal{A}\}) \parallel \text{sort}(\{p^- \mid (s,p,v) \in \mathcal{A}\})\right)$$
Equivalence cluster similarity between two nodes $u, v$:
$$\text{Jacc}_{\text{sig}}(u, v) = \frac{|\text{sig}(u) \cap \text{sig}(v)|}{|\text{sig}(u) \cup \text{sig}(v)|}$$
Clustering invariant: Nodes $u, v$ belong to cluster $K_i$ if $h(u) = h(v)$ or $\text{Jacc}_{\text{sig}}(u, v) \ge 0.85$.

### 4.2 Statistical Inclusions & Overlaps
For classes $C_i, C_j$ with instance sets $I(C_i), I(C_j)$:
$$\text{conf}(C_i \sqsubseteq C_j) = \frac{|I(C_i) \cap I(C_j)|}{|I(C_i)|}$$
$$\text{Jacc}(C_i, C_j) = \frac{|I(C_i) \cap I(C_j)|}{|I(C_i) \cup I(C_j)|}$$
Disjointness candidate criterion:
$$\frac{|I(C_i) \cap I(C_j)|}{\min(|I(C_i)|, |I(C_j)|)} \le \epsilon_{\text{disj}} = 0.005$$

### 4.3 Property Characteristics
For each object property $P \subseteq \mathcal{A}$:
- **Transitivity Ratio:**
  $$\rho_{\text{trans}}(P) = \frac{|\{(x,y,z) \mid (x,P,y) \in \mathcal{A} \land (y,P,z) \in \mathcal{A} \land (x,P,z) \in \mathcal{A}\}|}{|\{(x,y,z) \mid (x,P,y) \in \mathcal{A} \land (y,P,z) \in \mathcal{A}\}|}$$
- **Symmetry Ratio:**
  $$\rho_{\text{sym}}(P) = \frac{|\{(x,y) \mid (x,P,y) \in \mathcal{A} \land (y,P,x) \in \mathcal{A}\}|}{|\{(x,y) \mid (x,P,y) \in \mathcal{A}\}|}$$
- **Functionality Ratio:**
  $$\rho_{\text{func}}(P) = \frac{|\{x \mid \text{out\_deg}_P(x) = 1\}|}{|\{x \mid \text{out\_deg}_P(x) \ge 1\}|}$$
*(Note: If denominator $= 0$, empirical ratio defaults to $0.0$.)*

### 4.4 Prompt Scalability Invariant ($O(1)$)
$$\sup_{|\mathcal{A}| \rightarrow \infty} L(\text{payload}) \le C_{\max} = 1,500 \text{ tokens} \quad (\text{hard ceiling: } 2,050 \text{ tokens})$$

---

## 5. API Contracts & Model Integration

### 5.1 `tinyllama:latest` Micro-Prompt Specification (`/api/generate`)
- **Endpoint:** `POST /api/generate`
- **Request Payload Schema:**
  ```json
  {
    "model": "tinyllama:latest",
    "prompt": "You are an ontology engineer. Given the following entity profile, propose a concise PascalCase class name and a 1-sentence gloss.\n\nSample instance names: [Alice, Bob, Carol]\nOutgoing properties: [teachesCourse, hasOffice, advisesStudent]\nIncoming properties: [directedBy, departmentMember]\nDatatypes: [xsd:string, xsd:integer]\n\nRespond ONLY with valid JSON matching:\n{\"class_name\": \"PascalCaseIdentifier\", \"gloss\": \"Description.\"}",
    "stream": false,
    "format": "json",
    "options": {
      "num_predict": 64,
      "temperature": 0.1
    }
  }
  ```
- **Token Bounds:** Input tokens $\le 400$, Output tokens $\le 64$.
- **Validation Regex:** `^[A-Z][a-zA-Z0-9]+$`
- **Sanitization & Deterministic Fallback:**
  - Strip surrounding whitespace and markdown code fences (````json ... ````).
  - Parse JSON and extract `class_name` and `gloss`.
  - If JSON is malformed, field is missing, or `class_name` fails regex:
    1. Extract the most frequent nouns from outgoing/incoming predicates using TF-IDF.
    2. Convert nouns to `PascalCase` (e.g. `teachesCourse` $\rightarrow$ `CourseTeacher`).
    3. Synthesize gloss: `"Entity cluster characterized by predicates: [top predicates]."`

### 5.2 `tev1:0.8b` Axiom Adjudication Specification (`/v1/systemone`)
- **Endpoint:** `POST /v1/systemone`
- **Request Payload Schema:**
  ```json
  {
    "model": "tev1:0.8b",
    "state": {
      "task": "OWL2_TBox_Axiom_Verification",
      "open_world_assumption": true,
      "class_pair": {
        "C1": {
          "uri": ":VisitingProfessor",
          "label": "Visiting Professor",
          "instance_count": 1420,
          "top_out_predicates": [":teachesCourse", ":affiliatedWith", ":hasORCID"],
          "top_in_predicates": [":advisedBy", ":visitingChairAt"]
        },
        "C2": {
          "uri": ":FacultyMember",
          "label": "Faculty Member",
          "instance_count": 18900,
          "top_out_predicates": [":teachesCourse", ":affiliatedWith", ":hasTenureStatus"],
          "top_in_predicates": [":advisedBy", ":headedBy"]
        },
        "empirical_overlap": {
          "intersection_count": 1395,
          "p_c2_given_c1": 0.982,
          "p_c1_given_c2": 0.074,
          "predicate_jaccard": 0.714
        }
      }
    },
    "questions": {
      "taxonomic_axiom": {
        "type": "choice",
        "instructions": "Evaluate the formal OWL 2 taxonomic axiom between C1 and C2 based on their structural signatures and instance overlap.",
        "criteria": {
          "c1_sub_c2": "C1 is a strict subclass of C2 (every C1 is necessarily a C2)",
          "c2_sub_c1": "C2 is a strict subclass of C1 (every C2 is necessarily a C1)",
          "equivalent": "C1 and C2 are equivalent classes denoting the same concept",
          "disjoint": "C1 and C2 are mutually exclusive (owl:disjointWith)",
          "none": "No universal taxonomic subsumption or disjointness holds"
        }
      },
      "axiom_rigor": {
        "type": "score",
        "instructions": "Rate the ontological necessity of the selected relationship (distinguishing accidental data correlation from true conceptual subsumption).",
        "criteria": [
          "Accidental artifact of incomplete sampling; should not be in TBox",
          "Weak domain association; holds contingently but not universally",
          "Strong domain regularity suitable for lightweight RDFS schema",
          "Strict analytic and ontological necessity valid in OWL 2 DL"
        ]
      }
    }
  }
  ```
- **Response Format:**
  Maps each question key to its decision output:
  - For `choice`: `{"choice": "c1_sub_c2", "probability": 0.942, "confidence": 0.880, "distribution": {...}}`
  - For `noul`: `{"noul": 0.891, "confidence": 0.910}`
  - For `score`: `{"score": 2.75, "confidence": 0.850}`
- **Acceptance Gate Rule:**
  $$\begin{cases}
  P(\text{choice} = k^*) \ge 0.70 \land \text{confidence} \ge 0.65 \land \text{score} \ge 1.80 & (\texttt{choice}) \\
  \text{noul} \ge 0.80 \land |\text{noul} - 0.5| \ge 0.15 & (\texttt{noul})
  \end{cases}$$

### 5.3 Resilient Heuristic Simulation Architecture (Offline Fallback)
When Ollama daemon is offline, uninstalled, or models are not loaded:
1. **Fallback Concept Synthesizer (`tinyllama_simulate`):**
   - Parses local names of instances and predicates.
   - Cleans tokens, extracts common root nouns using TF-IDF ranking.
   - Formats class name in `PascalCase`.
   - Generates standardized definition gloss.
2. **Fallback Axiom Adjudicator (`tev1_simulate`):**
   - Reads empirical overlap $\text{conf}(C_1 \sqsubseteq C_2)$, $\text{conf}(C_2 \sqsubseteq C_1)$, $\text{Jacc}$, and instance counts from `state`.
   - Simulates 5-way `choice`:
     * If $\text{conf}(C_1 \sqsubseteq C_2) \ge 0.80$ and $\text{conf}(C_2 \sqsubseteq C_1) \ge 0.80 \implies$ `equivalent` ($P=0.95, \text{conf}=0.90, \text{score}=3.0$).
     * Else if $\text{conf}(C_1 \sqsubseteq C_2) \ge 0.80 \implies$ `c1_sub_c2` ($P=0.92, \text{conf}=0.88, \text{score}=2.8$).
     * Else if $\text{conf}(C_2 \sqsubseteq C_1) \ge 0.80 \implies$ `c2_sub_c1` ($P=0.92, \text{conf}=0.88, \text{score}=2.8$).
     * Else if $\frac{|I(C_1) \cap I(C_2)|}{\min(|I(C_1)|, |I(C_2)|)} \le 0.005$ and classes share common context $\implies$ `disjoint` ($P=0.88, \text{conf}=0.82, \text{score}=2.5$).
     * Else $\implies$ `none` ($P=0.85, \text{conf}=0.80, \text{score}=1.0$).
   - Simulates property `noul`:
     * For Transitive: $\text{noul} = \min(0.95, \rho_{\text{trans}} + 0.10)$ if $\rho_{\text{trans}} \ge 0.70$ else $\max(0.05, \rho_{\text{trans}} - 0.10)$.
     * For Symmetric: $\text{noul} = \min(0.95, \rho_{\text{sym}} + 0.10)$ if $\rho_{\text{sym}} \ge 0.70$ else $\max(0.05, \rho_{\text{sym}} - 0.10)$.
     * For Functional: $\text{noul} = \min(0.95, \rho_{\text{func}} + 0.05)$ if $\rho_{\text{func}} \ge 0.85$ else $\max(0.05, \rho_{\text{func}} - 0.10)$.

---

## 6. Graph-Theoretic Repair & Logical Soundness Specification

Let $G_{\text{sub}} = (V_C, E_{\text{sub}})$ be the directed graph of candidate `rdfs:subClassOf` edges admitted through the decision gate, where each edge $(u, v)$ has calibrated weight $w(u, v) = P(u \sqsubseteq v) \cdot \text{confidence}$.

### 6.1 Tarjan's Strongly Connected Components (SCC)
1. Run `nx.strongly_connected_components(G_sub)` to partition nodes into maximal strongly connected subgraphs.
2. For each non-trivial SCC $S$ with $|S| > 1$:
   - Check pairwise mutual edge weights.
   - If for all $u, v \in S$, $\min(w(u,v), w(v,u)) \ge 0.80$, declare all nodes in $S$ mutually equivalent:
     $$\forall u, v \in S: (u, \text{owl:equivalentClass}, v)$$
   - Designate a canonical representative node $u^* \in S$, redirect external incident edges to $u^*$, and collapse $S$ into $u^*$ in $G_{\text{sub}}$.

### 6.2 Minimum Feedback Arc Set (MFAS) Cycle Resolution
1. For any residual cycle in $G_{\text{sub}}$ (where mutual edge weights $< 0.80$, indicating noisy or contradictory induction):
2. Formulate the feedback arc set problem: find a minimum-weight set of edges $F \subset E_{\text{sub}}$ such that removing $F$ makes $G_{\text{sub}}$ acyclic.
3. Apply greedy / topological DFS cycle removal:
   - Identify simple cycles using `nx.simple_cycles(G_sub)`.
   - For each cycle, identify the edge with the minimal weight $e^* = \arg\min_{e \in \text{cycle}} w(e)$.
   - Remove $e^*$ from $E_{\text{sub}}$ and record in repair log.
4. Guarantee: Post-repair subsumption graph is a strict DAG:
   $$\text{len}(\text{list}(\text{nx.simple\_cycles}(G_{\text{sub}}))) == 0$$

### 6.3 Transitive Reduction (Hasse Diagram)
1. Redundant subsumption edges occur when $u \sqsubseteq v \sqsubseteq w$ and direct edge $(u, w)$ is also asserted.
2. Compute $G_{\text{reduced}} = \text{nx.transitive\_reduction}(G_{\text{sub}})$.
3. Preserve edge metadata from original graph $G_{\text{sub}}$ for edges surviving in $G_{\text{reduced}}$.
4. Output minimal, parsimonious Hasse diagram to `TBox.ttl`.

### 6.4 Disjointness-Subsumption Consistency Check
1. For every accepted disjointness axiom $(A, \text{owl:disjointWith}, B)$:
2. In DAG $G_{\text{sub}}$, compute the descendant sets $\mathcal{D}(A) = \text{nx.descendants}(G_{\text{sub}}, A) \cup \{A\}$ and $\mathcal{D}(B) = \text{nx.descendants}(G_{\text{sub}}, B) \cup \{B\}$.
3. If $\mathcal{D}(A) \cap \mathcal{D}(B) \ne \emptyset$:
   - A shared descendant $X \in \mathcal{D}(A) \cap \mathcal{D}(B)$ exists, making $X$ unsatisfiable ($X \sqsubseteq \bot$).
   - Trace shortest directed path $A \rightarrow^* X$ and $B \rightarrow^* X$.
   - Find the weakest subsumption edge $e_{\min} = \arg\min_{e \in \text{paths}} w(e)$ and compare its weight to the disjointness score $w(A \sqcap B \sqsubseteq \bot)$.
   - Prune whichever assertion has lower weight / confidence.
4. Verify $DVC_{\text{post}} = 0$ against ABox instances.

### 6.5 Property Characteristic Mutex Check
- Symmetric vs. Asymmetric: If both are asserted for property $P$, prune the characteristic with lower $\text{noul}$ score.
- Transitive vs. Asymmetric: Unsatisfiable in OWL 2 DL. Prune lower-confidence characteristic.

---

## 7. Serialization & Provenance Specification

### 7.1 Serialization Format
- Target file: `TBox.ttl` in standard W3C Turtle syntax.
- Mandatory prefixes:
  ```turtle
  @prefix : <http://example.org/ontology/> .
  @prefix owl: <http://www.w3.org/2002/07/owl#> .
  @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
  @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
  @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
  @prefix prov: <http://www.w3.org/ns/prov#> .
  ```

### 7.2 Research Provenance Reification (PROV-O)
When `EXPORT_STRICT_OWL2_DL = False`, every induced axiom is reified with research telemetry:
```turtle
:VisitingProfessor rdfs:subClassOf :FacultyMember .

[] a owl:Axiom ;
   owl:annotatedSource :VisitingProfessor ;
   owl:annotatedProperty rdfs:subClassOf ;
   owl:annotatedTarget :FacultyMember ;
   :decisionProbability 0.942 ;
   :decisionConfidence 0.880 ;
   :aboxSupportCount 1395 ;
   prov:wasAttributedTo "ollama:tev1:0.8b" .
```
When `EXPORT_STRICT_OWL2_DL = True`, the generator strips all `owl:Axiom` reification blocks to output a standard OWL 2 DL ontology parseable by strict DL reasoners (e.g. Pellet, HermiT).

---

## 8. Research Evaluation Metrics (Section 7)

Section 7 calculates, formats, and displays:

1. **Relationship Richness ($RR$):**
   $$RR = \frac{|P_{\text{obj}} \cup P_{\text{data}}|}{|P_{\text{obj}} \cup P_{\text{data}}| + |E_{\text{subClassOf}}|}$$
   Measures structural balance between horizontal relations and vertical taxonomy.
2. **Inheritance Richness ($IR$):**
   $$IR = \frac{\sum_{C_i \in \mathcal{C}} |\text{children}(C_i)|}{|\mathcal{C}|}$$
   Measures vertical fan-out and taxonomic depth.
3. **Class Coverage Ratio ($CCR$):**
   $$CCR = \frac{|\{e \in \text{Entities}(\mathcal{A}) \mid \exists C \in \mathcal{T}: e \in I(C)\}|}{|\text{Entities}(\mathcal{A})|}$$
   Measures the fraction of ABox entities categorized by the induced schema.
4. **Cycle Elimination Count ($CEC$):**
   Count of cyclic edges resolved into `owl:equivalentClass` or removed via MFAS.
5. **Disjointness Violation Count ($DVC$):**
   Instances violating disjointness before repair ($DVC_{\text{pre}}$) vs after repair ($DVC_{\text{post}}$). Target: $DVC_{\text{post}} = 0$.
6. **Token Utilization Telemetry:**
   Histogram showing $100\%$ of payloads $\le 1500$ tokens, with average, median, and 99th percentile token lengths.

---

## 9. Comprehensive Tables

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Setup | Section 0 Config & Seed Init | Configures deterministic random seeds, API endpoints, token caps, and statistical thresholds | Env variables, seed constants | Config dict, random seed handles | Falls back to default constants | SRS §3.1, §8 |
| 2 | Ingestion | Chunked Streaming ABox Parser | Ingests `ABox.ttl` in bounded memory via `rdflib` chunking or relational store | `ABox.ttl` filepath | Relational `triples` table | Raises file not found / syntax error if invalid RDF | SRS §4 FR-1.1 |
| 3 | Ingestion | Namespace & Local Name Extractor | Deterministically splits URI into namespace and local name; normalizes camelCase/snake_case | URI strings | Normalized string tokens | Returns raw string on unparseable URIs | SRS §4 FR-1.2 |
| 4 | Ingestion | Predicate Signature xxhash64 Hashing | Hashes incoming/outgoing predicate sets using 64-bit non-cryptographic hash | Node incident predicates | 64-bit integer hash | Defaults to hash of empty string if isolated node | SRS §4 FR-1.3 |
| 5 | Ingestion | Characteristic Set Equivalence Clustering | Groups untyped entities with matching hashes or signature Jaccard $\ge 0.85$ into clusters $K_i$ | Node signature hashes & Jaccard | Cluster prototypes $K_i$ | Creates singleton cluster for isolated signatures | SRS §4 FR-1.3 |
| 6 | Synthesis | Micro-Prompt Concept Induction | Dispatches bounded micro-prompt ($\le 400$ in, 64 out) to `tinyllama:latest` via `/api/generate` | Top 5 instances, predicates, datatypes | JSON with `class_name` and `gloss` | Invokes deterministic TF-IDF fallback on error/timeout | SRS §4 FR-2.1, FR-2.2 |
| 7 | Synthesis | PascalCase Regex Sanitizer | Validates generated class name matches `^[A-Z][a-zA-Z0-9]+$` | Raw generated string | Sanitized PascalCase string | Strips markdown, falls back to TF-IDF naming | SRS §4 FR-2.3 |
| 8 | Synthesis | TF-IDF Predicate Fallback Naming | Deterministically derives class names from highest TF-IDF predicate nouns | Predicate list of cluster | PascalCase class name & gloss | Generates generic `EntityClusterN` if no nouns found | SRS §4 FR-2.3 |
| 9 | Mining | Subsumption Candidate Pre-Filtering | Computes $\text{conf}(C_i \sqsubseteq C_j)$ and Jaccard; queues if $\text{conf} \ge 0.15$ or $\text{Jacc} \ge 0.40$ | Instance sets $I(C_i), I(C_j)$ | Candidate taxonomic pair list | Empty list if no pairs meet threshold | SRS §4 FR-3.1 |
| 10 | Mining | Disjointness Candidate Mining | Queues class pairs sharing superclass/domain where overlap ratio $\le 0.005$ | Instance sets, domain overlaps | Candidate disjointness pair list | Empty list if all pairs overlap significantly | SRS §4 FR-3.2 |
| 11 | Mining | Property Transitivity Ratio Mining | Computes $\rho_{\text{trans}}(P)$ from instance triangle counts | Property triples | Float ratio $[0.0, 1.0]$ | Returns $0.0$ if no length-2 paths exist | SRS §4 FR-3.3 |
| 12 | Mining | Property Symmetry Ratio Mining | Computes $\rho_{\text{sym}}(P)$ from bidirectional edge counts | Property triples | Float ratio $[0.0, 1.0]$ | Returns $0.0$ if no edges exist | SRS §4 FR-3.3 |
| 13 | Mining | Property Functionality Ratio Mining | Computes $\rho_{\text{func}}(P)$ from single out-degree node counts | Property triples | Float ratio $[0.0, 1.0]$ | Returns $0.0$ if property unused | SRS §4 FR-3.3 |
| 14 | Mining | Datatype vs Object Property Split | Classifies property range as XSD datatypes or OWL classes | Object RDF nodes | Datatype / Object property tag | Defaults to `owl:ObjectProperty` for URI targets | SRS §4 FR-4.4 |
| 15 | Adjudication | 5-way Taxonomic `choice` | Queries `tev1:0.8b` for `c1_sub_c2`, `c2_sub_c1`, `equivalent`, `disjoint`, `none` | Candidate pair state object | Choice key, probability, confidence | Falls back to empirical heuristic simulation | SRS §4 FR-4.2, §6.1 |
| 16 | Adjudication | Parallel `noul` Property Evaluation | Queries `tev1:0.8b` for Transitive, Symmetric, Asymmetric, Functional, InvFunctional | Property profile state object | Noul probabilities, confidence | Falls back to empirical ratio thresholds | SRS §4 FR-4.3 |
| 17 | Adjudication | 4-Level Axiom Rigor `score` | Rates ontological necessity ($0$ to $3$) to distinguish true axioms from artifacts | Axiom description state | Score float $[0.0, 3.0]$, confidence | Defaults to baseline score $2.0$ in simulation | SRS §4 FR-4.5 |
| 18 | Adjudication | $k$-ary Tournament Tree Reduction | Partitions $N > 15$ candidate domains/ranges into chunks of $b=15 + \text{Thing}$ | Candidate class list | Winning class URI or `owl:Thing` | Selects `owl:Thing` if all options below threshold | SRS §4 FR-5.1, FR-5.2 |
| 19 | Adjudication | Decision Acceptance Gate Filter | Filters choices by $\theta_{\text{prob}} \ge 0.70, \theta_{\text{conf}} \ge 0.65, \theta_{\text{score}} \ge 1.80$ and noul by $\ge 0.80$ | Adjudication results | Admitted candidate axioms | Rejects axiom, records in audit log | SRS §6.2 |
| 20 | Adjudication | Resilient Heuristic Simulation Engine | Emulates `/v1/systemone` and `/api/generate` deterministically when offline | Request payload | Simulated probability/choice JSON | Catches connection errors seamlessly | ORIGINAL_REQUEST R3 |
| 21 | Repair | Tarjan's SCC Equivalence Collapsing | Finds SCCs in $G_{\text{sub}}$ and collapses symmetric high-confidence pairs into `owl:equivalentClass` | Subsumption graph $G_{\text{sub}}$ | Equivalence sets, collapsed graph | Leaves asymmetric edges for MFAS | SRS §4 FR-6.1 |
| 22 | Repair | Minimum Feedback Arc Set DAG Repair | Removes minimal-weight edges to break residual cycles, guaranteeing a strict DAG | Collapsed graph $G_{\text{sub}}$ | Cycle-free DAG ($0$ simple cycles) | Logs pruned edges with confidence scores | SRS §4 FR-6.1 |
| 23 | Repair | Transitive Reduction (Hasse Diagram) | Eliminates redundant transitive shortcut edges | Cycle-free DAG | Minimal Hasse diagram DAG | Returns unchanged if graph is already reduced | SRS §4 FR-6.2 |
| 24 | Repair | Disjointness-Subsumption Conflict Resolver | Detects common descendants $X \in \mathcal{D}(A) \cap \mathcal{D}(B)$ and prunes weaker assertion | Disjointness axioms, DAG | Clean disjointness list & DAG | Emits conflict resolution diagnostic log | SRS §4 FR-6.3 |
| 25 | Repair | Property Mutex Validator | Enforces Symmetric $\ne$ Asymmetric and Transitive $\ne$ Asymmetric | Property characteristics | Consistent property axioms | Prunes lowest noul probability characteristic | SRS §4 FR-6.4 |
| 26 | Serialization | Turtle Schema Materialization | Serializes clean classes, properties, subsumptions, disjointness to `TBox.ttl` | Repaired graph structures | Valid `TBox.ttl` file | Validates parseability with `rdflib` | SRS §3.7, R1 |
| 27 | Serialization | W3C PROV-O Research Reification | Emits `owl:Axiom` with `:decisionProbability`, `:decisionConfidence`, `:aboxSupportCount`, `prov:wasAttributedTo` | Adjudication telemetry | Reified Turtle triples | Omitted if `EXPORT_STRICT_OWL2_DL = True` | SRS §5 NFR-3 |
| 28 | Evaluation | OntoQA Metric Suite ($RR, IR, CCR$) | Calculates Relationship Richness, Inheritance Richness, Class Coverage Ratio | ABox graph, TBox graph | Formatted metric table & dict | Handles empty entity sets with zero-division guards | SRS §7 |
| 29 | Evaluation | Soundness Audit ($CEC, DVC_{\text{post}}$) | Verifies Cycle Elimination Count and $DVC_{\text{post}} == 0$ | ABox instances, TBox constraints | Soundness verification report | Asserts $DVC_{\text{post}} == 0$; fails test if $> 0$ | SRS §7 |
| 30 | Evaluation | Token Ceiling & Telemetry Auditor | Analyzes payload token distribution; audits $100\% \le 1,500$ tokens | Request telemetry logs | Token histogram & audit summary | Flags warning if any request $> 1,500$ tokens | SRS §5 NFR-1, §7 |
| 31 | Evaluation | Taxonomy Hierarchy Visualizer | Renders graphical tree/DAG visualization of induced TBox taxonomy | Transitive reduction DAG | Matplotlib figure in notebook | Gracefully handles non-planar graphs | SRS §7 |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Ingestion | Empty `ABox.ttl` (0 triples) | Graph parses to empty dataset; pipeline produces empty TBox with standard ontology header; metrics evaluate to $0.0$ without crashing. |
| 2 | Ingestion | 100% untyped entities (no explicit `rdf:type` triples) | All entities are grouped into Characteristic Sets by predicate signature; Section 2 synthesizes class names for all high-support clusters; $CCR$ reaches $1.0$. |
| 3 | Ingestion | Singleton/isolated entity (no incoming or outgoing predicates) | Entity has empty signature $\emptyset$; grouped into empty characteristic set; skipped from class induction or assigned to `owl:Thing`. |
| 4 | Synthesis | `tinyllama:latest` generates invalid JSON or markdown code block | JSON parser raises error; regex fallback intercepts; TF-IDF predicate extraction derives class name and generic gloss; notebook cell continues without failure. |
| 5 | Synthesis | `tinyllama:latest` generates non-alphanumeric or lowercase class name | Regex `^[A-Z][a-zA-Z0-9]+$` rejects candidate name; TF-IDF fallback naming activates; valid PascalCase URI emitted. |
| 6 | Mining | Predicate has 0 transitive paths (denominator $= 0$ in $\rho_{\text{trans}}$) | Division by zero intercepted; $\rho_{\text{trans}}(P)$ safely returns $0.0$. |
| 7 | Mining | High-cardinality predicate with $N = 250$ candidate domain classes | Tournament tree partitions 250 candidates into $\lceil \log_{15}(250) \rceil = 2$ rounds of 16-key batches; payload remains strictly $\le 1,500$ tokens. |
| 8 | Adjudication | Ollama daemon offline or HTTP connection refused | Catch `requests.exceptions.ConnectionError`; trigger `tev1_simulate` and `tinyllama_simulate`; pipeline completes deterministically. |
| 9 | Adjudication | Decision near decision boundary ($\text{noul} = 0.52$) | Intercepted by deadband filter ($|0.52 - 0.50| = 0.02 < \delta_{\text{deadband}} = 0.15$); characteristic rejected due to epistemic uncertainty. |
| 10 | Repair | Direct 2-node cycle with mutual confidence ($A \sqsubseteq B$ and $B \sqsubseteq A$ with $w \ge 0.80$) | Tarjan's SCC groups $\{A, B\}$; emits $A \text{ owl:equivalentClass } B$; collapses into single node in $G_{\text{sub}}$. |
| 11 | Repair | 3-node asymmetric cycle ($A \sqsubseteq B \sqsubseteq C \sqsubseteq A$ with weights $0.9, 0.8, 0.4$) | SCC identifies cycle; asymmetric weights prevent equivalentClass collapsing; MFAS removes lowest-weight edge $(C, A)$ ($w=0.4$); strict DAG formed. |
| 12 | Repair | Transitive shortcut ($A \sqsubseteq B$, $B \sqsubseteq C$, $A \sqsubseteq C$) | `nx.transitive_reduction` removes shortcut edge $(A, C)$; minimal Hasse diagram preserved. |
| 13 | Repair | Subsumption-Disjointness contradiction ($A \sqsubseteq B$ and $A \text{ owl:disjointWith } B$) | Consistency check finds shared descendant $A \in \mathcal{D}(A) \cap \mathcal{D}(B)$; compares weights; removes assertion with lower confidence; $DVC_{\text{post}}$ remains $0$. |
| 14 | Repair | Property declared both `Symmetric` and `Asymmetric` | Mutex check compares calibrated $\text{noul}$ scores; keeps higher score; prunes lower score to prevent OWL 2 DL unsatisfiability. |
| 15 | Serialization | `EXPORT_STRICT_OWL2_DL = True` | Provenance reification blocks (`owl:Axiom`) omitted; clean, standard OWL 2 DL Turtle emitted. |
| 16 | Evaluation | Class taxonomy is a disconnected forest (multiple root classes) | Matplotlib visualizer layouts multiple subtrees without overlapping nodes or index errors. |

---

## 10. Acceptance Criteria Checklist

| Ref | Requirement | Pass Condition |
| :--- | :--- | :--- |
| **AC-1** | End-to-End Notebook Execution | `ABox2TBox.ipynb` runs all 8 sections (0 to 7) without unhandled exceptions or cell failure. |
| **AC-2** | Valid OWL 2 / RDFS Output | Output `TBox.ttl` is valid Turtle, successfully parsed by `rdflib.Graph().parse("TBox.ttl")`. |
| **AC-3** | Strict Subsumption DAG | Subsumption hierarchy in `TBox.ttl` has strictly $0$ directed cycles (`nx.is_directed_acyclic_graph == True`). |
| **AC-4** | Zero Post-Repair Disjointness Violations | $DVC_{\text{post}} == 0$ evaluated over the benchmark instance dataset. |
| **AC-5** | Strict Context Token Bound | $100\%$ of all model request payloads are bounded to $\le 1,500$ tokens (hard ceiling $\le 2,050$). |
| **AC-6** | OntoQA Metric Reporting | Section 7 calculates and renders $RR$, $IR$, and $CCR$ with non-empty values. |
| **AC-7** | Visual Hierarchy Rendering | Section 7 generates and renders a Matplotlib diagram of the class hierarchy DAG. |
| **AC-8** | Automated Verification Harness | `test_pipeline.py` executes notebook or pipeline programmatically and reports all assertions pass. |
