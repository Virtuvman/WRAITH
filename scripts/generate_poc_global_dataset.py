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


def _weighted_choice(rng: random.Random, items: list[str], weights: list[float]) -> str:
    total = sum(weights)
    if total <= 0:
        return rng.choice(items)
    pick = rng.uniform(0, total)
    acc = 0.0
    for item, w in zip(items, weights):
        acc += w
        if pick <= acc:
            return item
    return items[-1]


def _sample_days_ago(rng: random.Random, staleness_mix: dict[str, float]) -> int:
    """Return days_ago across CURRENT / REVIEW / STALE / EXPIRED ranges."""
    statuses = ["CURRENT", "REVIEW", "STALE", "EXPIRED"]
    weights = [float(staleness_mix.get(s, 0.0)) for s in statuses]
    status = _weighted_choice(rng, statuses, weights)

    if status == "CURRENT":
        return rng.randint(3, 80)
    if status == "REVIEW":
        return rng.randint(95, 170)
    if status == "STALE":
        return rng.randint(190, 345)
    return rng.randint(370, 540)  # EXPIRED (>360d)


def _biased_choice(rng: random.Random, base: list[str], preferred: list[str], preferred_weight: float) -> str:
    if preferred and rng.random() < preferred_weight:
        return rng.choice(preferred)
    return rng.choice(base)


def _build_rows(
    seed: int,
    poc_batch: str,
    profile_name: str,
    profile: dict[str, object],
    size: int = 500,
) -> list[dict[str, object]]:
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

    points_by_region: dict[str, list[tuple[str, str, float, float, str]]] = {}
    for p in world_points:
        points_by_region.setdefault(p[4], []).append(p)

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

    region_order = sorted(points_by_region.keys())
    region_weights_cfg = profile.get("region_weights")
    region_weights: dict[str, float] = (
        region_weights_cfg if isinstance(region_weights_cfg, dict) else {r: 1.0 for r in region_order}
    )

    staleness_mix_cfg = profile.get("staleness_mix")
    staleness_mix: dict[str, float] = (
        staleness_mix_cfg
        if isinstance(staleness_mix_cfg, dict)
        else {"CURRENT": 40, "REVIEW": 30, "STALE": 20, "EXPIRED": 10}
    )

    jitter_scale = float(profile.get("jitter_scale", 0.45))

    preferred_models = [str(x) for x in profile.get("preferred_models", [])] if isinstance(profile.get("preferred_models"), list) else []
    preferred_orgs = [str(x) for x in profile.get("preferred_orgs", [])] if isinstance(profile.get("preferred_orgs"), list) else []
    preferred_ports = [int(x) for x in profile.get("preferred_ports", [])] if isinstance(profile.get("preferred_ports"), list) else []

    preferred_weight = float(profile.get("preferred_weight", 0.65))

    today = date.today()
    rows: list[dict[str, object]] = []

    for i in range(size):
        if profile_name == "baseline":
            city, country, base_lat, base_lon, region = world_points[i % len(world_points)]
        else:
            selected_region = _weighted_choice(
                rng,
                region_order,
                [float(region_weights.get(r, 1.0)) for r in region_order],
            )
            city, country, base_lat, base_lon, region = rng.choice(points_by_region[selected_region])

        lat = max(-89.9, min(89.9, base_lat + rng.uniform(-jitter_scale, jitter_scale)))
        lon = max(-179.9, min(179.9, base_lon + rng.uniform(-jitter_scale, jitter_scale)))

        days_ago = _sample_days_ago(rng, staleness_mix)

        last_seen = (today - timedelta(days=days_ago)).isoformat()

        rows.append(
            {
                "ip": f"10.{(i // 256) % 256}.{(i // 16) % 256}.{(i % 254) + 1}",
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "device_type": rng.choice(device_types),
                "model": _biased_choice(rng, models, preferred_models, preferred_weight),
                "location_label": f"{city} Sector {i % 20 + 1}",
                "last_seen": last_seen,
                "port": _biased_choice(rng, [str(p) for p in ports], [str(p) for p in preferred_ports], preferred_weight),
                "org": _biased_choice(rng, orgs, preferred_orgs, preferred_weight),
                "country": country,
                "region": region,
                "poc_batch": poc_batch,
                "trial_profile": profile_name,
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
        (
            "GLOBAL_500_V1",
            42,
            "baseline",
            {
                "staleness_mix": {"CURRENT": 40, "REVIEW": 30, "STALE": 20, "EXPIRED": 10},
                "jitter_scale": 0.45,
            },
        ),
        (
            "GLOBAL_500_V2",
            84,
            "expired_heavy",
            {
                "staleness_mix": {"CURRENT": 15, "REVIEW": 20, "STALE": 30, "EXPIRED": 35},
                "region_weights": {
                    "North America": 1.0,
                    "South America": 1.0,
                    "Europe": 1.0,
                    "Africa": 1.3,
                    "Middle East": 1.5,
                    "Asia": 1.2,
                    "Oceania": 0.8,
                },
                "preferred_orgs": ["Lumen", "Cloudflare"],
                "preferred_weight": 0.7,
                "jitter_scale": 0.35,
            },
        ),
        (
            "GLOBAL_500_V3",
            126,
            "fresh_asia_focus",
            {
                "staleness_mix": {"CURRENT": 65, "REVIEW": 20, "STALE": 10, "EXPIRED": 5},
                "region_weights": {
                    "North America": 0.8,
                    "South America": 0.8,
                    "Europe": 1.0,
                    "Africa": 0.7,
                    "Middle East": 1.0,
                    "Asia": 2.2,
                    "Oceania": 1.3,
                },
                "preferred_models": ["Axis P5655-E", "Hanwha XNV-8080R"],
                "preferred_ports": [443, 8080],
                "preferred_weight": 0.72,
                "jitter_scale": 0.55,
            },
        ),
        (
            "GLOBAL_500_V4",
            168,
            "americas_hotspot",
            {
                "staleness_mix": {"CURRENT": 30, "REVIEW": 30, "STALE": 25, "EXPIRED": 15},
                "region_weights": {
                    "North America": 2.1,
                    "South America": 1.8,
                    "Europe": 0.7,
                    "Africa": 0.5,
                    "Middle East": 0.5,
                    "Asia": 0.8,
                    "Oceania": 0.6,
                },
                "preferred_models": ["Hikvision DS-2CD2085G1", "Dahua SD49425XB"],
                "preferred_orgs": ["Comcast", "Verizon", "AT&T"],
                "preferred_weight": 0.75,
                "jitter_scale": 0.25,
            },
        ),
        (
            "GLOBAL_500_V5",
            210,
            "review_stale_global_mix",
            {
                "staleness_mix": {"CURRENT": 20, "REVIEW": 40, "STALE": 30, "EXPIRED": 10},
                "region_weights": {
                    "North America": 1.0,
                    "South America": 1.0,
                    "Europe": 1.4,
                    "Africa": 1.2,
                    "Middle East": 1.3,
                    "Asia": 1.2,
                    "Oceania": 0.8,
                },
                "preferred_ports": [554, 8080],
                "preferred_orgs": ["DigitalOcean", "BT", "Airtel"],
                "preferred_weight": 0.68,
                "jitter_scale": 0.4,
            },
        ),
    ]

    generated_csv_paths: list[Path] = []

    for batch, seed, profile_name, profile in dataset_specs:
        rows = _build_rows(seed=seed, poc_batch=batch, profile_name=profile_name, profile=profile, size=500)

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
