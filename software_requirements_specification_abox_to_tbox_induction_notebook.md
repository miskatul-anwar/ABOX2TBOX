# Software Requirements Specification (SRS)
## Scalable Neuro-Symbolic ABox-to-TBox Ontology Induction Notebook (`ABox2TBox.ipynb`)

* **Document Version:** 1.0.0
* **Target Artifact:** Jupyter Notebook (`ABox2TBox.ipynb`)
* **Primary Input:** Instance-level Knowledge Base / Data Warehouse export (`ABox.ttl`)
* **Primary Output:** Terminological Schema & Ontology (`TBox.ttl`)
* **Inference Engines:** Ollama `/v1/systemone` (`tev1:0.8b`) & Ollama `/api/generate` (`tinyllama:latest`)
* **Symbolic & Graph Engines:** `rdflib`, `networkx`, `sqlite3` / `duckdb` (out-of-core triple indexing)

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional, architectural, and non-functional requirements for `ABox2TBox.ipynb`, a research-grade Jupyter Notebook designed to induce a formal OWL 2 / RDFS Terminological Box (`TBox.ttl`) from a large-scale Assertion Box (`ABox.ttl`). The system combines deterministic graph algorithms and statistical data mining (`rdflib`, `networkx`) with ultra-lightweight local language models (`tinyllama:latest` for lexical concept synthesis and `tev1:0.8b` for calibrated single-pass axiom adjudication).

### 1.2 Scope
Modern enterprise data warehouses and RDF knowledge bases frequently suffer from schema drift, missing `rdf:type` declarations, or implicit taxonomic hierarchies embedded exclusively in instance-level triples. Direct prompting of Large Language Models (LLMs) over large RDF graphs fails due to context window limits, quadratic attention scaling, and syntactic hallucinations.

`ABox2TBox.ipynb` resolves these bottlenecks through a **Neuro-Symbolic Map-Compress-Adjudicate-Repair** architecture:
1. **Context-Invariant Compression:** Billions or millions of ABox triples are deterministically compressed into structural equivalence classes (*Characteristic Sets*) so that LLM prompt sizes remain strictly $O(1)$ with respect to total ABox triple count.
2. **Strict Division of Labor:**
   * `rdflib` + `networkx`: Exact graph traversal, co-occurrence counting, Jaccard/conditional probability pruning, cycle elimination, and transitive reduction.
   * `tinyllama:latest` ($1.1\text{B}$ parameters): Open-vocabulary lexical abstraction, proposing candidate class names (`rdfs:label`), and synthesizing human-readable descriptions (`rdfs:comment`) for untyped entity clusters.
   * `tev1:0.8b` ($752\text{M}$ parameters via `/v1/systemone`): Calibrated probabilistic decision-making (`noul`, `choice`, `score`) to verify formal ontological axioms (`rdfs:subClassOf`, `owl:disjointWith`, `rdfs:domain`, `rdfs:range`, and algebraic property characteristics).

### 1.3 Definitions, Acronyms, and Formal Notation
| Term / Symbol | Definition |
| :--- | :--- |
| **ABox ($\mathcal{A}$)** | Assertion Box: Instance-level facts comprising concept assertions $C(a)$ (`a rdf:type C`) and role assertions $R(a, b)$ (`a R b`). |
| **TBox ($\mathcal{T}$)** | Terminological Box: Schema-level axioms governing classes and properties, such as $C_1 \sqsubseteq C_2$ (`rdfs:subClassOf`) and $C_1 \sqcap C_2 \sqsubseteq \bot$ (`owl:disjointWith`). |
| **Characteristic Set ($CS$)** | For a node $v \in \mathcal{A}$, the set of incident outgoing and incoming properties and explicit types: $CS(v) = \{p^+ \mid (v, p, o) \in \mathcal{A}\} \cup \{p^- \mid (s, p, v) \in \mathcal{A}\} \cup \{\tau \mid (v, \text{rdf:type}, \tau) \in \mathcal{A}\}$. |
| **$\text{supp}(X)$** | Support: Exact cardinality of instances or triples satisfying structural pattern $X$ in $\mathcal{A}$. |
| **$\text{conf}(C_1 \sqsubseteq C_2)$** | Empirical conditional inclusion probability: $\frac{|I(C_1) \cap I(C_2)|}{|I(C_1)|}$, where $I(C)$ is the instance extension of class $C$. |
| **`/v1/systemone`** | Ollama's native single-pass decision API implementing the TypeSafe Jev specification for `noul`, `choice`, and `score` primitives. |

---

## 2. Overall System Architecture

### 2.1 Component Responsibilities & Strict Separation of Concerns

| Subsystem | Assigned Tool / Model | Permitted Operations | Prohibited Operations |
| :--- | :--- | :--- | :--- |
| **Ingestion & Indexing** | `rdflib` + Out-of-Core Store (`SQLite` / `DuckDB`) | Streaming parse of `ABox.ttl`, URI prefix normalization, frequency aggregation, Characteristic Set hashing. | Loading raw multi-gigabyte graphs into unindexed Python lists or LLM prompts. |
| **Graph Mining & Topology** | `networkx` | Directed graph construction, conditional probability matrices, Tarjan's Strongly Connected Components (SCC), Hasse diagram transitive reduction, Minimum Feedback Arc Set. | Semantic disambiguation of polysemous URI labels. |
| **Lexical & Concept Synthesis** | `tinyllama:latest` (`/api/generate`) | Generating concise hypernym labels (`PascalCase` class identifiers) and 1-sentence glosses for untyped Characteristic Set clusters. | Deciding formal logical axioms, outputting raw Turtle syntax directly to `TBox.ttl`, or processing $>512$ tokens per call. |
| **Axiom Adjudication** | `tev1:0.8b` (`/v1/systemone`) | Evaluating binary (`noul`), multi-way taxonomic (`choice`), and rubric quality (`score`) questions over compact structural profiles. | Free-form text generation or evaluating $>24$ options in a single `choice` query. |

### 2.2 End-to-End Dataflow Pipeline

```
[ABox.ttl (Disk)]
       │
       ▼ (1. Streaming Parse & Characteristic Set Hashing via rdflib)
[Structural Summary Index: Property Signatures & Entity Equivalence Classes]
       │
       ├──► (2a. Untyped CS Clusters) ──► [tinyllama:latest] ──► Candidate Class Labels & Glosses
       │
       ▼ (2b. Statistical Co-occurrence & Inclusion Mining via networkx)
[Candidate Axiom Pool: (C1, C2) Pairs & Property Profiles]
       │
       ▼ (3. Bounded-Context Micro-Batching & Tournament Tree Partitioning)
[tev1:0.8b (/v1/systemone)] ──► Calibrated Probabilities (noul, choice, score)
       │
       ▼ (4. Graph-Theoretic Repair & Logical Consistency via networkx)
[SCC Equivalence Collapsing -> Minimum Feedback Arc Set -> Transitive Reduction]
       │
       ▼ (5. Serialization & Provenance Injection via rdflib)
[TBox.ttl + Research Evaluation Metrics & Calibration Report]
```

---

## 3. Notebook Structure Specification (`ABox2TBox.ipynb`)

To guarantee research reproducibility and interactive inspectability, the `.ipynb` file must be organized into **8 modular, sequential sections**:

1. **Section 0: Environment Setup, Hyperparameters & Reproducibility Seeds**
   * Configures deterministic random seeds, Ollama endpoint URLs, model tags (`tev1:0.8b`, `tinyllama:latest`), token budget caps, and statistical support/confidence thresholds.
2. **Section 1: Scalable ABox Ingestion & Characteristic Set Profiling (`rdflib`)**
   * Streams `ABox.ttl` in chunks, separates instance assertions from any pre-existing schema triples, and computes Characteristic Sets ($CS$) and property domain/range frequency tables.
3. **Section 2: Open-Vocabulary Concept Induction for Untyped Entities (`tinyllama:latest`)**
   * Identifies high-support untyped Characteristic Sets, constructs micro-prompts ($\le 350$ tokens) containing 5 sample local URI names and incident predicates, and queries `tinyllama:latest` to synthesize candidate class URIs and `rdfs:comment` descriptions.
4. **Section 3: Candidate Axiom Generation & Graph Pruning (`networkx`)**
   * Builds the candidate class co-occurrence graph and property signature bipartite graph. Prunes statistically improbable pairs before invoking neural inference.
5. **Section 4: Hierarchical Tournament & Batch Axiom Verification (`tev1:0.8b`)**
   * Packages candidate axioms into `/v1/systemone` payloads (`state` $\le 1,200$ tokens, $\le 32$ questions per batch, $\le 16$ options per `choice` head) and executes single-pass probability scoring.
6. **Section 5: Graph-Theoretic TBox Repair & Consistency Enforcement (`networkx`)**
   * Resolves cyclic `rdfs:subClassOf` chains, enforces disjointness consistency, and computes the Hasse diagram (transitive reduction).
7. **Section 6: `TBox.ttl` Materialization with W3C PROV-O Metadata (`rdflib`)**
   * Serializes validated OWL 2 / RDFS axioms and optional research provenance annotations (`owl:Axiom` reification with `tev1:0.8b` probability and ABox support counts) into `TBox.ttl`.
8. **Section 7: Research Evaluation, Ablation & Calibration Diagnostics**
   * Outputs OntoQA structural metrics, Expected Calibration Error (ECE) diagnostics, execution telemetry, and visual ontology hierarchy plots.

---

## 4. Functional Requirements (FR)

### FR-1: Context-Invariant ABox Ingestion & Structural Compression
* **FR-1.1 (Chunked Triple Streaming):** The notebook shall ingest `ABox.ttl` using a streaming or disk-backed `rdflib` store (or line-based N-Triples/Turtle chunking into an embedded relational table) so memory consumption remains bounded for KBs exceeding $10^7$ triples.
* **FR-1.2 (Namespace & Local Name Extraction):** The system shall deterministically split every URI into `(namespace, local_name)` and convert `camelCase` or `snake_case` local names into normalized lexical tokens.
* **FR-1.3 (Characteristic Set Quotients):** For every subject/object node $v \in \mathcal{A}$ lacking an explicit `rdf:type`, the system shall compute a 64-bit hash of its sorted predicate signature:
  $$h(v) = \text{xxhash64}\left(\text{sort}(\{p^+ \mid (v,p,o) \in \mathcal{A}\}) \parallel \text{sort}(\{p^- \mid (s,p,v) \in \mathcal{A}\})\right)$$
  Nodes sharing identical or high-Jaccard ($\ge 0.85$) signatures shall be grouped into an Equivalence Cluster $K_i$, reducing millions of instances to $M \ll |\mathcal{A}|$ structural prototypes.

### FR-2: Lexical Concept Synthesis via `tinyllama:latest`
* **FR-2.1 (Strict Role Confinement):** `tinyllama:latest` shall **only** be invoked for lexical naming and gloss generation over structural prototypes where explicit class labels are absent or opaque (e.g., `cls_99482`).
* **FR-2.2 (Micro-Prompt Token Bound):** Every prompt dispatched to `tinyllama:latest` shall be strictly bounded to $\le 400$ input tokens and `num_predict: 64` output tokens, formatted as a structured JSON completion template:
  * Input context: Top $k=5$ representative instance local names, top $k=5$ outgoing predicates, top $k=5$ incoming predicates, and sample literal datatypes.
  * Output schema: `{"class_name": "PascalCaseIdentifier", "gloss": "Concise 1-sentence ontological definition."}`.
* **FR-2.3 (Deterministic Sanitization):** The host Python code shall validate `tinyllama:latest` outputs via regular expressions (`^[A-Z][a-zA-Z0-9]+$`). If `tinyllama:latest` produces malformed JSON or invalid URI characters, a deterministic fallback naming algorithm (combining the highest-TF-IDF predicate nouns) shall execute automatically.

### FR-3: Statistical Candidate Generation & Pre-Filtering (`networkx`)
* **FR-3.1 (Subsumption Candidate Matrix):** For every pair of discovered or explicit classes $(C_i, C_j)$ with instance sets $I(C_i)$ and $I(C_j)$:
  $$\text{conf}(C_i \sqsubseteq C_j) = \frac{|I(C_i) \cap I(C_j)|}{|I(C_i)|}, \quad \text{Jacc}(C_i, C_j) = \frac{|I(C_i) \cap I(C_j)|}{|I(C_i) \cup I(C_j)|}$$
  A pair $(C_i, C_j)$ is forwarded to `tev1:0.8b` as a candidate taxonomic pair if and only if $\text{conf}(C_i \sqsubseteq C_j) \ge \tau_{\text{sub}}$ (default $0.15$) or their predicate signatures share Jaccard similarity $\ge \tau_{\text{sig}}$ (default $0.40$).
* **FR-3.2 (Disjointness Candidate Mining):** Pairs $(C_i, C_j)$ sharing a common superclass or overlapping predicate domains where $|I(C_i) \cap I(C_j)| / \min(|I(C_i)|, |I(C_j)|) \le \epsilon_{\text{disj}}$ (default $0.005$) shall be queued as candidate `owl:disjointWith` pairs.
* **FR-3.3 (Property Empirical Metrics):** For each object property $P$, `networkx` shall deterministically compute:
  * **Empirical Transitivity Ratio:**
    $$\rho_{\text{trans}}(P) = \frac{|\{(x,y,z) \mid (x,P,y) \in \mathcal{A} \land (y,P,z) \in \mathcal{A} \land (x,P,z) \in \mathcal{A}\}|}{|\{(x,y,z) \mid (x,P,y) \in \mathcal{A} \land (y,P,z) \in \mathcal{A}\}|}$$
  * **Empirical Symmetry Ratio:**
    $$\rho_{\text{sym}}(P) = \frac{|\{(x,y) \mid (x,P,y) \in \mathcal{A} \land (y,P,x) \in \mathcal{A}\}|}{|\{(x,y) \mid (x,P,y) \in \mathcal{A}\}|}$$
  * **Empirical Functionality Ratio:**
    $$\rho_{\text{func}}(P) = \frac{|\{x \mid \text{out\_deg}_P(x) = 1\}|}{|\{x \mid \text{out\_deg}_P(x) \ge 1\}|}$$
  These exact ratios are injected into the `state` object for `tev1:0.8b` so the decision model adjudicates whether low empirical ratios are due to Open-World Assumption (OWA) incompleteness or true ontological constraints.

### FR-4: Calibrated Axiom Adjudication via `tev1:0.8b` (`/v1/systemone`)
* **FR-4.1 (Context Window Protection):** Each `/v1/systemone` request to `tev1:0.8b` shall enforce:
  $$\text{Tokens}(\text{state}) + \text{Tokens}(\text{questions}) \le 1,500 \text{ tokens} \quad (\text{hard ceiling: } 2,050 \text{ tokens})$$
* **FR-4.2 (Taxonomic Relation Classification via `choice`):** For candidate class pairs $(C_1, C_2)$, `tev1:0.8b` shall evaluate a mutually exclusive 5-way `choice` question:
  * `c1_sub_c2`: $C_1 \sqsubseteq C_2$ (`C1 rdfs:subClassOf C2`)
  * `c2_sub_c1`: $C_2 \sqsubseteq C_1$ (`C2 rdfs:subClassOf C1`)
  * `equivalent`: $C_1 \equiv C_2$ (`C1 owl:equivalentClass C2`)
  * `disjoint`: $C_1 \sqcap C_2 \sqsubseteq \bot$ (`C1 owl:disjointWith C2`)
  * `none`: Overlapping or unrelated classes; emit no axiom.
* **FR-4.3 (Property Characteristics via `noul`):** For every object property $P$, `tev1:0.8b` shall evaluate parallel `noul` questions for:
  * `owl:TransitiveProperty`
  * `owl:SymmetricProperty`
  * `owl:AsymmetricProperty`
  * `owl:FunctionalProperty`
  * `owl:InverseFunctionalProperty`
* **FR-4.4 (Datatype vs. Object Property Classification):** Properties whose objects are RDF literals shall have their `rdfs:range` mapped to XSD types (`xsd:string`, `xsd:integer`, `xsd:decimal`, `xsd:dateTime`, `xsd:boolean`) via deterministic regex inspection combined with a `tev1:0.8b` `choice` disambiguation pass when literals are noisy strings.
* **FR-4.5 (Ontology Quality Scoring via `score`):** Candidate complex axioms (such as `owl:inverseOf` between $P_1$ and $P_2$) shall be evaluated using a 4-level `score` rubric ($0$ to $3$) measuring semantic validity and structural support.

### FR-5: Hierarchical Tournament Reduction for High-Cardinality `choice` Queries
* **FR-5.1 ($k$-ary Tournament Tree):** Because `tev1:0.8b` is trained on $2$ to $24$ options per `choice` question, whenever a property $P$ has $N > 15$ candidate `rdfs:domain` or `rdfs:range` classes, the system shall partition the candidates into chunks of size $b = 15$ (plus 1 `"owl:Thing"` fallback option $= 16$ keys).
* **FR-5.2 (Multi-Round Elimination):** Winner classes from Round $r$ (where probability $P(\text{choice}) \ge \tau_{\text{round}}$) advance to Round $r+1$ in $\lceil \log_{15}(N) \rceil$ passes until a single winning class (or `"owl:Thing"`) emerges.

### FR-6: Graph-Theoretic Repair & Logical Soundness (`networkx`)
* **FR-6.1 (Cycle Resolution via SCC & Feedback Arc Set):** Let $G_{\text{sub}} = (V_C, E_{\text{sub}})$ be the directed graph of accepted `rdfs:subClassOf` edges weighted by `tev1:0.8b` calibrated edge score $w(u, v) = P(u \sqsubseteq v) \cdot \text{confidence}$.
  1. Compute Strongly Connected Components (SCCs) via Tarjan's algorithm.
  2. For any SCC where bidirectional edges have symmetric high probability ($\min(w(u,v), w(v,u)) \ge 0.80$), collapse the nodes into an `owl:equivalentClass` cluster.
  3. For any remaining multi-node cycle caused by noisy local decisions, remove the minimum-weight edge(s) solving the Minimum Feedback Arc Set problem so $G_{\text{sub}}$ is a strict Directed Acyclic Graph (DAG).
* **FR-6.2 (Transitive Reduction / Hasse Diagram):** Execute `nx.transitive_reduction(G_sub)` to remove redundant edges $(u, w)$ whenever a directed path $u \rightarrow^+ v \rightarrow^+ w$ exists, keeping `TBox.ttl` minimal and parsimonious.
* **FR-6.3 (Disjointness-Subsumption Consistency Check):** For every accepted disjointness axiom $A \sqcap B \sqsubseteq \bot$, verify via DAG reachability in $G_{\text{sub}}$ that no class $X$ satisfies $X \in \text{descendants}(A) \cap \text{descendants}(B)$. If a conflict occurs, compare the `tev1:0.8b` log-odds of the disjointness axiom against the weakest subsumption edge on the path and prune the lower-scoring assertion.
* **FR-6.4 (Property Hierarchy Coherence):** Ensure no property $P$ is simultaneously declared `owl:SymmetricProperty` and `owl:AsymmetricProperty`, or `owl:TransitiveProperty` and `owl:AsymmetricProperty` (which is unsatisfiable in OWL 2 DL unless the property is empty).

---

## 5. Non-Functional Requirements (NFR)

### NFR-1: Strict Context-Length Decoupling ($O(1)$ Prompt Scaling)
Let $|\mathcal{A}|$ denote the number of triples in `ABox.ttl`. The token length $L$ of any request payload sent to `tev1:0.8b` or `tinyllama:latest` must satisfy:
$$\sup_{|\mathcal{A}| \rightarrow \infty} L(\text{payload}) \le C_{\max} = 1,500 \text{ tokens}$$
All scaling with respect to $|\mathcal{A}|$ is absorbed by deterministic streaming aggregation (`rdflib` / `duckdb`) and graph pruning (`networkx`).

### NFR-2: Scalability for Data Warehouses
* The notebook shall process an `ABox.ttl` containing $10^6$ to $10^7$ triples on a single workstation with $16\text{ GB}$ RAM and $4\text{ GB}$ VRAM (`tev1:0.8b` requires $\approx 774\text{ MiB}$ VRAM; `tinyllama:latest` requires $\approx 750\text{ MiB}$ VRAM, allowing both models to remain co-resident in GPU memory without model-swapping latency).

### NFR-3: Research Auditability & Provenance
* Every induced axiom in `TBox.ttl` shall optionally include OWL 2 Axiom Annotations (`owl:Axiom`, `owl:annotatedSource`, `owl:annotatedProperty`, `owl:annotatedTarget`) recording:
  * `:decisionProbability` (`xsd:decimal`): Raw probability from `tev1:0.8b`.
  * `:decisionConfidence` (`xsd:decimal`): Concentration metric from `/v1/systemone`.
  * `:aboxSupportCount` (`xsd:integer`): Number of supporting instance triples in `ABox.ttl`.
  * `prov:wasAttributedTo`: `"ollama:tev1:0.8b"` or `"ollama:tinyllama:latest"`.
* A toggle parameter `EXPORT_STRICT_OWL2_DL = True` shall allow researchers to export either a clean, standard TBox or an annotated research TBox.

---

## 6. Data Schemas & API Contracts

### 6.1 `tev1:0.8b` `/v1/systemone` Payload Contract (Class Hierarchy & Property Batch)

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

### 6.2 Decision Acceptance Gate Rule
An axiom proposed by `tev1:0.8b` is admitted into the candidate TBox graph $G_{\text{TBox}}$ if and only if:
$$\begin{cases}
P(\text{choice} = k^*) \ge \theta_{\text{prob}} \land \text{confidence} \ge \theta_{\text{conf}} \land \text{score} \ge \theta_{\text{score}}, & \text{for } \texttt{choice} \text{ questions} \\
\text{noul} \ge \theta_{\text{noul}} \land |\text{noul} - 0.5| \ge \delta_{\text{deadband}}, & \text{for } \texttt{noul} \text{ questions}
\end{cases}$$
Default calibrated thresholds: $\theta_{\text{prob}} = 0.70$, $\theta_{\text{conf}} = 0.65$, $\theta_{\text{score}} = 1.80$, $\theta_{\text{noul}} = 0.80$, and deadband $\delta_{\text{deadband}} = 0.15$.

---

## 7. Research Evaluation & Validation Metrics (Notebook Section 7)

To make `ABox2TBox.ipynb` directly usable for academic publications and benchmarking, Section 7 of the notebook shall automatically compute and render the following quantitative metrics:

1. **Schema Richness & Structural Metrics (OntoQA Standard):**
   * **Relationship Richness ($RR$):**
     $$RR = \frac{|P_{\text{obj}} \cup P_{\text{data}}|}{|P_{\text{obj}} \cup P_{\text{data}}| + |E_{\text{subClassOf}}|}$$
   * **Inheritance Richness ($IR$):** Average number of subclasses per class in the transitive reduction DAG:
     $$IR = \frac{\sum_{C_i \in \mathcal{C}} |\text{children}(C_i)|}{|\mathcal{C}|}$$
   * **Class Coverage Ratio ($CCR$):** Fraction of ABox entities covered by at least one induced or validated TBox class.
2. **Logical Soundness & Deductive Metrics:**
   * **Cycle Elimination Rate:** Number of raw cyclic assertions flagged and repaired via `networkx` SCC/FAS algorithms.
   * **Disjointness Violation Count ($DVC$):** Number of ABox instances violating induced `owl:disjointWith` axioms before and after graph repair (target: $DVC_{\text{post}} = 0$).
3. **Decision Model Telemetry:**
   * Entropy and Confidence distribution histograms across all `tev1:0.8b` `/v1/systemone` calls.
   * Prompt token utilization distribution (verifying $100\%$ of calls stay below $1,500$ tokens regardless of `ABox.ttl` size).

---

## 8. Implementation Dependencies & Environment Matrix

| Package | Minimum Version | Role in `.ipynb` |
| :--- | :--- | :--- |
| `python` | `>= 3.10` | Core runtime and type annotations |
| `ollama` | `>= 0.40.0` | Host daemon serving `tev1:0.8b` (`/v1/systemone`) and `tinyllama:latest` |
| `rdflib` | `>= 7.0.0` | Turtle parsing, namespace management, and `TBox.ttl` serialization |
| `networkx` | `>= 3.2.0` | DAG algorithms, SCC, transitive reduction, and bipartite signature mining |
| `duckdb` / `sqlite3` | Standard / `>= 1.0.0` | Out-of-core triple aggregation and Characteristic Set indexing for large KBs |
| `requests` / `httpx` | `>= 0.27.0` | Connection-pooled HTTP client for `/v1/systemone` batch execution |
| `matplotlib` / `pandas` | `>= 2.0.0` | Research evaluation tables, calibration plots, and TBox hierarchy visualization |