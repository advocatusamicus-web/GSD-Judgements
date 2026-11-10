#!/usr/bin/env python3
"""Discover Telangana metadata partitions and inspect their Parquet schemas.

This Phase 1 utility only accesses the public dataset's metadata/parquet objects.
It does not download judgment PDFs or scrape the court website.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import boto3
import pyarrow.parquet as pq
from botocore import UNSIGNED
from botocore.config import Config

BUCKET = "indian-high-court-judgments"
COURT_CODE = "36_29"  # Telangana High Court; source registry code is 36~29.
ROOT = Path(__file__).resolve().parents[1]


def s3_client():
    return boto3.client("s3", config=Config(signature_version=UNSIGNED), region_name="ap-south-1")


def find_parquet_objects(client, year: int) -> list[dict[str, Any]]:
    prefix = f"metadata/parquet/year={year}/court={COURT_CODE}/"
    found: list[dict[str, Any]] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for item in page.get("Contents", []):
            if item["Key"].lower().endswith(".parquet"):
                found.append(item)
    return sorted(found, key=lambda x: x["Key"])


def inspect_partition(client, year: int, obj: dict[str, Any], download: bool) -> dict[str, Any]:
    key = obj["Key"]
    result: dict[str, Any] = {
        "year": year,
        "key": key,
        "size_bytes": obj.get("Size"),
        "last_modified": obj.get("LastModified").isoformat() if obj.get("LastModified") else None,
    }
    if not download:
        result["inspection"] = "not downloaded (--list-only)"
        return result

    local_path = ROOT / "Metadata" / "parquet" / key.removeprefix("metadata/parquet/")
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if not local_path.exists() or local_path.stat().st_size != obj.get("Size"):
        print(f"Downloading metadata only: s3://{BUCKET}/{key} ({obj.get('Size', 0):,} bytes)")
        client.download_file(BUCKET, key, str(local_path))
    parquet = pq.ParquetFile(local_path)
    result.update({
        "local_path": str(local_path.relative_to(ROOT)),
        "row_count": parquet.metadata.num_rows,
        "row_group_count": parquet.metadata.num_row_groups,
        "schema": [
            {"name": field.name, "type": str(field.type), "nullable": field.nullable}
            for field in parquet.schema_arrow
        ],
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="+", type=int, default=[2019, 2020, 2021, 2022])
    parser.add_argument("--list-only", action="store_true", help="list exact S3 parquet keys/sizes without downloading")
    args = parser.parse_args()
    invalid = [year for year in args.years if year not in {2019, 2020, 2021, 2022}]
    if invalid:
        parser.error(f"years outside requested period: {invalid}")

    client = s3_client()
    report: dict[str, Any] = {
        "bucket": BUCKET,
        "court_code": "36~29",
        "s3_court_path": COURT_CODE,
        "years": {},
        "note": "Only public metadata Parquet objects are listed/downloaded; no PDFs are downloaded.",
    }
    for year in args.years:
        objects = find_parquet_objects(client, year)
        partitions = [inspect_partition(client, year, obj, not args.list_only) for obj in objects]
        report["years"][str(year)] = {
            "parquet_object_count": len(objects),
            "total_metadata_bytes": sum(obj.get("Size", 0) for obj in objects),
            "partitions": partitions,
        }
        if not objects:
            print(f"WARNING: no Parquet objects found for {year} at the expected court prefix", file=sys.stderr)

    output = ROOT / "Metadata" / "phase1_dataset_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        year: {
            "parquet_object_count": details["parquet_object_count"],
            "total_metadata_bytes": details["total_metadata_bytes"],
            "keys": [p["key"] for p in details["partitions"]],
            "schemas": sorted({tuple((f["name"], f["type"]) for f in p.get("schema", [])) for p in details["partitions"]}),
        }
        for year, details in report["years"].items()
    }, indent=2, default=list))
    print(f"Full Phase 1 report: {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - command-line diagnostic should be clear
        print(f"Phase 1 failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
