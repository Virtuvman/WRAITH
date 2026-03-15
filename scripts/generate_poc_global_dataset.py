"""Generate global PoC camera datasets for WRAITH trials.

Outputs:
  - data/poc_global_500.csv
  - poc_global_500.csv
  - data/poc_global_500_v2.csv
  - data/poc_global_500_v3.csv
  - data/poc_global_500_v4.csv
  - data/poc_global_500_v5.csv
  - data/poc_global_500.xlsx (if Excel engine available)
  - poc_global_500.xlsx (if Excel engine available)
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
import random


def _build_rows(seed: int, poc_batch: str, size: int = 500) -> list[dict[str, object]]:
    rng = random.Random(seed)

    world_points = [
        ("Washington", "US", 38.9072, -77.0369, "North America"),
        ("New York", "US", 40.7128, -74.0060, "North America"),
        ("Mexico City", "MX", 19.4326, -99.1332, "North America"),
        ("Toronto", "CA", 43.6532, -79.3832, "North America"),
        ("Bogota", "CO", 4.7110, -74.0721, "South America"),
        ("Lima", "PE", -12.0464, -77.0428, "South America"),
        ("Sao Paulo", "BR", -23.5505, -46.6333, "South America"),
        ("Buenos Aires", "AR", -34.6037, -58.3816, "South America"),
        ("London", "GB", 51.5074, -0.1278, "Europe"),
        ("Paris", "FR", 48.8566, 2.3522, "Europe"),
        ("Berlin", "DE", 52.5200, 13.4050, "Europe"),
        ("Madrid", "ES", 40.4168, -3.7038, "Europe"),
        ("Rome", "IT", 41.9028, 12.4964, "Europe"),
        ("Warsaw", "PL", 52.2297, 21.0122, "Europe"),
        ("Cairo", "EG", 30.0444, 31.2357, "Africa"),
        ("Lagos", "NG", 6.5244, 3.3792, "Africa"),
        ("Nairobi", "KE", -1.2921, 36.8219, "Africa"),
        ("Johannesburg", "ZA", -26.2041, 28.0473, "Africa"),
        ("Casablanca", "MA", 33.5731, -7.5898, "Africa"),
        ("Accra", "GH", 5.6037, -0.1870, "Africa"),
        ("Dubai", "AE", 25.2048, 55.2708, "Middle East"),
        ("Riyadh", "SA", 24.7136, 46.6753, "Middle East"),
        ("Tel Aviv", "IL", 32.0853, 34.7818, "Middle East"),
        ("Doha", "QA", 25.2854, 51.5310, "Middle East"),
        ("Istanbul", "TR", 41.0082, 28.9784, "Middle East"),
        ("Delhi", "IN", 28.6139, 77.2090, "Asia"),
        ("Mumbai", "IN", 19.0760, 72.8777, "Asia"),
        ("Singapore", "SG", 1.3521, 103.8198, "Asia"),
        ("Tokyo", "JP", 35.6762, 139.6503, "Asia"),
        ("Seoul", "KR", 37.5665, 126.9780, "Asia"),
        ("Bangkok", "TH", 13.7563, 100.5018, "Asia"),
        ("Jakarta", "ID", -6.2088, 106.8456, "Asia"),
        ("Sydney", "AU", -33.8688, 151.2093, "Oceania"),
        ("Melbourne", "AU", -37.8136, 144.9631, "Oceania"),
        ("Auckland", "NZ", -36.8509, 174.7645, "Oceania"),
        ("Perth", "AU", -31.9505, 115.8605, "Oceania"),
    ]

    device_types = ["IP Camera", "PTZ Camera", "Dome Camera", "Bullet Camera"]
    models = [
        "Hikvision DS-2CD2085G1",
        "Axis P5655-E",
        "Dahua SD49425XB",
        "Bosch FLEXIDOME",
        "Hanwha XNV-8080R",
        "Sony SNC-EP580",
    ]
    orgs = ["Comcast", "Verizon", "AT&T", "Lumen", "DigitalOcean", "Cloudflare", "Airtel", "BT"]
    ports = [80, 443, 554, 8080]

    today = date.today()
    rows: list[dict[str, object]] = []

    for i in range(size):
        city, country, base_lat, base_lon, region = world_points[i % len(world_points)]
        lat = max(-89.9, min(89.9, base_lat + rng.uniform(-0.45, 0.45)))
        lon = max(-179.9, min(179.9, base_lon + rng.uniform(-0.45, 0.45)))

        # Mix of fresh / stale / expired dates for PoC staleness views.
        if i % 10 < 4:
            days_ago = rng.randint(3, 80)      # fresh
        elif i % 10 < 7:
            days_ago = rng.randint(95, 170)    # stale
        else:
            days_ago = rng.randint(190, 360)   # expired

        last_seen = (today - timedelta(days=days_ago)).isoformat()

        rows.append(
            {
                "ip": f"10.{(i // 256) % 256}.{(i // 16) % 256}.{(i % 254) + 1}",
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "device_type": rng.choice(device_types),
                "model": rng.choice(models),
                "location_label": f"{city} Sector {i % 20 + 1}",
                "last_seen": last_seen,
                "port": rng.choice(ports),
                "org": rng.choice(orgs),
                "country": country,
                "region": region,
                "poc_batch": poc_batch,
            }
        )

    return rows


def _write_csv(rows: list[dict[str, object]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_optional_xlsx(rows: list[dict[str, object]], out_path: Path) -> None:
    try:
        # Keep Excel generation optional and dependency-light.
        from openpyxl import Workbook  # type: ignore[import-untyped]

        wb = Workbook()
        ws = wb.active

        headers = list(rows[0].keys())
        ws.append(headers)
        for row in rows:
            ws.append([row[h] for h in headers])

        wb.save(out_path)
    except Exception:
        # If no Excel writer installed, CSV outputs are still generated.
        pass


def main() -> None:
    dataset_specs = [
        ("GLOBAL_500_V1", 42),
        ("GLOBAL_500_V2", 84),
        ("GLOBAL_500_V3", 126),
        ("GLOBAL_500_V4", 168),
        ("GLOBAL_500_V5", 210),
    ]

    generated_csv_paths: list[Path] = []

    for batch, seed in dataset_specs:
        rows = _build_rows(seed=seed, poc_batch=batch, size=500)

        # Preserve original legacy output names for V1 in both root and data/
        if batch == "GLOBAL_500_V1":
            for p in [Path("data/poc_global_500.csv"), Path("poc_global_500.csv")]:
                _write_csv(rows, p)
                generated_csv_paths.append(p)

            for p in [Path("data/poc_global_500.xlsx"), Path("poc_global_500.xlsx")]:
                _write_optional_xlsx(rows, p)
        else:
            suffix = batch.split("_")[-1].lower()  # v2, v3, ...
            csv_path = Path(f"data/poc_global_500_{suffix}.csv")
            _write_csv(rows, csv_path)
            generated_csv_paths.append(csv_path)

    print("Generated 500-point PoC datasets:")
    for p in generated_csv_paths:
        print(f" - {p.as_posix()}")
    print(" - data/poc_global_500.xlsx (if supported)")
    print(" - poc_global_500.xlsx (if supported)")


if __name__ == "__main__":
    main()
