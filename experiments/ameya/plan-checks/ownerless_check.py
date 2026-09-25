"""What would test look like if its extra R records were owner-less (Plan A's drop-20%-of-S1 stress test)?
India train only, because India's train and test S1 pools are similar in size (883k vs 810k)."""
import numpy as np
import pandas as pd
from nn_lib import DC, log, nearest_s1, bucket

s1 = pd.read_parquet(f"{DC}/train_s1.parquet")
s1 = s1[s1.country == "India"].reset_index(drop=True)
R = pd.concat([pd.read_parquet(f"{DC}/train_s{s}.parquet") for s in (2, 3)], ignore_index=True)
R = R[R.country == "India"].reset_index(drop=True)
gt = pd.read_parquet(f"{DC}/train_gt.parquet")
gt = gt[gt.matched_entity_ids != ""]
pairs = gt.assign(r=gt.matched_entity_ids.str.split(",")).explode("r")
owner = pairs.set_index("r").source1_entity_id
drop = np.random.default_rng(5).random(len(s1)) < 0.2
dropped = set(s1.entity_id[drop])
R["owner"] = R.entity_id.map(owner)
ownerless = R[R.owner.isin(dropped)].sample(15_000, random_state=6).reset_index(drop=True)
kept = s1[~drop].reset_index(drop=True)
log(f"India: {drop.sum():,} of {len(s1):,} S1 dropped; querying 15,000 R whose owner was dropped")
ownerless["bucket"] = bucket(kept, ownerless, nearest_s1(kept, ownerless))
log("owner-less R, nearest remaining S1:\n" + ownerless.bucket.value_counts(normalize=True).round(3).to_string())
log("done")
