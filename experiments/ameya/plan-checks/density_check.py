"""Which kind of distractor grew in test? (train 4.68 S2/S3 per S1 -> test 5.75)

For a sample of R records per split and country, find the nearest S1 of the same split (rare-token retrieval,
nn_lib.nearest_s1) and bucket each R by how well that S1 agrees on name and address.
- more 'no close S1' in test -> the extra R are owner-less records (a drop-S1 stress test models this)
- same profile as train     -> more matches and/or more look-alikes per S1 (what we found: FINAL_PLAN section 1, #14)
Compare India: its train and test S1 pools are similar in size. The US pools differ 2x, which biases this proxy.
"""
import pandas as pd

from nn_lib import DC, log, nearest_s1, bucket

rows = []
for split in ("train", "test"):
    s1 = pd.read_parquet(f"{DC}/{split}_s1.parquet")
    R = pd.concat([pd.read_parquet(f"{DC}/{split}_s{s}.parquet") for s in (2, 3)], ignore_index=True)
    if split == "train":
        gt = pd.read_parquet(f"{DC}/train_gt.parquet")
        matched = gt.matched_entity_ids[gt.matched_entity_ids != ""].str.split(",").explode()
        R["orphan"] = ~R.entity_id.isin(matched)
    if split == "test":
        for name, df in (("S1", s1), ("R", R)):
            fr = df[df.country == "France"].business_address
            five = fr.str.contains(r"(?<!\d)\d{5}(?!\d)", regex=True).mean()
            log(f"France {name}: addresses with a 5-digit run (postcode-like) {five:.1%}; examples: "
                + " || ".join(fr.sample(6, random_state=4).tolist()))
    q = R.groupby("country", group_keys=False).sample(15_000, random_state=3).reset_index(drop=True)
    log(f"{split}: indexing {len(s1):,} S1, querying {len(q):,} R")
    top = nearest_s1(s1, q)
    q["bucket"] = bucket(s1, q, top)
    q["split"] = split
    rows.append(q)
    log(f"{split}: done")

allq = pd.concat(rows, ignore_index=True)
tab = pd.crosstab([allq.split, allq.country], allq.bucket, normalize="index").round(3)
log("share of sampled R records by closeness of their nearest S1 (same split, same country)\n" + tab.to_string())
tr = allq[allq.split == "train"]
tab2 = pd.crosstab([tr.country, tr.orphan], tr.bucket, normalize="index").round(3)
log("train only, split by orphan (True = matches no S1)\n" + tab2.to_string())
log("done")
