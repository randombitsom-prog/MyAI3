#!/usr/bin/env python3
"""
Utility script to download a public Google Sheet as CSV and save it locally.

Usage:
    python scripts/download_public_sheet.py --sheet-id SHEET_ID [--gid TAB_GID] [--output data.csv]

The sheet must be publicly accessible (anyone with the link can view). If the sheet
has multiple tabs, pass the specific tab's gid to download that tab; otherwise the
first tab is exported.
"""
import argparse
import csv
import sys
from io import StringIO
from typing import Optional

import requests


def download_sheet(sheet_id: str, gid: Optional[str] = None) -> str:
    base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export"
    params = {"format": "csv"}
    if gid:
        params["gid"] = gid

    resp = requests.get(base_url, params=params, timeout=60)
    resp.raise_for_status()
    return resp.text


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a public Google Sheet as CSV.")
    parser.add_argument("--sheet-id", required=True, help="Google Sheet ID (from the URL)")
    parser.add_argument("--gid", help="Optional tab gid if you need a specific sheet tab")
    parser.add_argument(
        "--output",
        help="Path to save the CSV output. If not provided, files will be named after tab names.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print the first few rows instead of saving (useful for testing)",
    )
    parser.add_argument(
        "--all-tabs",
        action="store_true",
        help="Download all tabs in the spreadsheet (requires Google Sheets API parameters).",
    )
    parser.add_argument(
        "--tabs",
        help="Optional comma-separated list of tab names (used when --all-tabs is set).",
    )

    args = parser.parse_args()

    if args.all_tabs:
        # Expect user to provide tab gids/names via --tabs in format name:gid
        if not args.tabs:
            print(
                "When using --all-tabs, provide --tabs \"Tab Name 1:gid1,Tab Name 2:gid2\"",
                file=sys.stderr,
            )
            sys.exit(1)

        for tab in args.tabs.split(","):
            name_gid = tab.strip().split(":")
            if len(name_gid) != 2:
                print(f"Invalid tab format: {tab}", file=sys.stderr)
                continue
            tab_name, gid = name_gid
            try:
                csv_text = download_sheet(args.sheet_id, gid)
            except requests.RequestException as exc:
                print(f"Failed to download tab {tab_name}: {exc}", file=sys.stderr)
                continue

            output_path = args.output or f"data/{tab_name.strip().replace(' ', '_')}.csv"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(csv_text)
            print(f"Tab '{tab_name}' saved to {output_path}")
        return

    try:
        csv_text = download_sheet(args.sheet_id, args.gid)
    except requests.RequestException as exc:
        print(f"Failed to download sheet: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.preview:
        reader = csv.DictReader(StringIO(csv_text))
        rows = list(reader)
        print(f"Total rows: {len(rows)}")
        for row in rows[:5]:
            print(row)
        return

    output_path = args.output or "data/bitcom_google_sheet.csv"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(csv_text)

    print(f"Sheet saved to {output_path}")


if __name__ == "__main__":
    main()

