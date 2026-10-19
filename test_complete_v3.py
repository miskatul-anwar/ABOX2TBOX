"""Regression checks for the reviewed notebook; no network calls or project outputs."""
from collections import defaultdict
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from pipeline_support import (DecisionTransport, calibration_metrics, class_closure,
    confirm_axiom, number, recover_assertions, repair_roles, validate_export)

ROOT = Path(__file__).parent
CELLS = json.loads((ROOT / 'abox2tbox.ipynb').read_text())['cells']
EX = Namespace('urn:test:')


def run_cell(ns, index):
    exec(compile(''.join(CELLS[index]['source']), f'notebook-cell-{index}', 'exec'), ns)


@pytest.fixture
def mining(monkeypatch):
    monkeypatch.setenv('USE_LLM', 'false')
    ns = {}
    for index in (3, 4, 5):
        run_cell(ns, index)
    conn = sqlite3.connect(':memory:')
    ns['conn'], ns['cur'] = conn, conn.cursor()
    ns['cur'].execute('CREATE TABLE triples(subject, predicate, object, is_literal, datatype)')
    yield ns
    conn.close()


def insert(ns, rows):
    ns['cur'].executemany('INSERT INTO triples VALUES (?, ?, ?, 0, NULL)',
                          [tuple(map(str, row)) for row in rows])


def test_restrictions_consider_every_positive_and_negative_filler(mining):
    ns = mining
    positives = {str(EX[f'p{i}']) for i in range(4)}
    negatives = {str(EX[f'n{i}']) for i in range(4)}
    rows = []
    # First fillers have another type; only second fillers support the target.
    for s in sorted(positives | negatives):
        rows += [(s, EX.link, s + ':first'), (s, EX.link, s + ':second'),
                 (s + ':first', RDF.type, EX.Other), (s + ':second', RDF.type, EX.Target)]
    insert(ns, rows)
    ns['class_instances'] = {str(EX.Positive): positives, str(EX.Negative): negatives}
    ns['config']['THETA_LOCAL_RESTRICTION'] = 0.0
    run_cell(ns, 14)
    candidates = [r for r in ns['candidate_local_restrictions']
        if r['class'] == str(EX.Positive) and r['filler'] == str(EX.Target) and r['type'] == 'someValuesFrom']
    assert len(candidates) == 1
    assert candidates[0]['coverage'] == 1
    # Four true and four false positives => F1=2/3, not 1.
    assert candidates[0]['phi_celoe'] == pytest.approx((2/3) + .2 * ((2/3) - .5) - .03 * 3)


def test_signature_containment_direction_and_no_type_only_similarity(mining):
    ns = mining
    rows = []
    for cls, predicates in [(EX.A, [EX.p]), (EX.B, [EX.p, EX.q]), (EX.C, [EX.r])]:
        for i in range(3):
            subject = str(cls) + str(i)
            rows.append((subject, RDF.type, cls))
            rows.extend((subject, p, EX.value) for p in predicates)
    insert(ns, rows)
    ns['induced_class_uris'] = {str(EX.A), str(EX.B), str(EX.C)}
    run_cell(ns, 13)
    pair, = ns['candidate_taxonomic_pairs']
    assert (pair['c1'], pair['c2']) == (str(EX.A), str(EX.B))
    assert pair['p_c2_c1'] == .5
    assert pair['p_c1_c2'] == 1
    assert all(str(RDF.type) not in predicates for predicates in ns['class_core_predicates'].values())
    run_cell(ns, 16)
    assert not ns['adjudicated_subsumptions']  # signatures alone are proposals
    assert not ns['adjudicated_equivalences']


def test_no_transitivity_evidence_without_compositions(mining):
    insert(mining, [(EX[f's{i}'], EX.p, EX[f'o{i}']) for i in range(6)])
    mining['class_instances'] = {}
    run_cell(mining, 14)
    assert mining['property_profiles'][str(EX.p)]['rho_trans'] == 0
    run_cell(mining, 18)
    assert not mining['adjudicated_property_characteristics'][str(EX.p)]


def test_transitivity_counts_cycle_self_compositions(mining):
    insert(mining, [(EX.a, EX.p, EX.b), (EX.b, EX.p, EX.a)])
    mining['class_instances'] = {}
    run_cell(mining, 14)
    assert mining['property_profiles'][str(EX.p)]['rho_trans'] == 0


def test_equivalence_participates_in_repair_and_recovery(mining):
    ns = mining
    ns.update(all_universe_classes=['A', 'B', 'C'],
              final_equivalences=[('A', 'B', .99)], entity_direct_types={'x': {'A'}},
              adjudicated_disjoint_pairs=[('B', 'C', .99, 3)],
              adjudicated_property_characteristics={}, adjudicated_subproperties=[],
              adjudicated_inverses=[], adjudicated_chains=[])
    ns['G_reduced'] = ns['nx'].DiGraph([('A', 'C')])
    run_cell(ns, 21)
    assert ns['inst_inferred_types']['x'] == {'A', 'B', 'C'}
    assert ns['clean_disjoint_pairs'] == []
    assert ns['dvc_pre'] == 1 and ns['DVC_POST'] == 0


def test_non_simple_roles_propagate_to_superproperties_and_inverses():
    chars, chains, rejected = repair_roles({'p': ['Transitive'], 'q': ['Functional'],
        'r': ['Asymmetric', 'Irreflexive']}, [{'sub': 'p', 'super': 'q'}],
        [{'p': 'q', 'q': 'r'}], [])
    assert chars == {'p': ['Transitive'], 'q': [], 'r': []}


def test_mutually_recursive_chain_dependencies_are_rejected():
    chains = [{'chain': ['p', 'q'], 'super': 'r'}, {'chain': ['r', 'q'], 'super': 'p'}]
    _, accepted, rejected = repair_roles({}, [], [], chains)
    assert len(accepted) == len(rejected) == 1


def test_complete_export_rejects_equivalence_disjointness_conflict():
    graph = Graph()
    for cls in (EX.A, EX.B):
        graph.add((cls, RDF.type, OWL.Class))
    graph.add((EX.A, OWL.equivalentClass, EX.B))
    graph.add((EX.A, OWL.disjointWith, EX.B))
    with pytest.raises(RuntimeError, match='unsatisfiable classes'):
        validate_export(graph)


def test_complete_export_checks_training_assertions():
    graph = Graph()
    for cls in (EX.A, EX.B):
        graph.add((cls, RDF.type, OWL.Class))
    graph.add((EX.A, OWL.disjointWith, EX.B))
    assert validate_export(graph)['tbox_coherent']
    abox = Graph()
    abox.add((EX.x, RDF.type, EX.A))
    abox.add((EX.x, RDF.type, EX.B))
    with pytest.raises(RuntimeError, match='TBox \\+ training ABox'):
        validate_export(graph, abox)


def test_export_rejects_inherited_non_simple_characteristic():
    graph = Graph()
    for prop in (EX.p, EX.q):
        graph.add((prop, RDF.type, OWL.ObjectProperty))
    graph.add((EX.p, RDF.type, OWL.TransitiveProperty))
    graph.add((EX.p, RDFS.subPropertyOf, EX.q))
    graph.add((EX.q, RDF.type, OWL.FunctionalProperty))
    with pytest.raises(ValueError, match='Non-simple property'):
        validate_export(graph)


def test_failed_validation_preserves_existing_export(mining, tmp_path):
    ns = mining
    target = tmp_path / 'existing.ttl'
    target.write_text('previous output')
    ns['config']['TBOX_PATH'] = str(target)
    graph = Graph()
    for cls in (EX.A, EX.B):
        graph.add((cls, RDF.type, OWL.Class))
    graph.add((EX.A, OWL.equivalentClass, EX.B))
    graph.add((EX.A, OWL.disjointWith, EX.B))
    ns.update(g_tbox=graph, training_graph=Graph(), induced_classes={})
    with pytest.raises(RuntimeError):
        run_cell(ns, 25)
    assert target.read_text() == 'previous output'


def test_missing_reasoner_fails_closed(monkeypatch):
    import pipeline_support
    def unavailable(*args, **kwargs):
        raise FileNotFoundError('java unavailable')
    monkeypatch.setattr(pipeline_support.owlready2, 'sync_reasoner_hermit', unavailable)
    with pytest.raises(RuntimeError, match='java unavailable'):
        validate_export(Graph())


def test_role_and_type_recovery_uses_equivalence_and_role_rules():
    closure = class_closure(['A', 'B', 'C'], [('B', 'C')], [('A', 'B', 1)])
    types, edges = recover_assertions({'x': {'A'}}, {'p': {('x', 'y')}, 'q': {('y', 'z')}},
        closure, [{'sub': 'p', 'super': 's'}], [{'p': 'p', 'q': 'inv'}],
        [{'chain': ['p', 'q'], 'super': 'r'}], {}, {'r': 'A'}, {'r': 'B'})
    assert edges['s'] == {('x', 'y')}
    assert edges['inv'] == {('y', 'x')}
    assert edges['r'] == {('x', 'z')}
    assert types['x'] == types['z'] == {'A', 'B', 'C'}


def test_calibration_includes_probability_one_and_requires_gold():
    predictions = {('A', 'B'): 1, ('B', 'C'): 0}
    assert calibration_metrics(predictions, {}) == {'ece': None, 'brier': None, 'count': 0, 'bins': []}
    result = calibration_metrics(predictions, {('A', 'B'): 0, ('B', 'C'): 1})
    assert result['ece'] == result['brier'] == 1
    assert result['count'] == sum(b['count'] for b in result['bins']) == 2


def config(**changes):
    return {'USE_LLM': True, 'OLLAMA_BASE_URL': 'http://test.invalid', 'MODEL_DECISION': 'test',
            'MAX_DECISION_PAIRS': 10, 'MAX_LLM_PAIRS': 10, 'MAX_PAYLOAD_TOKENS': 1500,
            'LLM_TIMEOUT_S': 2, 'LLM_MAX_CONSECUTIVE_ERRORS': 2, 'SYSTEMONE_BATCH_SIZE': 3, **changes}


def response(answers, chat=False):
    body = {'message': {'content': json.dumps({'answers': answers})}, 'prompt_eval_count': 25} if chat else {
        'answers': answers, 'usage': {'input_tokens': 25}}
    return io.BytesIO(json.dumps(body).encode())


def test_chat_emulation_performs_actual_adjudication():
    calls = []
    def opener(request, timeout):
        calls.append(request.full_url)
        if request.full_url.endswith('/v1/systemone'):
            raise OSError('unsupported endpoint')
        questions = json.loads(json.loads(request.data)['messages'][1]['content'])['questions']
        if 'ready' in questions:
            return response({'ready': {'noul': 1}}, chat=True)
        return response({'valid': {'noul': .99}, 'necessity': {'score': 3}}, chat=True)
    transport = DecisionTransport(config(), [], opener)
    transport.connect()
    assert transport.tier == 'chat_emulated'
    assert confirm_axiom(transport, {'proposed': 'test'}, 'test')
    assert calls == ['http://test.invalid/v1/systemone', 'http://test.invalid/api/chat', 'http://test.invalid/api/chat']


def test_request_budget_skips_oversized_payload_before_network():
    def opener(*args, **kwargs):
        pytest.fail('Oversized request reached network')
    audit = []
    transport = DecisionTransport(config(), audit, opener)
    transport.tier = 'native_http'
    assert transport.ask({'data': 'x' * 2000}, {}, 'test') == {}
    assert audit[-1]['status'] == 'skipped_budget'
    assert audit[-1]['input_tokens'] is None


@pytest.mark.parametrize('limit', ['MAX_DECISION_PAIRS', 'MAX_LLM_PAIRS'])
def test_decision_limits_are_enforced(limit):
    calls = []
    def opener(*args, **kwargs):
        calls.append(1)
        return response({'valid': {'noul': .5}})
    transport = DecisionTransport(config(**{limit: 1}), [], opener)
    transport.tier = 'native_http'
    for _ in range(3):
        transport.ask({}, {}, 'test')
    assert len(calls) == 1


def test_repeated_errors_open_circuit_and_never_confirm():
    calls = []
    def opener(*args, **kwargs):
        calls.append(1)
        raise TimeoutError('timeout')
    audit = []
    transport = DecisionTransport(config(), audit, opener)
    transport.tier = 'native_http'
    for _ in range(5):
        assert not confirm_axiom(transport, {}, 'test')
    assert len(calls) == 2
    assert all(e['status'] == 'error' for e in audit)


@pytest.mark.parametrize('answer', [{}, {'noul': float('nan')}, {'noul': 2}, {'noul': 'bad'}, {'noul': True}])
def test_malformed_model_values_are_rejected(answer):
    assert number(answer, 'noul') is None


def test_offline_probe_does_not_fabricate_calls():
    audit = []
    transport = DecisionTransport(config(USE_LLM=False), audit)
    transport.connect()
    assert transport.tier == 'statistical' and audit == []


def test_reported_token_overrun_disables_transport():
    calls = []
    def opener(*args, **kwargs):
        calls.append(1)
        return io.BytesIO(json.dumps({'answers': {'valid': {'noul': 1}},
                                     'usage': {'input_tokens': 2000}}).encode())
    audit = []
    transport = DecisionTransport(config(), audit, opener)
    transport.tier = 'native_http'
    assert not transport.ask({}, {}, 'test')
    assert not transport.ask({}, {}, 'test')
    assert len(calls) == 1 and audit[0]['input_tokens'] == 2000
    assert audit[0]['status'] == 'error'


def test_cooccurrence_does_not_create_equivalence(mining):
    rows = [(EX[f'x{i}'], RDF.type, cls) for i in range(8) for cls in (EX.A, EX.B)]
    insert(mining, rows)
    mining['induced_class_uris'] = set()
    run_cell(mining, 13)
    run_cell(mining, 16)
    assert not mining['adjudicated_equivalences']
    assert not mining['adjudicated_subsumptions']


def test_mining_never_reads_held_out_assertions(monkeypatch, tmp_path):
    monkeypatch.setenv('USE_LLM', 'false')
    monkeypatch.setenv('ABOX_INPUT_PATH', str(ROOT / 'input/ABox.ttl'))
    monkeypatch.setenv('TBOX_OUTPUT_PATH', str(tmp_path / 'TBox.ttl'))
    ns = {}
    for index in (3, 4, 5, 7):
        run_cell(ns, index)
    for entity, cls in ns['held_out_type_assertions']:
        assert (URIRef(entity), RDF.type, URIRef(cls)) not in ns['training_graph']
    for s, p, o in ns['held_out_role_assertions']:
        assert (URIRef(s), URIRef(p), URIRef(o)) not in ns['training_graph']
    class ForbiddenHoldout:
        def __iter__(self):
            raise AssertionError('Mining inspected held-out labels')
        def __len__(self):
            raise AssertionError('Mining inspected held-out labels')
        def __getitem__(self, key):
            raise AssertionError('Mining inspected held-out labels')
    ns['held_out_type_assertions'] = ForbiddenHoldout()
    ns['held_out_role_assertions'] = ForbiddenHoldout()
    ns['entity_types_map'] = ForbiddenHoldout()
    try:
        for index in (8, 10, 11, 13, 14, 16, 17, 18, 20, 21, 22, 24, 25):
            run_cell(ns, index)
        assert ns['VALIDATION_REPORT']['status'] == 'passed'
    finally:
        ns['conn'].close()


def test_holdout_split_reproducible_across_hash_seeds(tmp_path):
    script = '''import json
from pathlib import Path
cells=json.loads(Path('abox2tbox.ipynb').read_text())['cells']
ns={}
for i in (3,4,5,7): exec(''.join(cells[i]['source']),ns)
print(json.dumps([ns['held_out_type_assertions'],ns['held_out_role_assertions']],sort_keys=True))
'''
    outputs = []
    for seed in ('1', '2'):
        env = {**os.environ, 'USE_LLM': 'false', 'PYTHONHASHSEED': seed,
               'ABOX_INPUT_PATH': str(ROOT / 'input/ABox.ttl')}
        result = subprocess.run([sys.executable, '-c', script], cwd=ROOT, env=env,
                                 text=True, capture_output=True, check=True, timeout=30)
        outputs.append(result.stdout.splitlines()[-1])
    assert outputs[0] == outputs[1]


def test_generator_matches_notebook_without_executing_it(tmp_path):
    subprocess.run([sys.executable, str(ROOT / 'build_notebook.py')], cwd=tmp_path, check=True)
    generated = json.loads((tmp_path / 'abox2tbox.ipynb').read_text())
    assert generated['cells'] == CELLS
