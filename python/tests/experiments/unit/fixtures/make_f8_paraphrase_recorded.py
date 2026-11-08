"""Build f8_paraphrase_recorded.json from an e2e evaluation regression truth record (no network, no model call).

    python make_f8_paraphrase_recorded.py <e2e>/truth/evaluation regression.json > f8_paraphrase_recorded.json

The row runs every F8 paraphrase pair (the 6 development pairs and held-out sets 1-3) through judge() on each model
in its F8_MODELS, then the criteria controls (CONTROL, CONTROL_HELD_OUT, CONTROL_HELD_OUT_2 and, from wave 2d,
CONTROL_HELD_OUT_3) once per control run ("default": judge(criteria) with no model=; then each named model), and
records each raw exchange (the request's system and user messages, the response body; no key, no headers), the judge's
one criteria read per criteria included. From wave 2d a row is judged part by part: the read splits the CRITERIA into
parts, and each part of each row is its own exchange. This keeps:
- records: the F8 guard model's exchanges for each paraphrase pair (``parts``: one per part), with the pair's must_pass;
- control_records: every control run's exchanges for each control pair, with its run, criteria and must_pass;
- criteria_reads: the F8 guard model's read of the paraphrase criteria, and each control run's read per criteria.
A part's exchange is found by its exact request, rebuilt with the SDK's own ``part_request`` from the recorded read, so
two criteria with the same OUTPUT never mix. From wave 2f a part the read marked as a count only (``counted_only``) is
decided by code and has no exchange; CONTROL_HELD_OUT_4 (rows with no expected) and CONTROL_HELD_OUT_5 (countable
criteria) are recorded too, and the misses kept are those of the recorded seed (seed 1; the lock's judge: unseeded);
from the L-SDK2f review fixes CONTROL_HELD_OUT_6 (the sentence counter's held-out set) too. The unit test replays them: the requests the SDK builds today must equal
the recorded ones byte for byte, and the recorded answers must give each pair's verdict."""

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
        if part.counted_only:  # decided by code (wave 2f): no exchange
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
    # from wave 2e the row runs every control on 6 seeds and records seed 1's exchanges (the lock's judge: its one
    # unseeded run); the misses kept here are those of the recorded run
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
