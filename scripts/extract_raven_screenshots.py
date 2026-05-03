"""
Extract screenshots from a Shodan or FOFA JSON export to disk.

Usage:
    python scripts/extract_raven_screenshots.py <json_file> [output_dir]

Examples:
    python scripts/extract_raven_screenshots.py data/shodan_cameras.json
    python scripts/extract_raven_screenshots.py data/shodan_cameras.json data/screenshots
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.raven_ingest import load_raven_file
from modules.raven_matcher import filter_cameras
from modules.raven_media import extract_screenshots


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/extract_raven_screenshots.py <json_file> [output_dir]")
        sys.exit(1)

    json_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "data/screenshots"

    print(f"Loading {json_file}...")
    df = load_raven_file(json_file)

    if df.empty:
        print("No records found.")
        sys.exit(0)

    print(f"{len(df)} records loaded.")

    cam_df = filter_cameras(df)
    print(f"{len(cam_df)} camera devices identified.")

    if cam_df.empty:
        print("No camera devices to extract screenshots from.")
        sys.exit(0)

    result = extract_screenshots(cam_df, output_dir=output_dir)

    print(f"Extracted: {result['extracted']} screenshots → {result['output_dir']}")
    print(f"Skipped (no image): {result['skipped']}")
    if result["errors"] > 0:
        print(f"Errors: {result['errors']}")


if __name__ == "__main__":
    main()
