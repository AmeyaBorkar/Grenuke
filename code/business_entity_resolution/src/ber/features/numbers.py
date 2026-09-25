"""Address-number set features over normalized-record list CSR arrays."""
from __future__ import annotations

from functools import lru_cache

import numpy as np


@lru_cache(maxsize=1)
def _kernel():
    from numba import njit, prange

    @njit(parallel=True)
    def calculate(offsets, values, left_rows, right_rows):
        result = np.empty((len(left_rows), 4), dtype=np.float32)
        for pair in prange(len(left_rows)):
            ls, le = offsets[left_rows[pair]], offsets[left_rows[pair] + 1]
            rs, re = offsets[right_rows[pair]], offsets[right_rows[pair] + 1]
            nl, nr, common = 0, 0, 0
            every_r_compatible = 1.0 if rs < re else np.nan
            for i in range(ls, le):
                a = values[i]
                duplicate = False
                for k in range(ls, i):
                    if values[k] == a:
                        duplicate = True
                        break
                if duplicate:
                    continue
                nl += 1
                for j in range(rs, re):
                    if values[j] == a:
                        common += 1
                        break
            for j in range(rs, re):
                b = values[j]
                duplicate = False
                for k in range(rs, j):
                    if values[k] == b:
                        duplicate = True
                        break
                if duplicate:
                    continue
                nr += 1
                compatible = False
                for i in range(ls, le):
                    a = values[i]
                    if a == b or (a >= 0 and b >= 0 and abs(a - b) <= 10):
                        compatible = True
                        break
                if not compatible:
                    every_r_compatible = 0.0
            union = nl + nr - common
            result[pair, 0] = common / union if union else np.nan
            result[pair, 1] = nl - common
            result[pair, 2] = nr - common
            result[pair, 3] = every_r_compatible
        return result

    return calculate


def number_features(offsets: np.ndarray, values: np.ndarray,
                    left_rows: np.ndarray, right_rows: np.ndarray) -> np.ndarray:
    return _kernel()(np.asarray(offsets, dtype=np.int64),
                     np.asarray(values, dtype=np.int64),
                     np.asarray(left_rows, dtype=np.int64),
                     np.asarray(right_rows, dtype=np.int64))
