import numpy as np, pandas as pd, pyarrow as pa, pyarrow.compute as pc, pyarrow.parquet as pq
from ber.block.text import fold
from ber.paths import records_path
from post_ops import name_edit, addr_parts, same_address, tokens, LEG, STOP


def load_text(split, eids):
    eids = np.unique(np.asarray(eids, np.int64))
    f = pq.ParquetFile(records_path(split))
    out = []
    vs = pa.array(eids)
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=["eid", "country", "name", "address"])
        t = t.filter(pc.is_in(t["eid"], value_set=vs))
        if t.num_rows:
            out.append(pd.DataFrame({"eid": t["eid"].to_numpy(),
                                     "name": fold(t["name"].combine_chunks()).to_numpy(zero_copy_only=False),
                                     "address": fold(t["address"].combine_chunks()).to_numpy(zero_copy_only=False)}))
    d = pd.concat(out, ignore_index=True).set_index("eid")
    d["name"] = d.name.fillna("")
    d["address"] = d.address.fillna("")
    return d


def pair_rel(d, txt):
    """name kind + address relation for pairs d(s1, r)."""
    ns, nr = txt.name.reindex(d.s1).to_numpy(), txt.name.reindex(d.r).to_numpy()
    a_s, a_r = txt.address.reindex(d.s1).to_numpy(), txt.address.reindex(d.r).to_numpy()
    kind = [name_edit(a or "", b or "")[0] for a, b in zip(ns, nr)]
    ps = [addr_parts(a or "") for a in a_s]
    pr = [addr_parts(a or "") for a in a_r]
    same_num = np.array([bool(x[0]) and x[0] == y[0] for x, y in zip(ps, pr)])
    same_addr = np.array([same_address(x, y) for x, y in zip(ps, pr)])
    full_street = np.array([bool(x[1]) and x[1] == y[1] for x, y in zip(ps, pr)])
    r_empty = np.array([not (b or "").strip() or b.strip() == "null" for b in a_r])
    return d.assign(kind=kind, same_num=same_num, same_addr=same_addr, full_street=full_street, r_addr_empty=r_empty)
