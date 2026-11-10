# Justice G. Sri Devi (Retired) — Telangana High Court judgments

This repository is being built in phases to collect and search public judicial records for **Hon'ble Justice G. Sri Devi (Retired), High Court for the State of Telangana**, for 15 May 2019–9 October 2022. It must not be conflated with Justice Juvvadi Sridevi. No claim of completeness is made.

## Phase 1 status: dataset structure and metadata schema

The Phase 1 utility discovers the actual public S3 Parquet keys under the Telangana dataset prefix for 2019–2022, records exact partition names and object sizes, and (unless `--list-only` is used) downloads only those metadata Parquet objects and reports their real Arrow schemas and row counts. It does **not** download judgment PDFs, scrape the court website, or use AWS credentials.

### Verified from source documentation (not from a live S3 execution)

- The dataset documentation describes `metadata/parquet/year=<YYYY>/court=<court_code>/bench=<bench_code>/metadata.parquet` and the public bucket `indian-high-court-judgments`.
- The dataset's own `high_courts.csv` identifies `High Court for State of Telangana` as `36_29`, bench `taphc`; the repository documentation says replace `~` with `_` for S3 paths.
- The source documentation warns that `pdf_link` is a storage pointer and recommends structured keys such as `(cnr, decision_date, order_number)` for deduplication.

The exact currently available S3 partitions and actual schema have **not yet been verified by running the script**. Run the commands below and inspect `Metadata/phase1_dataset_report.json` before any filtering or judgment download. The bucket is updated over time, so record the execution date with the report.

## macOS setup

1. Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/macos/) (or install Homebrew from [brew.sh](https://brew.sh/) and run `brew install python`).
2. In Terminal, clone this repository if it is not already on your Mac, then change into its directory:

   ```bash
   git clone https://github.com/advocatusamicus-web/GSD-Judgements.git
   cd GSD-Judgements
   ```

3. Install the isolated environment and packages:

   ```bash
   chmod +x setup_mac.sh
   ./setup_mac.sh
   source .venv/bin/activate
   ```

AWS CLI is **not required** for Phase 1; the Python script uses anonymous access to the public S3 bucket. No AWS credentials should be configured or committed.

## Phase 1 commands

List exact Parquet keys and object sizes without downloading metadata:

```bash
source .venv/bin/activate
python scripts/inspect_dataset.py --list-only
```

Download only the discovered metadata Parquet files and inspect schema/row counts (not PDFs):

```bash
python scripts/inspect_dataset.py
```

Inspect one year only:

```bash
python scripts/inspect_dataset.py --years 2021
```

The script writes `Metadata/phase1_dataset_report.json` (ignored by Git) and caches metadata under `Metadata/parquet/` (also ignored). If the script errors, preserve the diagnostic and report; do not guess at paths or schema. Metadata object sizes are printed and included in the report before or as each metadata object is downloaded.

## Execution boundaries

GitHub Copilot can add project files to this repository but cannot run them on your Mac or inspect your local filesystem. The commands above must be executed in a configured local environment (or another environment you control with network access). No live S3 request, schema inspection, judgment identification, PDF download, or Excel generation has been run as part of this initial Phase 1 setup. Do not start a large PDF download until candidate counts and estimated storage are reported and you explicitly confirm.

## Planned phases

1. Verify actual partitions and metadata schema (current phase).
2. Normalize judge/bench fields, identify candidates, provide year-wise preliminary counts, and separate ambiguous identities for manual review.
3. Test up to 10 confirmed PDFs, check PDF integrity, and report estimated storage before asking before a larger download.
4. Implement resumable selective downloads with checksums, retries, deduplication, and an attempt manifest.
5. Generate the Excel index, local searchable application, and coverage report with limitations clearly stated.

Never commit judgment PDFs, large datasets, generated indexes, or credentials to this repository.
