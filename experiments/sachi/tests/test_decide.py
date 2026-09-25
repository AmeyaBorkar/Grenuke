import itertools, numpy as np, pandas as pd, pytest
from model.decide import (_expected_f_best_k, argmax_ownership, EvalIndex,
                          f_vector, paired_bootstrap)

def f_entity(pred, true):
    if not true: return 1.0 if not pred else 0.0
    if not pred: return 0.0
    c = len(pred & true); return 1.25 * c / (0.25 * len(true) + len(pred))

def brute_best_k(p):
    n = len(p); best = (-1, None)
    for k in range(n + 1):
        ev = 0.0
        for bits in itertools.product([0, 1], repeat=n):
            pr = np.prod([pi if b else 1 - pi for pi, b in zip(p, bits)])
            ev += pr * f_entity(set(range(k)), {i for i, b in enumerate(bits) if b})
        if ev > best[0] + 1e-12: best = (ev, k)
    return best[1]

@pytest.mark.parametrize("seed", range(40))
def test_dp_matches_bruteforce(seed):
    rng = np.random.default_rng(seed)
    p = np.sort(rng.random(rng.integers(1, 8)))[::-1].copy()
    assert _expected_f_best_k(p, 0.25) == brute_best_k(p)

def test_metric_and_singletons():
    truth = pd.DataFrame({"s1_eid": [1, 1, 2], "r_eid": [10, 11, 20]})
    ev = EvalIndex(np.array([1, 2, 3]), truth)
    pred = pd.DataFrame({"s1_eid": [1, 1, 1], "r_eid": [10, 11, 12]})
    f = f_vector(pred, ev)
    assert f[0] == pytest.approx(0.714, abs=1e-3)
    assert f[1] == 0.0 and f[2] == 1.0

def test_argmax_ownership():
    s = pd.DataFrame({"s1_eid": [1, 2, 2], "r_eid": [10, 10, 11], "p": [0.4, 0.9, 0.3]})
    o = argmax_ownership(s)
    assert set(zip(o.s1_eid, o.r_eid)) == {(2, 10), (2, 11)}

def test_bootstrap():
    rng = np.random.default_rng(0)
    a = rng.random(20000)
    assert paired_bootstrap(a, np.clip(a + 0.01, 0, 1))["keep"]
    assert not paired_bootstrap(a, a)["keep"]
