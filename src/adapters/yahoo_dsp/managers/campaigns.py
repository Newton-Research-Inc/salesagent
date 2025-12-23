"""
Yahoo DSP Campaign Manager

Manages Yahoo DSP Campaigns (equivalent to GAM Orders / AdCP Media Buys).
Reference: https://help.yahooinc.com/dsp-api/docs/campaigns
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.adapters.yahoo_dsp.utils.constants import YahooToAdCPStatusMapping
from src.adapters.yahoo_dsp.utils.formatters import (
    format_budget_for_yahoo,
    format_date_for_yahoo,
    parse_budget_from_yahoo,
)

if TYPE_CHECKING:
    from src.adapters.yahoo_dsp.client import YahooDSPClient

logger = logging.getLogger(__name__)


class YahooDSPCampaignManager:
    """Manages Yahoo DSP Campaign operations.

    Yahoo DSP Campaign Object:
    - Contains multiple Lines (line items)
    - Has overall budget and flight dates
    - Associated with a single Advertiser (accountId)

    Mapping to AdCP:
    - Campaign → Media Buy / Order
    - Lines within Campaign → Packages
    
    API Endpoints:
    - GET /traffic/campaigns - List campaigns (filter by accountId)
    - GET /traffic/campaigns/{id} - Get single campaign
    - POST /traffic/campaigns - Create campaign
    - PUT /traffic/campaigns/{id} - Update campaign
    """

    def __init__(self, client: "YahooDSPClient", advertiser_id: str):
        """Initialize campaign manager.

        Args:
            client: Yahoo DSP API client
            advertiser_id: Yahoo DSP advertiser/account ID for all operations
        """
        self.client = client
        self.advertiser_id = advertiser_id

    def create_campaign(
        self,
        name: str,
        budget: int,
        start_date: datetime,
        end_date: datetime,
        *,
        status: str = "ACTIVE",
        pacing_type: str = "EVEN",
        goal_type: str = "IMPRESSION",
        goal_value: int | None = None,
        currency: str = "USD",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new Yahoo DSP Campaign.

        Args:
            name: Campaign name
            budget: Total budget in cents
            start_date: Campaign start date
            end_date: Campaign end date
            status: Campaign status - "ACTIVE" or "INACTIVE" (use INACTIVE for testing)
            pacing_type: EVEN or ACCELERATED
            goal_type: IMPRESSION, CLICK, CONVERSION, etc.
            goal_value: Target goal value (e.g., number of impressions). Auto-calculated if not provided.
            currency: Currency code (default USD)
            metadata: Additional metadata to store

        Returns:
            Created campaign object with ID

        Raises:
            YahooDSPAPIError: On API failure
        """
        logger.info(f"Creating Yahoo DSP campaign: {name} (status: {status}, budget: {budget} cents)")

        # Calculate goal_value if not provided
        # For impression goals, estimate based on budget assuming ~$5 CPM
        if goal_value is None:
            if goal_type == "IMPRESSION":
                # budget is in cents, assume $5 CPM = 500 cents per 1000 impressions
                # impressions = (budget_cents / 500) * 1000
                goal_value = max(1000, (budget * 1000) // 500)
            elif goal_type == "CLICK":
                # Assume $1 CPC = 100 cents per click
                goal_value = max(10, budget // 100)
            else:
                # Default to 1000 for other goal types
                goal_value = 1000

        campaign_data = {
            "accountId": int(self.advertiser_id),  # Yahoo uses accountId (integer)
            "name": name,
            "status": status,
            "budget": format_budget_for_yahoo(budget),
            "startDate": format_date_for_yahoo(start_date),
            "endDate": format_date_for_yahoo(end_date),
            "pacingType": pacing_type,
            "goalType": goal_type,
            "goalValue": goal_value,
        }

        # NOTE: Removed externalId and labels as they may not be supported
        # and were causing 500 errors. Can add back once basic creation works.

        # Log full request for debugging
        logger.info(f"Yahoo DSP campaign request payload: {campaign_data}")

        response = self.client.post("/traffic/campaigns", campaign_data)

        # Yahoo returns {"response": {...}, "errors": null, "timeStamp": "..."}
        campaign = response.get("response", response)
        logger.info(f"Created campaign with ID: {campaign.get('id')}")
        return campaign

    def get_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Get campaign by ID.

        Args:
            campaign_id: Yahoo DSP campaign ID

        Returns:
            Campaign object

        Raises:
            YahooDSPNotFoundError: If campaign not found
        """
        response = self.client.get(f"/traffic/campaigns/{campaign_id}")
        # Return the response data (may be wrapped in {"response": ...})
        return response.get("response", response)

    def list_campaigns(
        self,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List campaigns for advertiser.

        Args:
            status: Filter by status (ACTIVE, PAUSED, etc.)
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of campaign objects
        """
        params: dict[str, Any] = {
            "accountId": int(self.advertiser_id),  # Yahoo uses accountId
        }

        if status:
            params["status"] = status
            
        # Note: Yahoo DSP pagination may differ - adjust as needed
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset

        response = self.client.get("/traffic/campaigns", params=params)
        
        # Yahoo returns {"response": [...], "errors": null, "timeStamp": "..."}
        return response.get("response", [])

    def update_campaign(
        self,
        campaign_id: str,
        *,
        name: str | None = None,
        budget: int | None = None,
        status: str | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Update campaign properties.

        Args:
            campaign_id: Campaign ID to update
            name: New name (optional)
            budget: New budget in cents (optional)
            status: New status (optional)
            end_date: New end date (optional)

        Returns:
            Updated campaign object

        Raises:
            YahooDSPAPIError: On API failure
        """
        logger.info(f"Updating Yahoo DSP campaign: {campaign_id}")

        update_data: dict[str, Any] = {}

        if name is not None:
            update_data["name"] = name

        if budget is not None:
            update_data["budget"] = format_budget_for_yahoo(budget)

        if status is not None:
            update_data["status"] = status

        if end_date is not None:
            update_data["endDate"] = format_date_for_yahoo(end_date)

        response = self.client.put(f"/traffic/campaigns/{campaign_id}", update_data)
        return response.get("response", response)

    def pause_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Pause a campaign.

        Args:
            campaign_id: Campaign ID to pause

        Returns:
            Updated campaign object
        """
        return self.update_campaign(campaign_id, status="PAUSED")

    def activate_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Activate a campaign.

        Args:
            campaign_id: Campaign ID to activate

        Returns:
            Updated campaign object
        """
        return self.update_campaign(campaign_id, status="ACTIVE")

    def delete_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Delete (archive) a campaign.

        Args:
            campaign_id: Campaign ID to delete

        Returns:
            Deletion confirmation
        """
        logger.info(f"Deleting Yahoo DSP campaign: {campaign_id}")
        response = self.client.delete(f"/traffic/campaigns/{campaign_id}")
        return response.get("response", response)

    def get_campaign_status_for_adcp(self, campaign_id: str) -> dict[str, Any]:
        """Get campaign status formatted for AdCP response.

        Args:
            campaign_id: Campaign ID

        Returns:
            AdCP-formatted status information
        """
        campaign = self.get_campaign(campaign_id)

        yahoo_status = campaign.get("status", "UNKNOWN")
        adcp_status = YahooToAdCPStatusMapping.campaign(yahoo_status)

        return {
            "media_buy_id": campaign_id,
            "platform_status": yahoo_status,
            "adcp_status": adcp_status,
            "name": campaign.get("name", ""),
            "budget_spent": parse_budget_from_yahoo(campaign.get("spentBudget", {})),
            "budget_total": parse_budget_from_yahoo(campaign.get("budget", {})),
            "start_date": campaign.get("startDate"),
            "end_date": campaign.get("endDate"),
        }
