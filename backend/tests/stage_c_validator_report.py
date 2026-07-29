"""Measure the Stage C 'ready-made' validator against the labeled set.
Reports confusion matrix + false positives/negatives. Run before AND after refining.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from stage_c_validator_cases import CASES


def flagged_readymade(draft, student):
    # target/dependency irrelevant to the ready-made check; use a neutral target.
    _ok, issues, _t, _d = server._validate_coaching(draft, "thesis", "", False, student)
    return any("ready-made" in i for i in issues)


def main():
    tp = fp = tn = fn = 0
    fps, fns = [], []
    for c in CASES:
        got = flagged_readymade(c["draft"], c["student"])
        exp = c["should_flag"]
        if exp and got:
            tp += 1
        elif exp and not got:
            fn += 1; fns.append(c)
        elif not exp and got:
            fp += 1; fps.append(c)
        else:
            tn += 1
    n = len(CASES)
    should_flag = sum(1 for c in CASES if c["should_flag"])
    print(f"cases={n}  should_flag={should_flag}  should_pass={n-should_flag}")
    print(f"TP={tp} FN={fn} | TN={tn} FP={fp}")
    print(f"false_positive_rate={fp}/{n-should_flag}  false_negative_rate={fn}/{should_flag}")
    if fps:
        print("FALSE POSITIVES (acceptable scaffolds wrongly flagged):")
        for c in fps:
            print(f"  - {c['id']} [{c['category']}]")
    if fns:
        print("FALSE NEGATIVES (genuine ready-made missed):")
        for c in fns:
            print(f"  - {c['id']} [{c['category']}]")


if __name__ == "__main__":
    main()
