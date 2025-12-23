"""
Yahoo DSP Data Formatters

Format data between AdCP and Yahoo DSP API formats.
"""

from datetime import datetime, timezone
from typing import Any


def format_date_for_yahoo(dt: datetime) -> str:
    """Format datetime for Yahoo DSP API.

    Yahoo DSP API expects ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ

    Args:
        dt: Datetime object to format

    Returns:
        ISO 8601 formatted string
    """
    # Ensure UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)

    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def format_yahoo_date_to_datetime(date_str: str) -> datetime:
    """Parse Yahoo DSP API date string to datetime.

    Args:
        date_str: ISO 8601 formatted date string

    Returns:
        datetime object in UTC
    """
    # Handle various formats Yahoo might return
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date string: {date_str}")


def format_budget_for_yahoo(budget_cents: int) -> dict[str, Any]:
    """Format AdCP budget (cents) to Yahoo DSP budget format.

    Yahoo DSP uses micros (1/1,000,000 of currency unit) for budgets.
    AdCP uses cents (1/100 of currency unit).

    Args:
        budget_cents: Budget in cents

    Returns:
        Yahoo DSP budget object
    """
    # Convert cents to micros (multiply by 10,000) - ensure integer
    budget_micros = int(budget_cents * 10000)

    return {
        "amount": budget_micros,
        "currency": "USD",  # Default, can be parameterized
    }


def parse_budget_from_yahoo(yahoo_budget: dict[str, Any]) -> int:
    """Parse Yahoo DSP budget to AdCP format (cents).

    Args:
        yahoo_budget: Yahoo DSP budget object with 'amount' in micros

    Returns:
        Budget in cents
    """
    # Convert micros to cents (divide by 10,000)
    amount_micros = yahoo_budget.get("amount", 0)
    return int(amount_micros / 10000)


def format_targeting_for_yahoo(adcp_targeting: dict[str, Any]) -> dict[str, Any]:
    """Convert AdCP targeting to Yahoo DSP targeting format.

    Args:
        adcp_targeting: AdCP targeting specification

    Returns:
        Yahoo DSP targeting object
    """
    yahoo_targeting = {}

    # Geographic targeting
    if "geo_any_of" in adcp_targeting:
        yahoo_targeting["geo"] = {
            "include": [
                {"type": _get_geo_type(g), "id": g}
                for g in adcp_targeting["geo_any_of"]
            ]
        }

    # Device targeting
    if "device_type_any_of" in adcp_targeting:
        yahoo_targeting["device"] = {
            "deviceTypes": [
                _map_device_type(d)
                for d in adcp_targeting["device_type_any_of"]
            ]
        }

    # Audience segments
    if "audience_segment_ids" in adcp_targeting:
        yahoo_targeting["audiences"] = {
            "include": [
                {"segmentId": seg_id}
                for seg_id in adcp_targeting["audience_segment_ids"]
            ]
        }

    # Time of day / dayparting
    if "time_of_day_any_of" in adcp_targeting:
        yahoo_targeting["dayparting"] = _format_dayparting(
            adcp_targeting["time_of_day_any_of"]
        )

    return yahoo_targeting


def _get_geo_type(geo_code: str) -> str:
    """Determine geo type from code format."""
    if len(geo_code) == 2:
        return "COUNTRY"
    elif len(geo_code) == 5 and "-" in geo_code:
        return "REGION"
    elif geo_code.isdigit():
        return "DMA"
    else:
        return "CITY"


def _map_device_type(adcp_device: str) -> str:
    """Map AdCP device type to Yahoo DSP device type."""
    mapping = {
        "desktop": "DESKTOP",
        "mobile": "MOBILE",
        "tablet": "TABLET",
        "ctv": "CONNECTED_TV",
        "connected_tv": "CONNECTED_TV",
    }
    return mapping.get(adcp_device.lower(), "ALL")


def _format_dayparting(time_periods: list[dict]) -> dict[str, Any]:
    """Format time of day targeting for Yahoo DSP.

    Args:
        time_periods: List of time period specifications

    Returns:
        Yahoo DSP dayparting object
    """
    # Yahoo uses a different format - hours per day of week
    # This is a simplified conversion
    dayparting = {"enabled": True, "schedule": []}

    for period in time_periods:
        days = period.get("days", ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"])
        start_hour = period.get("start_hour", 0)
        end_hour = period.get("end_hour", 24)

        for day in days:
            dayparting["schedule"].append({
                "day": day.upper(),
                "startHour": start_hour,
                "endHour": end_hour,
            })

    return dayparting


def format_creative_for_yahoo(adcp_creative: dict[str, Any]) -> dict[str, Any]:
    """Convert AdCP creative to Yahoo DSP creative format.

    Args:
        adcp_creative: AdCP creative specification

    Returns:
        Yahoo DSP creative object
    """
    creative_type = _determine_creative_type(adcp_creative)

    yahoo_creative = {
        "name": adcp_creative.get("name", "Untitled Creative"),
        "type": creative_type,
        "status": "ACTIVE",
    }

    # Add type-specific fields
    if creative_type == "DISPLAY":
        yahoo_creative.update({
            "width": adcp_creative.get("width", 300),
            "height": adcp_creative.get("height", 250),
            "clickUrl": adcp_creative.get("click_url", ""),
            "imageUrl": adcp_creative.get("asset_url", ""),
        })
    elif creative_type == "VIDEO":
        yahoo_creative.update({
            "vastUrl": adcp_creative.get("vast_url", ""),
            "duration": adcp_creative.get("duration", 30),
        })
    elif creative_type == "NATIVE":
        yahoo_creative.update({
            "headline": adcp_creative.get("headline", ""),
            "description": adcp_creative.get("description", ""),
            "iconUrl": adcp_creative.get("icon_url", ""),
            "imageUrl": adcp_creative.get("image_url", ""),
            "clickUrl": adcp_creative.get("click_url", ""),
        })

    return yahoo_creative


def _determine_creative_type(creative: dict[str, Any]) -> str:
    """Determine Yahoo DSP creative type from AdCP creative."""
    if creative.get("vast_url"):
        return "VIDEO"
    elif creative.get("headline") or creative.get("description"):
        return "NATIVE"
    else:
        return "DISPLAY"

