"""Offline audit integrity checks; optional local Git reads, never reference execution."""

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
PINS = {
    "target_base": "b24ef18e4270af5ab4f731aca31cf95f4f4b0cce",
    "pr8_head": "e4361678ed176cbd7c0bb6f838d3daa7174caf22",
    "pr9_head": "6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5",
    "hoya_head": "0e9c589c1b83027146f909a9cdc306c2c665ceaf",
    "initial_ai_commit": "c1006caadfd7b47d528ab466338da223aa79dd8e",
    "carrot_wip_head": "f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
    "previous_carrot_wip": "bfc3ebb44f24e99e2d46e65ef091c4cf27627be9",
}
CONFIDENCE = {"PROVEN", "CONDITIONAL", "HEURISTIC", "UNRESOLVED", "REJECTED"}
DECISIONS = {"ADOPT", "ADOPT_WITH_STRONGER_CONTRACT", "REFERENCE_ONLY", "REJECT", "DEFER"}
EPISODES = {
    "departure_start",
    "harsh_catchup_accel",
    "harsh_decel",
    "steering_tracking_error",
    "curve_speed_mismatch",
    "driver_brake_override",
    "driver_gas_override",
    "driver_steer_override",
}
SCORES = {
    "architectural_value",
    "evidence_quality",
    "safety_compatibility",
    "reuse_value",
    "implementation_coupling",
    "risk",
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def hex_id(value, length):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{" + str(length) + "}", value) is not None


def source_inventory(file_id, data):
    """Inventory every zero/False getattr default and pass-only Python handler."""
    tree = ast.parse(data.decode("utf-8"))
    defaults, handlers = [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "getattr" and len(node.args) == 3:
                default = node.args[2]
                if isinstance(default, ast.Constant) and (
                    default.value is False
                    or type(default.value) in (int, float)
                    and default.value == 0
                ):
                    field = node.args[1]
                    defaults.append(
                        {
                            "file": file_id,
                            "line": node.lineno,
                            "end": node.end_lineno,
                            "field": field.value if isinstance(field, ast.Constant) else "dynamic",
                            "default_kind": "FALSE" if default.value is False else "ZERO",
                            "verdict": "UNAVAILABLE_COLLAPSED",
                        }
                    )
        if isinstance(node, ast.ExceptHandler) and len(node.body) == 1:
            if isinstance(node.body[0], ast.Pass):
                handlers.append(
                    {
                        "file": file_id,
                        "line": node.lineno,
                        "end": node.end_lineno,
                        "verdict": "ERROR_SUPPRESSED_NOT_VALIDITY",
                    }
                )
    return sorted(defaults, key=lambda x: (x["line"], x["field"])), sorted(
        handlers, key=lambda x: x["line"]
    )


def validate(sources, features):
    require(sources["schema_version"] == features["schema_version"] == 1, "unsupported schema")
    require(sources["pins"] == PINS, "pin mismatch")
    require(sources["scope"] == features["scope"] == "DESIGN_AUDIT_ONLY", "scope mismatch")
    require(sources["copied_source_bodies"] is False, "source copying forbidden")
    files, refs = {}, set()
    for item in sources["files"]:
        require(item["id"] not in files, "duplicate file")
        files[item["id"]] = item
        require(hex_id(item["commit"], 40) and hex_id(item["blob_sha"], 40), "bad Git identity")
        require(
            item["commit"] == PINS["hoya_head"]
            if item["repository"] == "ajouatom/openpilot"
            else item["repository"] == "rownlvh8875-coder/cyberpilot-autotune"
            and item["commit"] in {PINS["target_base"], PINS["pr8_head"], PINS["pr9_head"]},
            "source outside pinned audit scope",
        )
        require(hex_id(item["sha256"], 64), "bad source digest")
        path = PurePosixPath(item["path"])
        require(not path.is_absolute() and ".." not in path.parts, "invalid source path")
        require(type(item["line_count"]) is int and item["line_count"] > 0, "invalid source size")
        for span in item["ranges"]:
            require(span["id"] not in refs, "duplicate evidence id")
            refs.add(span["id"])
            require(type(span["start"]) is type(span["end"]) is int, "invalid range type")
            require(1 <= span["start"] <= span["end"] <= item["line_count"], "invalid range")
            require(hex_id(span["sha256"], 64), "bad range digest")
            require(span["confidence"] in CONFIDENCE, "invalid confidence")
            require(bool(span["symbol"]) and bool(span["claim"]), "missing semantic evidence")
    require(set(sources["required_files"]) <= files.keys(), "required source absent")
    require(
        features["application_architecture"] == "APPLICATION_ARCHITECTURE_REJECTED", "unsafe apply"
    )
    require(features["advisory_authority"] == "ADVISORY_ONLY", "unsafe advisory authority")
    require(features["external_ai"] == "NOT_AUTHORIZED", "external AI not authorized")
    require(features["runtime_fingerprint"] == "UNCONFIRMED", "unproven fingerprint")
    require(features["episode_design_status"] == "EPISODE_OBSERVER_DESIGN_READY", "design status")
    require(
        features["supervisor_design_status"] == "AUTOTUNE_SUPERVISOR_DESIGN_READY", "design status"
    )
    require({x["name"] for x in features["episodes"]} == EPISODES, "incomplete episode inventory")
    require(len(features["episodes"]) == len(EPISODES), "duplicate episode")
    for episode in features["episodes"]:
        require(episode["threshold_role"] == "DIAGNOSTIC_HEURISTIC_ONLY", "unsafe threshold")
        for key in (
            "formula",
            "units",
            "override",
            "false_positive",
            "false_negative",
            "cohort_risk",
        ):
            require(bool(episode[key]), "incomplete episode analysis")
        if episode["name"].startswith("driver_"):
            require(episode["observed_fact"] == "DRIVER_INPUT_TRANSITION", "unsupported inference")
    names = [p["name"] for p in features["parameters"]]
    require(len(names) == len(set(names)), "duplicate parameter")
    require(set(names) == set(sources["named_parameter_universe"]), "unclassified parameter")
    for parameter in features["parameters"]:
        require(parameter["application_authorized"] is False, "parameter authority forbidden")
        require(parameter["ui_metadata_role"] == "DESCRIPTIVE_ONLY", "UI range is not policy")
        require(
            parameter["classification"]
            in {
                "DIAGNOSTIC_ONLY",
                "FUTURE_LONGITUDINAL_RESEARCH",
                "FUTURE_LATERAL_RESEARCH",
                "POTENTIAL_APPLICATION_FAMILY",
                "USER_PREFERENCE",
                "SAFETY_SENSITIVE",
                "NOT_SUITABLE",
                "UNRESOLVED",
            },
            "invalid parameter classification",
        )
    require(
        {p["name"] for p in features["providers"]}
        == {
            "free",
            "gemini",
            "openai",
            "claude",
            "grok",
            "custom",
        },
        "provider inventory",
    )
    for record in features["adoption"]:
        require(record["decision"] in DECISIONS, "invalid adoption decision")
    by_concept = {record["concept"]: record["decision"] for record in features["adoption"]}
    for concept, decision in {
        "Apply endpoint": "REJECT",
        "automatic dissatisfaction label": "REJECT",
        "latest-value log join": "REJECT",
        "external LLM recommender": "DEFER",
        "longitudinal taxonomy": "DEFER",
    }.items():
        require(by_concept.get(concept) == decision, "unsafe concept promotion")
    for record in features["scores"]:
        for key in SCORES:
            require(type(record[key]) is int and 0 <= record[key] <= 5, "invalid score")
    for group in (
        "adoption",
        "episodes",
        "parameters",
        "providers",
        "apply_requirements",
        "scores",
        "source_grounding_checks",
        "additional_catalog_parameters",
    ):
        for record in features[group]:
            require(bool(record["evidence"]) and set(record["evidence"]) <= refs, "dangling claim")
    for group in ("getattr_defaults", "silent_handlers"):
        for site in sources["inventory"][group]:
            require(site["file"] in files, "unknown inventory source")
            require(
                1 <= site["line"] <= site["end"] <= files[site["file"]]["line_count"], "bad site"
            )
    catalog_names = {p["name"] for p in features["additional_catalog_parameters"]}
    require(
        catalog_names == set(sources["catalog_other_names"]), "incomplete catalog classification"
    )
    require(
        len(catalog_names) == len(features["additional_catalog_parameters"]), "duplicate catalog"
    )
    complete_catalog = catalog_names | {
        p["name"] for p in features["parameters"] if p["catalog_present"]
    }
    require(len(complete_catalog) == sources["catalog_parameter_count"], "catalog count mismatch")
    encoded_names = json.dumps(sorted(complete_catalog), separators=(",", ":")).encode()
    require(
        hashlib.sha256(encoded_names).hexdigest() == sources["catalog_parameter_names_sha256"],
        "catalog name digest mismatch",
    )
    for record in features["additional_catalog_parameters"]:
        require(record["classification"] == "UNRESOLVED", "unreviewed catalog authority")
        require(record["application_authorized"] is False, "catalog authority forbidden")
    require(len(sources["source_grounding_pairs"]) >= 15, "snippet comparison missing")
    require(len(features["apply_requirements"]) >= 22, "incomplete apply comparison")
    return {
        "files": len(files),
        "ranges": len(refs),
        "episodes": len(EPISODES),
        "providers": len(features["providers"]),
        "parameters": len(names),
        "application_authority": False,
    }


def verify_blob(item, data):
    require(hashlib.sha256(data).hexdigest() == item["sha256"], "source hash mismatch")
    header = b"blob " + str(len(data)).encode() + b"\0"
    require(hashlib.sha1(header + data).hexdigest() == item["blob_sha"], "Git blob mismatch")
    lines = data.splitlines(keepends=True)
    require(len(lines) == item["line_count"], "source size mismatch")
    for span in item["ranges"]:
        block = b"".join(lines[span["start"] - 1 : span["end"]])
        require(hashlib.sha256(block).hexdigest() == span["sha256"], "evidence range mismatch")


def normalized_line(line):
    # Comparison of this synopsis's commented statements only, never execution.
    return "".join(line.lstrip().removeprefix("#").split("#", 1)[0].split()).encode()


def verify_local_sources(sources, reference, target):
    blobs = {}
    environment = dict(os.environ, GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")
    for item in sources["files"]:
        checkout = reference if item["repository"] == "ajouatom/openpilot" else target
        data = subprocess.check_output(
            [
                "git",
                "-c",
                f"safe.directory={checkout}",
                "show",
                item["commit"] + ":" + item["path"],
            ],
            cwd=checkout,
            env=environment,
            stderr=subprocess.DEVNULL,
        )
        verify_blob(item, data)
        blobs[item["id"]] = data
    defaults, handlers = [], []
    for file_id in sources["inventory"]["python_scope"]:
        d, h = source_inventory(file_id, blobs[file_id])
        defaults.extend(d)
        handlers.extend(h)
    require(defaults == sources["inventory"]["getattr_defaults"], "default inventory mismatch")
    require(handlers == sources["inventory"]["silent_handlers"], "exception inventory mismatch")
    for pair in sources["source_grounding_pairs"]:
        left = normalized_line(blobs["autotune"].decode().splitlines()[pair["snippet_line"] - 1])
        right = normalized_line(blobs[pair["file"]].decode().splitlines()[pair["source_line"] - 1])
        require((left == right) is pair["equal"], "snippet comparison mismatch")
        require(
            hashlib.sha256(left).hexdigest() == pair["snippet_normalized_sha256"], "snippet hash"
        )
        require(
            hashlib.sha256(right).hexdigest() == pair["source_normalized_sha256"], "consumer hash"
        )
    return len(blobs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-checkout", type=Path)
    parser.add_argument("--target-checkout", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        directory = ROOT / "docs/evidence"
        sources, features = [
            json.loads((directory / name).read_text(encoding="utf-8"))
            for name in (
                "hoya_c3_atune_sources.json",
                "hoya_c3_atune_features.json",
            )
        ]
        result = validate(sources, features)
        result["raw_blobs_verified"] = 0
        if args.reference_checkout is not None:
            result["raw_blobs_verified"] = verify_local_sources(
                sources, args.reference_checkout, args.target_checkout
            )
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError):
        print('{"error":"AUDIT_EVIDENCE_INVALID"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
