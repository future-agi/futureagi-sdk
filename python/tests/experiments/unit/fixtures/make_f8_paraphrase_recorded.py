"""Build f8_paraphrase_recorded.json from an e2e evaluation regression truth record (no network, no model call).

    python make_f8_paraphrase_recorded.py <e2e>/truth/evaluation regression.json > f8_paraphrase_recorded.json

The evaluation runs every F8 paraphrase pair (the 6 development pairs and held-out sets 1-3) through judge() on
each model in F8_MODELS and runs the criteria controls with the default judge and each named model. The fixture
records the system and user messages and response bodies, without credentials or headers. The judge reads each
criterion once to split it into parts, then requests a verdict for each part that requires model judgment.
The fixture keeps:
- records: the F8 guard model's exchanges for each paraphrase pair (``parts``: one per part), with the pair's must_pass;
- control_records: every control run's exchanges for each control pair, with its run, criteria and must_pass;
- criteria_reads: the F8 guard model's read of the paraphrase criteria, and each control run's read per criteria.
A part's exchange is found by its exact request, rebuilt with the SDK's own ``part_request`` from the recorded read, so
two criteria with the same OUTPUT are matched separately. A part marked as count only (``counted_only``) is
computed locally and has no exchange. The controls include CONTROL_HELD_OUT_4 (rows with no expected),
CONTROL_HELD_OUT_5 (countable criteria) and CONTROL_HELD_OUT_6 (held-out sentence counting cases). The fixture
keeps misses from seed 1 for seeded runs and from the unseeded run for the lock's judge. The replay test checks
that SDK requests match the recordings byte for byte and that recorded answers reproduce each pair's verdict."""

import json
import sys

from public_metadata import public_fixture

from fi.experiments.evaluators._judge_prompt import parse_parts, part_request

PARAPHRASE_CRITERIA = "Is the output a correct answer to the input?"


def _keep(x: dict) -> dict:
    return {"model": x["model"], "system": x["system"], "user": x["user"], "status": x["status"], "response": x["response"]}


def _reads(exchanges: list, criteria: list) -> dict:
    out = {}
    for c in criteria:
        found = [x for x in exchanges if x["user"] == f"CRITERIA:\n{c}"]
        assert found, ("no criteria read", c)
        out[c] = _keep(found[0])
    return out


def _parts_of(exchanges: list, read: dict, pair: dict) -> list:
    parts = parse_parts(read["response"]["choices"][0]["message"]["content"])
    out = []
    for part in parts:
        if part.counted_only:  # computed locally without a model request
            continue
        user = part_request(part, input_text=pair["input"], output_text=pair["answer"],
                            expected_text=pair.get("expected"))
        found = [x for x in exchanges if x["user"] == user]
        assert len(found) == 1, (pair["id"], part.part, len(found))
        out.append(_keep(found[0]))
    return out


def main(path: str) -> None:
    row = json.load(open(path, encoding="utf-8"))
    guard = row["f8_guard_model"].split("/", 1)[1]
    pairs = row["paraphrase_pairs"] + row["held_out_pairs"] + row["held_out_2_pairs"] + row["held_out_3_pairs"]
    exchanges = row["judge_recorded"][guard]
    reads = {guard: _reads(exchanges, [PARAPHRASE_CRITERIA])}
    records = []
    for pair in pairs:
        records.append({"id": pair["id"], "input": pair["input"], "expected": pair["expected"], "output": pair["answer"],
                        "must_pass": pair["must_pass"], "model": guard,
                        "parts": _parts_of(exchanges, reads[guard][PARAPHRASE_CRITERIA], pair)})
    controls = (row["control_pairs"] + row["control_held_out_pairs"] + row.get("control_held_out_2_pairs", [])
                + row.get("control_held_out_3_pairs", []) + row.get("control_held_out_4_pairs", [])
                + row.get("control_held_out_5_pairs", []) + row.get("control_held_out_6_pairs", []))
    control_records = []
    for run, seen in sorted(row["control_recorded"].items()):  # run: "default" or the model named
        reads.setdefault(run, {}).update(_reads(seen, list(dict.fromkeys(p["criteria"] for p in controls))))
        for pair in controls:
            read = reads[run][pair["criteria"]]
            parts = _parts_of(seen, read, pair)
            control_records.append({"id": pair["id"], "run": run, "criteria": pair["criteria"], "input": pair["input"],
                                    "expected": pair.get("expected"), "output": pair["answer"],
                                    "must_pass": pair["must_pass"], "model": (parts or [read])[0]["model"],
                                    "parts": parts})
    # The evaluation runs each seeded control on six seeds; keep the misses from seed 1, which is recorded.
    # For the lock's judge, keep the misses from its single unseeded run.
    recorded_run = {m: ("1" if "1" in by else "unseeded") for m, by in row["control_misses_by_model"].items()}
    out = {"provenance": {"record": "judge-paraphrase-and-criteria-regressions", "status": row["status"],
                          "date": row["date"],
                          "criteria": PARAPHRASE_CRITERIA, "model": guard,
                          "control_runs": sorted(row["control_recorded"]),
                          "failed_checks": sorted(a["id"] for a in row["assertions"] if a.get("pass") is False),
                          "f8_misses_by_model": {m: by.get("1", by.get("unseeded", [])) if isinstance(by, dict) else by
                                                 for m, by in row["f8_misses_by_model"].items()},
                          "control_misses_by_model": {m: row["control_misses_by_model"][m][sd]
                                                      for m, sd in recorded_run.items()},
                          "recorded_seed": recorded_run,
                          "note": "real model responses recorded by the row's transport (no key, no headers kept)"},
           "records": records, "control_records": control_records, "criteria_reads": reads}
    json.dump(public_fixture(out), sys.stdout, indent=1, sort_keys=True, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    if sys.argv[1] == "--public-fixture":
        with open(sys.argv[2], encoding="utf-8") as source:
            fixture = public_fixture(json.load(source))
        json.dump(fixture, sys.stdout, indent=1, sort_keys=True, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        main(sys.argv[1])
