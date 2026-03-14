"""
WRAITH — Shodan Camera Ingestion Script
==========================================
Author: Virtuvman | GitHub: https://github.com/Virtuvman
Version: 2.0
Purpose: Pull FOG IP camera data (or any camera type) from Shodan
         for any country, city, or lat/lon bounding box.
         Outputs a WRAITH-ready CSV file.

ETHICAL USE NOTICE:
  This script performs passive OSINT data collection only.
  It does NOT access camera streams, authenticate to devices,
  or perform any active scanning. All data comes from Shodan's
  pre-indexed public database.
  You are responsible for ensuring lawful use in your jurisdiction.

REQUIREMENTS:
  pip install shodan python-dotenv

SETUP:
  1. Rename .env.example to .env in the same folder as this script.
  2. Replace the placeholder with your Shodan API key:
        SHODAN_API_KEY=your_actual_key_here
  3. Get your key at: https://account.shodan.io

LOCATION OPTIONS (all optional, all combinable):
  --country   Two-letter country code          e.g. BO
  --city      City name                        e.g. "La Paz"
  --bbox      Bounding box as lat/lon          e.g. "-22.9,-43.2,-22.8,-43.1"
              Format: min_lat,min_lon,max_lat,max_lon

EXAMPLES:
  python shodan_ingest.py
  python shodan_ingest.py --country BO
  python shodan_ingest.py --country US --city "Houston"
  python shodan_ingest.py --bbox "-16.5,-68.2,-16.4,-68.1"
  python shodan_ingest.py --country BR --city "Rio de Janeiro" --limit 500
  python shodan_ingest.py --country DE --type hikvision --limit 200
  python shodan_ingest.py --filter 'product:"FOG" port:554' --country MX
"""

import os
import sys
import csv
import argparse
import datetime
from typing import Any
import importlib

# Optional dependency import for cleaner editor/lint behavior when
# python-dotenv is not available in the currently selected interpreter.
def load_dotenv(*args, **kwargs):
    """Fallback no-op when python-dotenv is unavailable."""
    return False

try:
    _dotenv = importlib.import_module("dotenv")
    load_dotenv = getattr(_dotenv, "load_dotenv", load_dotenv)
except Exception:
    pass

# ── Load API key from .env ────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("SHODAN_API_KEY")


# ── Shodan import with beginner-friendly error ────────────────────────────────
try:
    shodan: Any = importlib.import_module("shodan")
except ImportError:
    print("\n[ERROR] The 'shodan' library is not installed.")
    print("  Run this in your terminal to fix it:")
    print("       pip install shodan python-dotenv\n")
    sys.exit(1)


# ── Output CSV columns — matches WRAITH schema exactly ─────────────────────
FIELDNAMES = [
    "ip", "latitude", "longitude", "device_type", "model",
    "location_label", "last_seen", "port", "org", "country"
]

# ── Camera type presets ───────────────────────────────────────────────────────
# DEFAULT is "fog" — change DEFAULT_TYPE below if you want a different default.
DEFAULT_TYPE = "fog"

CAMERA_QUERIES = {
    "fog":       '"FOG" camera',
    "generic":   '"ip camera" OR "network camera"',
    "ptz":       '"PTZ" camera',
    "webcam":    "webcam",
    "hikvision": 'product:"Hikvision"',
    "axis":      'product:"Axis"',
    "dahua":     'product:"Dahua"',
    "all":       'webcam OR "ip camera" OR "network camera" OR "FOG" OR "PTZ"',
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def check_api_key():
    """Verify API key exists before spending any time on anything else."""
    if not API_KEY or API_KEY == "your_api_key_here":
        print("\n[ERROR] No valid Shodan API key found.")
        print("  Steps to fix:")
        print("  1. Open the file named '.env' in the same folder as this script.")
        print("  2. Replace 'your_api_key_here' with your actual key.")
        print("  3. Save the file and run the script again.")
        print("  Get your key at: https://account.shodan.io\n")
        sys.exit(1)


def parse_bbox(bbox_str):
    """
    Parse a bounding box string into its four components.

    Expected format:  "min_lat,min_lon,max_lat,max_lon"
    Example:          "-16.5,-68.2,-16.4,-68.1"

    Returns a tuple (min_lat, min_lon, max_lat, max_lon) or exits with
    a clear error message if the format is wrong.
    """
    try:
        parts = [float(p.strip()) for p in bbox_str.split(",")]
        if len(parts) != 4:
            raise ValueError
        min_lat, min_lon, max_lat, max_lon = parts

        # Sanity check the values are in plausible ranges
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if min_lat >= max_lat:
            raise ValueError("min_lat must be less than max_lat")
        if min_lon >= max_lon:
            raise ValueError("min_lon must be less than max_lon")

        return min_lat, min_lon, max_lat, max_lon

    except ValueError as e:
        print(f"\n[ERROR] Invalid bounding box: {e}")
        print("  Expected format: min_lat,min_lon,max_lat,max_lon")
        print("  Example:         -16.5,-68.2,-16.4,-68.1")
        print("  Tip: Use Google Maps to find lat/lon coordinates.\n")
        sys.exit(1)


def build_query(country=None, city=None, bbox=None, camera_type=None, custom_filter=None):
    """
    Assemble a Shodan search query from the provided location options.

    Priority order:
      1. custom_filter overrides camera_type if both are provided
      2. bbox, country, and city are all additive filters appended to the query

    Shodan bounding box filter syntax: geo:min_lat,min_lon,max_lat,max_lon
    """
    # ── Camera base query ──────────────────────────────────────────────────
    if custom_filter:
        base = custom_filter
    else:
        resolved_type = (camera_type or DEFAULT_TYPE).lower()
        base = CAMERA_QUERIES.get(resolved_type, CAMERA_QUERIES[DEFAULT_TYPE])

    parts = [base]

    # ── Location filters ───────────────────────────────────────────────────
    # Bounding box takes priority over country/city if all three are provided,
    # because a bbox is already geographically constrained.
    if bbox:
        min_lat, min_lon, max_lat, max_lon = bbox
        parts.append(f"geo:{min_lat},{min_lon},{max_lat},{max_lon}")
    else:
        if country:
            parts.append(f"country:{country.upper()}")
        if city:
            parts.append(f'city:"{city}"')

    return " ".join(parts)


def extract_device_info(result):
    """
    Pull the fields we need from a single Shodan result.

    Shodan returns deeply nested dictionaries. This function flattens
    everything into the flat row format that WRAITH expects.

    Returns None if the record has no lat/lon coordinates — those records
    are useless for a globe visualization and are skipped.
    """
    location = result.get("location", {})
    lat = location.get("latitude")
    lon = location.get("longitude")

    if lat is None or lon is None:
        return None

    # Product/model name — Shodan stores this in different fields depending
    # on the device, so we try several and take the first non-empty one.
    model = (
        result.get("product")
        or result.get("info", "").split("\n")[0]  # first line of banner
        or "Unknown"
    ).strip()[:80]  # cap length to keep CSV clean

    # Device type — Shodan may or may not populate this field
    device_type = (result.get("devicetype") or "IP Camera").strip()

    # Human-readable location label for the WRAITH table/tooltip
    city_name    = location.get("city") or ""
    country_name = location.get("country_name") or location.get("country_code") or ""
    location_label = ", ".join(filter(None, [city_name, country_name])) or "Unknown"

    # Shodan timestamps look like: "2025-08-01T12:34:56.000000"
    # WRAITH only needs the date portion (YYYY-MM-DD)
    raw_ts = result.get("timestamp", "")
    last_seen = raw_ts[:10] if raw_ts else datetime.date.today().isoformat()

    return {
        "ip":             result.get("ip_str", ""),
        "latitude":       lat,
        "longitude":      lon,
        "device_type":    device_type,
        "model":          model,
        "location_label": location_label,
        "last_seen":      last_seen,
        "port":           result.get("port", ""),
        "org":            result.get("org", "Unknown"),
        "country":        location.get("country_code", ""),
    }


def save_to_csv(records, output_path):
    """Write the collected records to a properly formatted CSV file."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)
    print(f"\n[SAVED]  {len(records)} records → {output_path}")


def print_bbox_help():
    """Print a quick guide for finding bounding box coordinates."""
    print("""
  HOW TO FIND A BOUNDING BOX:
  ────────────────────────────────────────────────────────
  1. Go to:  https://boundingbox.klokantech.com
  2. Search for your city or draw a rectangle on the map.
  3. Select "CSV" format at the bottom.
  4. Copy the four numbers — that's your bbox string.

  Format:  min_lat,min_lon,max_lat,max_lon
  Example (La Paz, Bolivia):  -16.57,-68.18,-16.45,-68.02
  ────────────────────────────────────────────────────────
    """)


# ─────────────────────────────────────────────────────────────────────────────
# INTERACTIVE MODE
# ─────────────────────────────────────────────────────────────────────────────

def interactive_mode():
    """
    Walk the user through all options one at a time with clear prompts.
    Falls back gracefully to defaults when the user hits ENTER without input.
    """
    print("\n" + "="*58)
    print("  WRAITH — Shodan FOG Camera Ingestion")
    print("  Interactive Mode — press ENTER to use the default")
    print("="*58)

    # ── Location method ──────────────────────────────────────────────────────
    print("""
  LOCATION OPTIONS (you can use one, two, or all three):
    1. Country code  — e.g. BO, US, DE, BR, MX
    2. City name     — e.g. La Paz, Houston, Berlin
    3. Bounding box  — lat/lon rectangle for precise area targeting
  """)

    country = input("  Country code [optional, e.g. BO]: ").strip().upper() or None
    city    = input("  City name    [optional, e.g. La Paz]: ").strip() or None

    bbox_raw = input("  Bounding box [optional, format: min_lat,min_lon,max_lat,max_lon]: ").strip()
    if bbox_raw:
        bbox = parse_bbox(bbox_raw)
    else:
        bbox = None

    if bbox_raw == "?":
        print_bbox_help()
        bbox_raw = input("  Bounding box: ").strip()
        bbox = parse_bbox(bbox_raw) if bbox_raw else None

    # ── Camera type ──────────────────────────────────────────────────────────
    print(f"\n  Camera type presets:")
    for key in CAMERA_QUERIES:
        marker = " (default)" if key == DEFAULT_TYPE else ""
        print(f"    {key}{marker}")

    type_input = input(f"\n  Camera type [default: {DEFAULT_TYPE}]: ").strip().lower()
    camera_type = type_input if type_input in CAMERA_QUERIES else DEFAULT_TYPE

    if type_input and type_input not in CAMERA_QUERIES:
        print(f"  [NOTE] '{type_input}' not recognized — using default: {DEFAULT_TYPE}")

    # ── Custom filter override ───────────────────────────────────────────────
    print("\n  Custom Shodan filter (optional — overrides camera type):")
    print("  Example: product:\"Hikvision\" port:554")
    print("  Leave blank to use the camera type preset above.")
    custom_filter = input("  Custom filter: ").strip() or None

    # ── Result limit ─────────────────────────────────────────────────────────
    limit_str = input("\n  Max results to pull [default: 100]: ").strip()
    try:
        limit = int(limit_str) if limit_str else 100
        if limit <= 0:
            raise ValueError
    except ValueError:
        print("  [NOTE] Invalid number — using default of 100.")
        limit = 100

    # ── Output filename ──────────────────────────────────────────────────────
    location_tag = (country or city or "global").replace(" ", "_").lower()
    default_out  = f"wraith_{location_tag}_{datetime.date.today().isoformat()}.csv"
    out_input    = input(f"\n  Output filename [default: {default_out}]: ").strip()
    output_path  = out_input or default_out

    return country, city, bbox, camera_type, custom_filter, limit, output_path


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():

    parser = argparse.ArgumentParser(
        prog="shodan_ingest.py",
        description="WRAITH — Pull FOG/IP camera data from Shodan for any location.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
LOCATION FLAGS (combinable — use one, two, or all three):
  --country   Two-letter ISO country code          e.g. BO
  --city      City name (quote multi-word names)   e.g. "La Paz"
  --bbox      Bounding box: min_lat,min_lon,max_lat,max_lon
              e.g. -16.57,-68.18,-16.45,-68.02
              Tip: generate coords at https://boundingbox.klokantech.com

EXAMPLES:
  python shodan_ingest.py
  python shodan_ingest.py --country BO
  python shodan_ingest.py --country BO --city "La Paz"
  python shodan_ingest.py --bbox "-16.57,-68.18,-16.45,-68.02"
  python shodan_ingest.py --country US --city "Houston" --limit 500
  python shodan_ingest.py --country DE --type hikvision
  python shodan_ingest.py --filter 'product:"FOG" port:554' --country MX
  python shodan_ingest.py --interactive
        """
    )

    # Location arguments
    parser.add_argument("--country",  type=str, default=None,
                        help="Two-letter country code (e.g. BO, US, DE)")
    parser.add_argument("--city",     type=str, default=None,
                        help="City name (e.g. 'La Paz')")
    parser.add_argument("--bbox",     type=str, default=None,
                        help="Bounding box: min_lat,min_lon,max_lat,max_lon")

    # Query arguments
    parser.add_argument("--type",     type=str, default=None,
                        choices=list(CAMERA_QUERIES.keys()),
                        help=f"Camera type preset (default: {DEFAULT_TYPE})")
    parser.add_argument("--filter",   type=str, default=None,
                        help="Raw Shodan filter string — overrides --type")

    # Output arguments
    parser.add_argument("--limit",    type=int, default=100,
                        help="Max results to pull (default: 100)")
    parser.add_argument("--output",   type=str, default=None,
                        help="Output CSV filename")

    # Mode
    parser.add_argument("--interactive", action="store_true",
                        help="Force interactive prompt mode")
    parser.add_argument("--bbox-help",   action="store_true",
                        help="Show instructions for finding bounding box coordinates")

    args = parser.parse_args()

    # ── Bounding box help shortcut ───────────────────────────────────────────
    if args.bbox_help:
        print_bbox_help()
        sys.exit(0)

    # ── API key check — always first ─────────────────────────────────────────
    check_api_key()

    # ── Decide: interactive or CLI ───────────────────────────────────────────
    # Default to interactive if no location or query flags were passed
    no_location = args.country is None and args.city is None and args.bbox is None
    no_query    = args.type is None and args.filter is None

    use_interactive = args.interactive or (no_location and no_query)

    if use_interactive:
        country, city, bbox, camera_type, custom_filter, limit, output_path = interactive_mode()
    else:
        country       = args.country
        city          = args.city
        bbox          = parse_bbox(args.bbox) if args.bbox else None
        camera_type   = args.type or DEFAULT_TYPE
        custom_filter = args.filter
        limit         = args.limit

        # Auto-generate output filename if not specified
        if args.output:
            output_path = args.output
        else:
            loc_tag = (country or city or "global").replace(" ", "_").lower()
            output_path = f"wraith_{loc_tag}_{datetime.date.today().isoformat()}.csv"

    # ── Build the query ──────────────────────────────────────────────────────
    query = build_query(
        country=country,
        city=city,
        bbox=bbox,
        camera_type=camera_type,
        custom_filter=custom_filter
    )

    # ── Pre-flight summary ───────────────────────────────────────────────────
    print("\n" + "─"*50)
    print(f"  QUERY   : {query}")
    if bbox:
        print(f"  BBOX    : lat {bbox[0]}–{bbox[2]}, lon {bbox[1]}–{bbox[3]}")
    print(f"  LIMIT   : {limit} results")
    print(f"  OUTPUT  : {output_path}")
    print("─"*50)

    confirm = input("\n  Proceed? [Y/n]: ").strip().lower()
    if confirm == "n":
        print("  Cancelled.\n")
        sys.exit(0)

    # ── Connect to Shodan ────────────────────────────────────────────────────
    print("\n  Connecting to Shodan API...")
    try:
        api = shodan.Shodan(API_KEY)
        info = api.info()
        print(f"  Connected. Query credits remaining: {info.get('query_credits', 'unknown')}")
    except shodan.APIError as e:
        print(f"\n[ERROR] Could not connect to Shodan: {e}")
        print("  Check that your API key in .env is valid.\n")
        sys.exit(1)

    # ── Pull results ─────────────────────────────────────────────────────────
    records = []
    pulled  = 0
    skipped = 0

    print(f"\n  Pulling up to {limit} results...\n")

    try:
        for result in api.search_cursor(query):
            if pulled >= limit:
                break

            row = extract_device_info(result)

            if row is None:
                skipped += 1
                continue

            records.append(row)
            pulled += 1

            if pulled % 10 == 0:
                print(f"    {pulled} records collected...", flush=True)

    except shodan.APIError as e:
        err = str(e)
        print(f"\n[ERROR] Search failed: {err}")

        if "No information available" in err:
            print("  No results found for this query. Try:")
            print("  - A broader camera type (--type all)")
            print("  - Removing the city filter")
            print("  - Checking the country code is correct")

        elif "insufficient query credits" in err.lower():
            print("  Your Shodan account is out of query credits.")
            print("  Free accounts get 1 credit/month. Upgrade at shodan.io.")

        elif "Access denied" in err:
            print("  This search requires a paid Shodan plan (e.g. bounding box queries).")

        sys.exit(1)

    # ── Results ──────────────────────────────────────────────────────────────
    print(f"\n  Done.")
    print(f"  Collected : {pulled} records with coordinates")
    print(f"  Skipped   : {skipped} records (no lat/lon — unusable for globe)")

    if not records:
        print("\n  No valid records to save. Try a different query or location.\n")
        sys.exit(0)

    # ── Save CSV ─────────────────────────────────────────────────────────────
    save_to_csv(records, output_path)

    print(f"\n  Next step — load into WRAITH:")
    print(f"  streamlit run app.py  →  upload '{output_path}'\n")


if __name__ == "__main__":
    main()
