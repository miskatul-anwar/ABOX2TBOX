# Technical Environment & Dependency Survey Report
**Target Artifact:** `ABox2TBox.ipynb` & Automated Test Harness (`test_pipeline.py`)  
**Project:** Scalable Neuro-Symbolic ABox-to-TBox Ontology Induction  
**Investigating Agent:** `explorer_env_1`  
**Date:** 2026-10-14  

---

## 1. Executive Summary

This survey provides an empirical investigation of the host environment, runtime dependencies, Ollama server status, programmatic notebook execution capabilities, and the architectural design for the dual-model neuro-symbolic resilient fallback mechanism required by **Requirement R3** and **SRS Section 8**.

### Key Findings
1. **Python Environment:** The host runs Python **3.14.7** on Arch Linux (kernel 7.2.4-arch1-2 x86_64). Core symbolic and graph libraries (`rdflib 7.6.0`, `networkx 3.6.1`, `pandas 3.0.5`, `matplotlib 3.11.1`, `requests 2.34.2`, `httpx 0.28.1`, `sqlite3`, `numpy 2.5.3`, `pydantic 2.14.1`, `tqdm 4.70.0`) are fully installed and verified operational.
2. **Missing Optional Packages:** `duckdb`, `xxhash`, `nbformat`, `nbconvert`, and `nbclient` are not installed in the system environment. However:
   - `sqlite3` is fully available in standard library and meets all out-of-core indexing needs.
   - Standard library `hashlib.blake2b(digest_size=8)` or `hashlib.sha256()[:16]` provides deterministic 64-bit hashing identical in function to `xxhash64`.
   - All missing packages (`nbformat`, `nbclient`, `xxhash`, `duckdb`) can be installed into user space (`~/.local/lib/python3.14/site-packages`) via `pip install --user` if desired (PyPI connectivity and binary wheels verified).
3. **Programmatic Notebook Execution:** `IPython.core.interactiveshell.InteractiveShell` (IPython 9.17.1, `ipykernel 7.3.0`) is installed and was tested running code cells in-memory with full state persistence. `test_pipeline.py` can execute `ABox2TBox.ipynb` end-to-end without requiring `nbclient` or external dependencies.
4. **Ollama Service Status & Critical Vulnerability:**
   - Ollama daemon (`ollama serve`) is running on PID 1099 (`127.0.0.1:11434`), but is in an unhealthy state: calls to `/api/generate` with `tinyllama:latest` fail with HTTP 500 (`llama-server binary not found`).
   - Model `tev1:0.8b` is **not installed** in Ollama.
   - Endpoint `/v1/systemone` is **not implemented** by the daemon, returning HTTP 404 (`404 page not found`).
5. **Architectural Imperative:** Because Ollama cannot execute model inferences on this host in its current state, the **Resilient Simulation / Deterministic Heuristic Fallback Engine** is **mandatory** for end-to-end execution and automated tests. The architecture detailed in Section 4 provides a seamless, calibrated fallback ensuring that all acceptance criteria (OWL 2 DL validity, DAG hierarchy, $DVC_{\text{post}} = 0$, $\le 1,500$ token bounds) are strictly met.

---

## 2. Host Hardware & System Environment Matrix

| Dimension | Specification | Verification Command & Result |
| :--- | :--- | :--- |
| **Operating System** | Arch Linux (x86_64, rolling) | `uname -a` -> `Linux ryoku 7.2.4-arch1-2 #1 SMP PREEMPT_DYNAMIC` |
| **CPU Architecture** | x86_64 (Intel/AMD) | Verified via GNU/Linux release info |
| **System Memory (RAM)** | 15 GiB Total, 7.7 GiB Available | `free -h` -> 7.8 GiB used, 7.7 GiB available, 15 GiB swap free |
| **Storage (`/home`)** | 232 GB Total, 12 GB Free | `df -h /home` -> 95% used, 12 GB available |
| **GPU / Acceleration** | NVIDIA GeForce GTX 1050 Ti (4096 MiB VRAM) | `nvidia-smi` -> Driver 580.178.04, CUDA 13.0, 705 MiB allocated, ~3391 MiB free |
| **Matplotlib Backend** | `Agg` (Headless rendering verified) | `matplotlib.use('Agg')` -> verified plot creation and export |

*Note on SRS NFR-2 Compliance:* The hardware environment exactly matches the target specification in SRS NFR-2 ("single workstation with 16 GB RAM and 4 GB VRAM").

---

## 3. Python Runtime & Library Audit

### 3.1 Runtime Configuration
- **Python Binary:** `/usr/bin/python3`
- **Python Version:** `3.14.7 (main, Aug 10 2026, 07:46:56) [GCC 16.1.1 20260728]`
- **Virtual Environment:** None active (`$VIRTUAL_ENV` empty).
- **User Site-Packages:** Enabled at `/home/miskat/.local/lib/python3.14/site-packages` (verified present in `sys.path`).

### 3.2 Dependency Status Matrix

| Package | SRS Minimum | Host Version | Status | Architectural Recommendation & Fallback |
| :--- | :--- | :--- | :--- | :--- |
| `python` | `>= 3.10` | `3.14.7` | ✅ Satisfied | Native runtime. |
| `rdflib` | `>= 7.0.0` | `7.6.0` | ✅ Satisfied | Full support for Turtle parsing, namespaces, graph mining, PROV-O serialization. |
| `networkx` | `>= 3.2.0` | `3.6.1` | ✅ Satisfied | Verified support for `tarjan_scc`, `transitive_reduction`, `is_directed_acyclic_graph`. |
| `sqlite3` | Standard | Available (3.x) | ✅ Satisfied | Standard library. Recommended for Characteristic Set indexing and out-of-core triple storage. |
| `duckdb` | `>= 1.0.0` | Not Installed | ⚠️ Fallback | Use `sqlite3` natively (as explicitly permitted by SRS Section 8 matrix: "`duckdb / sqlite3`"). |
| `requests` | Standard | `2.34.2` | ✅ Satisfied | Synchronous HTTP calls with session connection pooling. |
| `httpx` | `>= 0.27.0` | `0.28.1` | ✅ Satisfied | Modern client for async or synchronous REST queries. |
| `matplotlib` | `>= 2.0.0` | `3.11.1` | ✅ Satisfied | Headless `Agg` backend confirmed for Section 7 hierarchy and ECE calibration plots. |
| `pandas` | `>= 2.0.0` | `3.0.5` | ✅ Satisfied | Full dataframe indexing, summary tables, OntoQA metrics aggregation. |
| `numpy` | Standard | `2.5.3` | ✅ Satisfied | Matrix computations and statistical calculations. |
| `tqdm` | Standard | `4.70.0` | ✅ Satisfied | Ingestion and tournament progress bars. |
| `pydantic` | Standard | `2.14.1` | ✅ Satisfied | JSON schema parsing and API request/response validation. |
| `xxhash` | Standard | Not Installed | ⚠️ Fallback | Use standard library `hashlib.blake2b(data, digest_size=8).hexdigest()` or `hashlib.sha256(data).hexdigest()[:16]` for 64-bit CS hashes. |
| `IPython` | `>= 8.0` | `9.17.1` | ✅ Satisfied | In-process execution shell. |
| `ipykernel` | `>= 6.0` | `7.3.0` | ✅ Satisfied | Jupyter kernel backend. |
| `nbformat` | Standard | Not Installed | ⚠️ Fallback | Standalone JSON parser in `test_pipeline.py` or `pip install --user nbformat`. |
| `nbclient` | Standard | Not Installed | ⚠️ Fallback | In-process `InteractiveShell` execution harness or `pip install --user nbclient`. |

---

## 4. Ollama Service & Endpoint Investigation

### 4.1 Daemon & Process Status
```bash
$ ps aux | grep -i ollama
ollama      1099  0.0  0.2 1874120 44464 ?       Ssl  22:35   0:00 /usr/local/bin/ollama serve
```
- Daemon is running under user `ollama` listening on TCP `127.0.0.1:11434`.
- Host CLI version: `0.40.4`. Daemon version reported via API: `0.32.15`.

### 4.2 Model Inventory (`/api/tags`)
```json
{
  "models": [
    {"name": "gemma4:cloud", "size": 312},
    {"name": "tinyllama:latest", "size": 637700138, "parameter_size": "1B", "format": "gguf"},
    {"name": "gemma4:latest", "size": 9608350718, "parameter_size": "8.0B"},
    {"name": "qwen3.5:2b", "size": 2741192820, "parameter_size": "2.3B"},
    {"name": "gemma4:e2b", "size": 7162405886, "parameter_size": "5.1B"}
  ]
}
```
- `tinyllama:latest`: Model weights are present on disk (~637 MB).
- `tev1:0.8b`: **Not present**.

### 4.3 Endpoint Test Results
1. **Endpoint `POST /api/generate` (`tinyllama:latest`):**
   ```json
   {
     "error": "error starting llama-server: llama-server binary not found (checked: /usr/local/lib/ollama/llama-server, /usr/local/bin/build/lib/ollama/llama-server...). Run 'cmake -S llama/server --preset cpu && cmake --build --preset cpu' first "
   }
   ```
   *Diagnosis:* The Ollama installation lacks the compiled `llama-server` runtime executable, preventing local inference execution.
2. **Endpoint `POST /v1/systemone`:**
   ```http
   HTTP/1.1 404 Not Found
   Content-Length: 18

   404 page not found
   ```
   *Diagnosis:* The standard Ollama daemon does not implement the experimental `/v1/systemone` route.

---

## 5. Architectural Design: Resilient Neuro-Symbolic Simulation & Fallback (R3)

To ensure the pipeline satisfies **R3** and runs deterministically whether Ollama is online, offline, or lacking model binaries, the notebook and test harness must employ a unified **`NeuroSymbolicClient`** adapter.

### 5.1 Architecture Diagram
```
                     ┌──────────────────────────────────────────────┐
                     │          ABox2TBox Induction Pipeline        │
                     │  (Section 2: Synthesis & Section 4: Axioms)  │
                     └──────────────────────┬───────────────────────┘
                                            │
                                  [NeuroSymbolicClient]
                                            │
                           ┌────────────────┴────────────────┐
                           ▼                                 ▼
                 [Probe Ollama Daemon]             [Deterministic Fallback]
                /api/tags & test query             (When offline/404/500/mock)
                           │                                 │
                 ┌─────────┴─────────┐                       │
                 ▼                   ▼                       ▼
            [Available]          [Failed]          ┌───────────────────────┐
                 │                   └────────────►│ Heuristic Synthesis   │
                 ▼                                 │ - TF-IDF Noun Naming  │
        Live Ollama Calls                          │ - Calibrated Stats    │
        - /api/generate                            │ - Bounded Tokens      │
        - /v1/systemone                            │ - PROV-O Tagging      │
                                                   └───────────────────────┘
```

### 5.2 Deterministic Lexical Concept Synthesis Fallback (Section 2)
When `tinyllama:latest` via `/api/generate` is unavailable or returns an error:
1. **Micro-Prompt Formatting:** Formulate the standard JSON prompt with $k=5$ representative instances, $k=5$ outgoing predicates, and $k=5$ incoming predicates ($\le 400$ tokens).
2. **Deterministic Hypernym Extraction:**
   - Tokenize predicate local names (e.g. `teachesCourse` -> `['teaches', 'Course']`, `advisedBy` -> `['advised', 'By']`, `hasDepartment` -> `['has', 'Department']`).
   - Identify candidate domain nouns (`Course`, `Department`, `Researcher`, `Faculty`, `Publication`).
   - Construct a `PascalCase` class identifier: e.g. `CourseInstructor`, `DepartmentAffiliate`, or `Cluster_<TopNoun>`.
   - Validate against regular expression `^[A-Z][a-zA-Z0-9]+$`. If regex fails, fallback to `Concept_<ClusterID>`.
3. **Gloss Synthesis:** Generate a deterministic ontological gloss:
   `"Class characterizing entities with outgoing properties: {preds_out} and incoming properties: {preds_in}."`
4. **Provenance Metadata:** Attach `prov:wasAttributedTo: "heuristics:lexical_concept_synthesis"`.

### 5.3 Deterministic Axiom Adjudication Fallback (Section 4)
When `tev1:0.8b` via `/v1/systemone` is unavailable (404 or connection error):
1. **Input State & Context Verification:** The client receives the standard `state` object containing:
   - $C_1, C_2$ labels and instance counts.
   - Empirical overlap: $p(C_2 \mid C_1)$, $p(C_1 \mid C_2)$, Jaccard similarity $\text{Jacc}(C_1, C_2)$.
   - Object property metrics: $\rho_{\text{trans}}(P)$, $\rho_{\text{sym}}(P)$, $\rho_{\text{func}}(P)$.
   - Hard context check: verify $\text{Tokens}(\text{state}) + \text{Tokens}(\text{questions}) \le 1,500$ tokens.
2. **5-Way Taxonomic Decision Logic (`choice`):**
   - **`equivalent`:** If $p(C_2 \mid C_1) \ge 0.85 \land p(C_1 \mid C_2) \ge 0.85$ (or $\text{Jacc}(C_1, C_2) \ge 0.85$):
     $$\text{prob} = \min(p(C_2 \mid C_1), p(C_1 \mid C_2)), \quad \text{confidence} = 0.90, \quad \text{score} = 2.85$$
   - **`c1_sub_c2` ($C_1 \sqsubseteq C_2$):** If $p(C_2 \mid C_1) \ge 0.70 \land p(C_1 \mid C_2) < 0.70$:
     $$\text{prob} = \min(0.98, p(C_2 \mid C_1)), \quad \text{confidence} = 0.85, \quad \text{score} = 2.50$$
   - **`c2_sub_c1` ($C_2 \sqsubseteq C_1$):** If $p(C_1 \mid C_2) \ge 0.70 \land p(C_2 \mid C_1) < 0.70$:
     $$\text{prob} = \min(0.98, p(C_1 \mid C_2)), \quad \text{confidence} = 0.85, \quad \text{score} = 2.50$$
   - **`disjoint` ($C_1 \sqcap C_2 \sqsubseteq \bot$):** If $\frac{|I(C_1) \cap I(C_2)|}{\min(|I(C_1)|, |I(C_2)|)} \le 0.005$ and classes share an ancestor or common domain/range:
     $$\text{prob} = 0.95, \quad \text{confidence} = 0.80, \quad \text{score} = 2.40$$
   - **`none`:** If none of the above criteria hold:
     $$\text{prob}(\text{none}) = 0.85, \quad \text{confidence} = 0.75, \quad \text{score} = 1.00$$
3. **Property Characteristics Decision Logic (`noul`):**
   - Transitive: $\text{noul} = \min(0.99, \rho_{\text{trans}})$ if $\rho_{\text{trans}} \ge 0.80$, else $\max(0.01, \rho_{\text{trans}})$.
   - Symmetric: $\text{noul} = \min(0.99, \rho_{\text{sym}})$ if $\rho_{\text{sym}} \ge 0.80$, else $\max(0.01, \rho_{\text{sym}})$.
   - Asymmetric: $\text{noul} = 0.95$ if $\rho_{\text{sym}} \le 0.05$ and $|E(P)| \ge 5$, else $0.05$.
   - Functional: $\text{noul} = \min(0.99, \rho_{\text{func}})$ if $\rho_{\text{func}} \ge 0.85$, else $\max(0.01, \rho_{\text{func}})$.
   - Inverse Functional: based on incoming object uniqueness.
4. **Decision Acceptance Gating (SRS 6.2):**
   - Axiom admitted if and only if $\text{prob} \ge \theta_{\text{prob}}$ (0.70) $\land \text{confidence} \ge \theta_{\text{conf}}$ (0.65) $\land \text{score} \ge \theta_{\text{score}}$ (1.80) for `choice`, and $\text{noul} \ge 0.80 \land |\text{noul} - 0.5| \ge 0.15$ for `noul`.
   - The simulation guarantees calibrated scores that respect the exact acceptance thresholds.
5. **Tournament Tree Partitioning ($b=15$):**
   - Candidates sorted by empirical frequency; partitioned into batches of 15 (+ 1 `owl:Thing` fallback); highest probability/coverage advances until the root class is selected.

---

## 6. Programmatic Notebook Execution & Test Runner Strategy

### 6.1 In-Process Execution Engine (Zero Dependency)
Because `nbclient` and `nbconvert` are not installed in the base system, `test_pipeline.py` should implement an in-process notebook runner using `IPython.core.interactiveshell.InteractiveShell`:

```python
import json
import sys
from IPython.core.interactiveshell import InteractiveShell

def execute_notebook(notebook_path: str, user_ns: dict = None) -> InteractiveShell:
    """Executes a Jupyter Notebook cell-by-cell in-process with state preservation."""
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    shell = InteractiveShell.instance()
    if user_ns:
        shell.user_ns.update(user_ns)
        
    for idx, cell in enumerate(nb.get('cells', [])):
        if cell.get('cell_type') == 'code':
            source = "".join(cell.get('source', []))
            if not source.strip():
                continue
            result = shell.run_cell(source)
            if not result.success:
                raise RuntimeError(
                    f"Notebook execution failed at cell {idx}:\n"
                    f"Source:\n{source[:200]}...\n"
                    f"Error: {result.error_in_exec}"
                )
    return shell
```

**Empirical Verification:**
- Tested in Python 3.14 on host.
- Correctly executes multiline Python code, imports libraries (`rdflib`, `networkx`, `sqlite3`), preserves state across cell boundaries, and halts on assertion failures.

### 6.2 Alternative: User-Space Pip Installation
If the user or orchestrator wishes to use standard `nbformat` and `nbclient`, running:
```bash
pip install --user nbformat nbclient xxhash duckdb
```
is fully functional and places packages into `/home/miskat/.local/lib/python3.14/site-packages` which is already in `sys.path`.

---

## 7. Concrete Action Items for Implementation Tracks

### 7.1 For Track 1 (Dataset & Test Runner)
- **Dataset (`ABox.ttl`):** Build a realistic academic university domain with:
  - Explicit classes: `Professor`, `Student`, `UndergraduateStudent`, `GraduateStudent`, `Department`, `Course`.
  - Untyped instance clusters with distinct predicate signatures (e.g. `VisitingResearcher`, `TeachingAssistant`).
  - Intentional cycles for repair testing: e.g. `AssociateProfessor rdfs:subClassOf FullProfessor` and `FullProfessor rdfs:subClassOf AssociateProfessor` (symmetric equivalence), plus a cyclic anomaly `Professor rdfs:subClassOf Undergrad`.
  - Disjointness test pairs: `FacultyMember` vs `Student`.
  - Properties with empirical transitivity (`hasPrerequisite`), symmetry (`collaboratesWith`), functionality (`hasAdvisor`), asymmetry (`advisedBy`).
- **Test Runner (`test_pipeline.py`):**
  - Use `InteractiveShell` runner to execute `ABox2TBox.ipynb`.
  - Validate output `TBox.ttl` with `rdflib.Graph().parse('TBox.ttl', format='turtle')`.
  - Assert 0 directed cycles in subsumption hierarchy (`nx.is_directed_acyclic_graph(G_tbox) is True`).
  - Assert $DVC_{\text{post}} == 0$ against `ABox.ttl`.
  - Assert all model request payloads $\le 1,500$ tokens.
  - Assert OntoQA metrics ($RR, IR, CCR$) are computed.

### 7.2 For Track 2 (`ABox2TBox.ipynb` Sections 0 to 7)
- **Section 0:** Set seeds, configure `OLLAMA_HOST = "http://localhost:11434"`, define `FALLBACK_SIMULATION_MODE = True` (or auto-detect).
- **Section 1:** Use `sqlite3` for out-of-core triple indexing and Characteristic Set aggregation. Use `hashlib.blake2b(..., digest_size=8).hexdigest()` for 64-bit CS hashes.
- **Section 2:** Integrate `tinyllama:latest` with micro-prompt ($\le 400$ tokens) and automatic fallback to TF-IDF predicate noun synthesis.
- **Section 3:** Compute empirical conditional inclusion probabilities and property ratios in `networkx`.
- **Section 4:** Implement `tev1:0.8b` client with 5-way choice, noul, score, and tournament reduction ($b=15$), coupled with the deterministic calibrated heuristic engine.
- **Section 5:** Apply Tarjan SCC for equivalence, Minimum Feedback Arc Set for strict DAG, and transitive reduction.
- **Section 6:** Serialize `TBox.ttl` with optional PROV-O annotations.
- **Section 7:** Render OntoQA metrics, ECE diagnostics, and hierarchy visualizations using `Agg` backend.
