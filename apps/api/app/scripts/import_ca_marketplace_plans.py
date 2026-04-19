from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

AGE_SAMPLES = [21, 27, 40, 55]

ISSUER_NAMES = {
    "18126": "Molina Healthcare",
    "20523": "Aetna CVS Health",
    "27603": "Anthem Blue Cross",
    "40513": "Kaiser Permanente",
    "47579": "Balance by CCHP",
    "51396": "IEHP",
    "67138": "Health Net",
    "70285": "Blue Shield of California",
    "84014": "Valley Health Plan",
    "92499": "Sharp Health Plan",
    "92815": "L.A. Care",
    "93689": "Western Health Advantage",
}

QUALITY_RATINGS = {
    ("Aetna CVS Health", "HMO"): 5.0,
    ("Anthem Blue Cross", "EPO"): 5.0,
    ("Anthem Blue Cross", "HMO"): 5.0,
    ("Balance by CCHP", "HMO"): 5.0,
    ("Blue Shield of California", "HMO"): 5.0,
    ("Blue Shield of California", "PPO"): 5.0,
    ("Health Net", "HMO"): 5.0,
    ("Health Net", "PPO"): 5.0,
    ("Kaiser Permanente", "HMO"): 5.0,
    ("L.A. Care", "HMO"): 5.0,
    ("Molina Healthcare", "HMO"): 5.0,
    ("Sharp Health Plan", "HMO"): 5.0,
    ("Valley Health Plan", "HMO"): 5.0,
    ("Western Health Advantage", "HMO"): 5.0,
}

PURCHASE_URL = "https://www.coveredca.com/"
SOURCE_URL = "https://www.coveredca.com/support/getting-started/review-plans-and-prices/"
QUALITY_SOURCE_URL = "https://www.coveredca.com/support/getting-started/quality-ratings/"


def _money_to_float(value: str) -> float | None:
    cleaned = value.replace("$", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _money_to_int(value: str) -> int | None:
    amount = _money_to_float(value)
    return int(round(amount)) if amount is not None else None


def _premium_band(amount: float | None) -> str:
    if amount is None:
        return "medium"
    if amount <= 360:
        return "low"
    if amount <= 620:
        return "medium"
    return "high"


def _deductible_band(amount: int | None) -> str:
    if amount is None:
        return "medium"
    if amount <= 1500:
        return "low"
    if amount <= 5500:
        return "medium"
    return "high"


def _network_flexibility(plan_type: str, referral_required: bool | None) -> str:
    if plan_type in {"PPO", "EPO"}:
        return "high"
    if referral_required is False:
        return "high"
    return "low"


def _metal_care_usage_fit(metal_level: str, deductible_band: str) -> list[str]:
    normalized = metal_level.lower()
    if "platinum" in normalized or "gold" in normalized:
        return ["moderate", "high"]
    if "bronze" in normalized or "catastrophic" in normalized:
        return ["low"]
    if deductible_band == "low":
        return ["moderate", "high"]
    return ["low", "moderate"]


def _prescription_support(metal_level: str, deductible_band: str) -> str:
    normalized = metal_level.lower()
    if "gold" in normalized or "platinum" in normalized or deductible_band == "low":
        return "strong"
    return "moderate"


def _quality_band(quality_rating: float | None) -> str:
    if quality_rating is not None and quality_rating >= 4.5:
        return "strong"
    return "solid"


def _doctor_search_plan_id(plan_type: str, metal_level: str, premium_band: str) -> str:
    if plan_type in {"PPO", "EPO"}:
        if "gold" in metal_level.lower() or "platinum" in metal_level.lower() or premium_band == "high":
            return "cigna-open-access"
        return "blue-shield-ppo"
    return "anthem-blue-hmo"


def _advisor_blurb(
    provider: str,
    metal_level: str,
    plan_type: str,
    premium_amount: float | None,
    referral_required: bool | None,
) -> str:
    premium_copy = (
        f" Estimated monthly premium is around ${premium_amount:.0f} before subsidies."
        if premium_amount is not None
        else ""
    )
    referral_copy = (
        " Specialist referrals are usually required."
        if referral_required
        else " Specialist access is more direct."
    )
    return (
        f"{provider} {metal_level} {plan_type} marketplace coverage for California shoppers."
        f"{premium_copy}{referral_copy}"
    ).strip()


def _ideal_for(
    *,
    premium_band: str,
    plan_type: str,
    metal_level: str,
    deductible_band: str,
) -> list[str]:
    ideas: list[str] = []
    if premium_band == "low":
        ideas.append("Shoppers trying to keep monthly premiums lower before subsidies are applied")
    if plan_type in {"PPO", "EPO"}:
        ideas.append("People who want easier specialist access and less referral friction")
    if "gold" in metal_level.lower() or "platinum" in metal_level.lower():
        ideas.append("Patients expecting frequent visits, prescriptions, or a heavier-care year")
    elif deductible_band == "high":
        ideas.append("Healthier shoppers who mainly want protection for bigger or unexpected events")
    else:
        ideas.append("People who want a balanced plan for moderate year-round use")
    return ideas[:3]


def _tradeoffs(
    *,
    premium_band: str,
    deductible_band: str,
    referral_required: bool | None,
    plan_type: str,
) -> list[str]:
    tradeoffs: list[str] = []
    if premium_band == "high":
        tradeoffs.append("Monthly premiums can run higher before tax credits or subsidies")
    if deductible_band == "high":
        tradeoffs.append("Out-of-pocket costs can stay high until you meet the deductible")
    if referral_required:
        tradeoffs.append("Specialist visits may require a primary care referral first")
    if plan_type == "EPO":
        tradeoffs.append("Out-of-network flexibility is usually limited even without referral rules")
    if not tradeoffs:
        tradeoffs.append("You still need to verify exact doctors, prescriptions, and subsidy details on Covered California")
    return tradeoffs[:3]


def build_marketplace_catalog(source_dir: Path) -> list[dict[str, object]]:
    plans_path = source_dir / "CAPlans05062025.csv"
    rates_path = source_dir / "CARates05062025.csv"
    service_areas_path = source_dir / "CAServiceAreas05062025.csv"
    networks_path = source_dir / "CANetworks05062025.csv"

    network_lookup: dict[tuple[str, str], dict[str, str]] = {}
    with networks_path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["MARKET COVERAGE"] != "Individual" or row["DENTAL PLAN ONLY"] != "No":
                continue
            network_lookup[(row["ISSUER ID"], row["NETWORK ID"])] = {
                "name": row["NETWORK NAME"].strip(),
                "url": row["NETWORK URL"].strip(),
            }

    service_lookup: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(
        lambda: {"zip_codes": set(), "counties": set()}
    )
    with service_areas_path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["MARKET COVERAGE"] != "Individual" or row["DENTAL PLAN ONLY"] != "No":
                continue
            key = (row["ISSUER ID"], row["SERVICE AREA ID"])
            counties = service_lookup[key]["counties"]
            if row["COUNTY NAME"].strip():
                counties.add(row["COUNTY NAME"].strip())
            zip_codes = service_lookup[key]["zip_codes"]
            for zip_code in row["ZIP CODE"].split(","):
                cleaned = zip_code.strip()
                if cleaned:
                    zip_codes.add(cleaned)

    rate_lookup: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    with rates_path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["TOBACCO"] != "No Preference":
                continue
            if not row["AGE"].isdigit():
                continue
            age = int(row["AGE"])
            if age not in AGE_SAMPLES:
                continue
            amount = _money_to_float(row["INDIVIDUAL RATE"])
            if amount is not None:
                rate_lookup[row["PLAN ID"]][age].append(amount)

    catalog_rows: dict[str, dict[str, object]] = {}
    with plans_path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["MARKET COVERAGE"] != "Individual" or row["DENTAL ONLY PLAN"] != "No":
                continue

            plan_id = row["STANDARD COMPONENT ID"].strip()
            issuer_id = row["ISSUER ID"].strip()
            network_id = row["NETWORK ID"].strip()
            service_area_id = row["SERVICE AREA ID"].strip()
            service_data = service_lookup[(issuer_id, service_area_id)]
            network_data = network_lookup.get((issuer_id, network_id), {"name": "", "url": ""})

            metal_level = row["METAL LEVEL"].strip() or "Unknown"
            plan_type = row["PLAN TYPE"].strip() or "Unknown"
            referral_required = row["IS REFERRAL REQUIRED FOR SPECIALIST"].strip().lower() == "yes"
            deductible_amount = _money_to_int(
                row["MEHB DED INN TIER1 INDIVIDUAL"] or row["TEHB DED INN TIER 1 INDIVIDUAL"]
            )
            out_of_pocket_max_amount = _money_to_int(
                row["TEHB INN TIER 1 INDIVIDUAL MOOP"] or row["MEHB INN TIER 1 INDIVIDUAL MOOP"]
            )
            premium_samples = {
                str(age): round(statistics.median(values), 2)
                for age, values in rate_lookup.get(plan_id, {}).items()
                if values
            }
            default_premium = premium_samples.get("27")
            if default_premium is None and premium_samples:
                default_premium = round(statistics.median(premium_samples.values()), 2)

            premium_band = _premium_band(default_premium)
            deductible_band = _deductible_band(deductible_amount)
            provider = ISSUER_NAMES.get(issuer_id, network_data["name"] or f"Issuer {issuer_id}")
            quality_rating = QUALITY_RATINGS.get((provider, plan_type))

            catalog_rows[plan_id] = {
                "plan_id": plan_id,
                "provider": provider,
                "plan_name": row["PLAN MARKETING NAME"].strip(),
                "plan_type": plan_type,
                "network_name": network_data["name"] or None,
                "metal_level": metal_level,
                "coverage_channels": ["marketplace"],
                "service_states": ["CA"],
                "supported_zip_codes": sorted(service_data["zip_codes"]),
                "service_counties": sorted(service_data["counties"]),
                "monthly_premium_band": premium_band,
                "monthly_premium_amount": default_premium,
                "monthly_premium_samples": premium_samples,
                "deductible_band": deductible_band,
                "deductible_amount": deductible_amount,
                "out_of_pocket_max_amount": out_of_pocket_max_amount,
                "network_flexibility": _network_flexibility(plan_type, referral_required),
                "care_usage_fit": _metal_care_usage_fit(metal_level, deductible_band),
                "prescription_support": _prescription_support(metal_level, deductible_band),
                "quality_band": _quality_band(quality_rating),
                "quality_rating": quality_rating,
                "referral_required_for_specialists": referral_required,
                "advisor_blurb": _advisor_blurb(
                    provider=provider,
                    metal_level=metal_level,
                    plan_type=plan_type,
                    premium_amount=default_premium,
                    referral_required=referral_required,
                ),
                "ideal_for": _ideal_for(
                    premium_band=premium_band,
                    plan_type=plan_type,
                    metal_level=metal_level,
                    deductible_band=deductible_band,
                ),
                "tradeoffs": _tradeoffs(
                    premium_band=premium_band,
                    deductible_band=deductible_band,
                    referral_required=referral_required,
                    plan_type=plan_type,
                ),
                "purchase_url": PURCHASE_URL,
                "purchase_cta_label": "Compare or apply on Covered California",
                "source_url": SOURCE_URL,
                "quality_source_url": QUALITY_SOURCE_URL,
                "network_url": network_data["url"] or None,
                # Closest legacy demo-plan mapping so the doctor search step still works.
                "doctor_search_plan_id": _doctor_search_plan_id(
                    plan_type=plan_type,
                    metal_level=metal_level,
                    premium_band=premium_band,
                ),
            }

    return sorted(
        catalog_rows.values(),
        key=lambda item: (
            item["provider"],
            item["metal_level"],
            item["plan_name"],
        ),
    )


def main() -> None:
    project_root = Path(__file__).resolve().parents[4]
    source_dir = Path("/tmp/californiasbepuf2025")
    output_path = project_root / "packages" / "mock-data" / "ca_marketplace_plans.json"

    if not source_dir.exists():
        raise SystemExit(
            "Missing extracted CMS California marketplace files at /tmp/californiasbepuf2025. "
            "Download and unzip the official California SBE PUF first."
        )

    catalog = build_marketplace_catalog(source_dir)
    output_path.write_text(json.dumps(catalog, indent=2))
    print(f"Wrote {len(catalog)} marketplace plans to {output_path}")


if __name__ == "__main__":
    main()
