"""Audit-only metadata/Git verification; never imports or runs reference code."""

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from cyberpilot_autotune.knowledge.canonical import canonical_bytes
from cyberpilot_autotune.knowledge.steering import CATALOGS

ROOT = Path(__file__).resolve().parents[2]
PINS = {
    "hoya": "0e9c589c1b83027146f909a9cdc306c2c665ceaf",
    "runtime": "c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
    "upstream": "f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
}
INTEGRATION = "7a2f051b1f3847786318900444c88c2ba7a74a67"
COMPATIBILITY = {
    "LateralTorqueAccelFactor": "CONDITIONAL",
    "LateralTorqueFriction": "CONDITIONAL",
    "LateralTorqueKpV": "SEMANTICALLY_EQUIVALENT",
    "LateralTorqueKiV": "SEMANTICALLY_EQUIVALENT",
    "LateralTorqueKf": "SEMANTICALLY_EQUIVALENT",
    "LateralTorqueCustom": "SEMANTICALLY_EQUIVALENT",
    "SteerRatioRate": "DRIFTED",
    "SteerActuatorDelay": "DRIFTED",
    "liveTorqueParameters.latAccelOffset": "UNRESOLVED",
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def projection(value):
    return json.loads(canonical_bytes(value))


def validate(sources, catalog):
    require(sources["schema_version"] == catalog["schema_version"] == 1, "schema")
    require(sources["pins"] == PINS, "exact source pins")
    require(sources["integration_revision"] == INTEGRATION, "integration pin")
    require(sources["target_base"] == "dd1d4232f3d151fe9bbf0808c1fbe5131618b09a", "base")
    require(sources["scope"] == "STEERING_DESCRIPTIVE_KNOWLEDGE_ONLY", "scope")
    require(sources["copied_source_bodies"] is False, "source bodies forbidden")
    require(catalog["application_registry"] is False, "not an application registry")
    files = {(x["exact_revision"], x["path"]): x for x in sources["files"]}
    require(len(files) == len(sources["files"]) == 39, "duplicate/incomplete file inventory")
    claims = {x["claim_id"]: x for x in sources["entries"]}
    require(len(claims) == len(sources["entries"]) == 78, "duplicate/incomplete claims")
    descriptors = {
        (x["source_role"], x["descriptor"]["parameter_id"]): x for x in catalog["entries"]
    }
    require(len(descriptors) == len(catalog["entries"]) == 27, "descriptor inventory")
    for role, revision in PINS.items():
        registry = next(r for r in CATALOGS if r.source_revision == revision)
        for claim in registry.claims:
            record = claims[claim.claim_id]
            require(record["source_role"] == role, "source role mixing")
            require(
                record["repository"]
                == ("rownlvh8875-coder/openpilot" if role == "runtime" else "ajouatom/openpilot"),
                "repository",
            )
            require(
                projection(claim) == {k: record[k] for k in projection(claim)},
                "altered source claim",
            )
            file = files[(revision, claim.path)]
            require(record["source_sha256"] == file["sha256"], "file digest mismatch")
            require(claim.git_blob_sha == file["git_blob_sha"], "blob digest mismatch")
            require(claim.range_end <= file["line_count"], "range outside file")
        for descriptor in registry.parameters:
            record = descriptors[(role, descriptor.parameter_id)]
            require(record["descriptor"] == projection(descriptor), "altered descriptor")
            require(record["descriptor_digest"] == descriptor.digest, "altered identity")
            require(
                record["compatibility_verdict"] == COMPATIBILITY[descriptor.parameter_id],
                "compatibility",
            )
            require(
                record["application_policy"] == "APPLICATION_POLICY_UNRESOLVED", "policy authority"
            )
    excluded = sources["excluded_parameters"]
    require(
        len(excluded) == 3 and {e["exact_revision"] for e in excluded} == set(PINS.values()),
        "exclusion inventory",
    )
    require(
        all(
            e["parameter_id"] == "CarSelected3"
            and e["classification"] == ["PLATFORM_SELECTOR", "NOT_SUITABLE"]
            for e in excluded
        ),
        "platform selector exclusion",
    )
    return {"files": len(files), "claims": len(claims), "descriptors": len(descriptors)}


def verify_blob(file, ranges, data):
    require(hashlib.sha256(data).hexdigest() == file["sha256"], "source SHA-256 mismatch")
    require(
        hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        == file["git_blob_sha"],
        "Git blob mismatch",
    )
    lines = data.splitlines(keepends=True)
    require(len(lines) == file["line_count"], "line count mismatch")
    for item in ranges:
        start, end = item["range_start"], item["range_end"]
        require(
            type(start) is type(end) is int and 1 <= start <= end <= len(lines),
            "invalid source range",
        )
        require(
            hashlib.sha256(b"".join(lines[start - 1 : end])).hexdigest()
            == item["source_range_sha256"],
            "source range mismatch",
        )


def verify_reference(sources, reference):
    def git(*args):
        return subprocess.check_output(
            ["git", "-C", str(reference), *args],
            env=os.environ | {"GIT_NO_LAZY_FETCH": "1", "GIT_TERMINAL_PROMPT": "0"},
            stderr=subprocess.PIPE,
        )

    require(
        git("rev-parse", f"{INTEGRATION}^{{tree}}")
        == git("rev-parse", f"{PINS['runtime']}^{{tree}}"),
        "integration tree mismatch",
    )
    for file in sources["files"]:
        revision, path = file["exact_revision"], file["path"]
        ranges = [
            e
            for e in sources["entries"] + sources["excluded_parameters"]
            if e["exact_revision"] == revision and e["path"] == path
        ]
        data = git("show", f"{revision}:{path}")
        verify_blob(file, ranges, data)
        registry = next(r for r in CATALOGS if r.source_revision == revision)
        if path.endswith("carrot_settings.json"):
            items = {p["name"]: p for p in json.loads(data)["params"]}
            for p in registry.parameters:
                if p.storage_key is not None:
                    require(
                        tuple(items[p.storage_key][k] for k in ("min", "max", "default"))
                        == (p.ui_catalog_min, p.ui_catalog_max, p.ui_default),
                        "UI metadata differs from source",
                    )
        if path.endswith("params_keys.h"):
            for p in registry.parameters:
                if p.storage_key is not None:
                    pattern = r'\{"' + re.escape(p.storage_key) + r'",\s*\{[^\n]+INT,\s*"(-?\d+)"'
                    match = re.search(pattern, data.decode("utf-8"))
                    require(
                        match is not None and int(match[1]) == p.storage_registry_default,
                        "native INT/default differs",
                    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-checkout", type=Path)
    args = parser.parse_args()
    sources, catalog = (
        json.loads((ROOT / "docs/evidence" / name).read_text(encoding="utf-8"))
        for name in ("steering_parameter_knowledge_sources.json", "steering_parameter_catalog.json")
    )
    result = validate(sources, catalog)
    if args.reference_checkout is not None:
        verify_reference(sources, args.reference_checkout)
    print(
        json.dumps(
            result | {"source_bytes_verified": args.reference_checkout is not None}, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
