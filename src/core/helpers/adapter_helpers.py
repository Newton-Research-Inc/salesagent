"""Adapter instance creation and configuration helpers."""

import os
from typing import Any

from sqlalchemy import select

from src.adapters.google_ad_manager import GoogleAdManager
from src.adapters.kevel import Kevel
from src.adapters.mock_ad_server import MockAdServer as MockAdServerAdapter
from src.adapters.triton_digital import TritonDigital
from src.adapters.yahoo_dsp_simulated import YahooDSP
from src.adapters.yahoo_dsp_live import YahooDSPLive
from src.core.config_loader import get_current_tenant
from src.core.database.database_session import get_db_session
from src.core.database.models import AdapterConfig
from src.core.schemas import Principal


def get_adapter(
    principal: Principal, dry_run: bool = False, testing_context: Any = None
) -> MockAdServerAdapter | GoogleAdManager | Kevel | TritonDigital | YahooDSP | YahooDSPLive:
    """Get the appropriate adapter instance for the selected adapter type."""
    import logging

    logger = logging.getLogger(__name__)

    # Get tenant and adapter config from database
    tenant = get_current_tenant()
    selected_adapter = tenant.get("ad_server", "mock")
    logger.info(f"[ADAPTER_SELECT] Initial selected_adapter from tenant.ad_server: {selected_adapter}")

    # Get adapter config from adapter_config table
    with get_db_session() as session:
        stmt = select(AdapterConfig).filter_by(tenant_id=tenant["tenant_id"])
        config_row = session.scalars(stmt).first()

        adapter_config: dict[str, Any] = {"enabled": True}
        if config_row:
            adapter_type = config_row.adapter_type
            logger.info(f"[ADAPTER_SELECT] adapter_type from AdapterConfig: {adapter_type}")
            # Use adapter_type from AdapterConfig as the source of truth
            if adapter_type:
                selected_adapter = adapter_type
                logger.info(f"[ADAPTER_SELECT] Using AdapterConfig.adapter_type: {selected_adapter}")
            if adapter_type == "mock":
                adapter_config["dry_run"] = config_row.mock_dry_run or False
                # Default to True (require approval) for safety
                adapter_config["manual_approval_required"] = (
                    config_row.mock_manual_approval_required
                    if config_row.mock_manual_approval_required is not None
                    else True
                )
            elif adapter_type == "google_ad_manager":
                adapter_config["network_code"] = config_row.gam_network_code or ""
                adapter_config["refresh_token"] = config_row.gam_refresh_token or ""
                adapter_config["trafficker_id"] = config_row.gam_trafficker_id or ""
                # Default to True (require approval) for safety
                adapter_config["manual_approval_required"] = (
                    config_row.gam_manual_approval_required
                    if config_row.gam_manual_approval_required is not None
                    else True
                )

                # Get advertiser_id from principal's platform_mappings (per-principal, not tenant-level)
                # Support both old format (nested under "google_ad_manager") and new format (root "gam_advertiser_id")
                advertiser_id: str | None = None
                if principal.platform_mappings:
                    # Try nested format first
                    gam_mappings = principal.platform_mappings.get("google_ad_manager", {})
                    advertiser_id = gam_mappings.get("advertiser_id")
                    logger.info(
                        f"[ADAPTER_CONFIG] principal_id={principal.principal_id}, platform_mappings={principal.platform_mappings}, gam_mappings={gam_mappings}, advertiser_id={advertiser_id}"
                    )

                    # Fall back to root-level format if nested not found
                    if not advertiser_id:
                        advertiser_id = principal.platform_mappings.get("gam_advertiser_id")
                        logger.info(f"[ADAPTER_CONFIG] Fell back to root-level gam_advertiser_id: {advertiser_id}")

                    adapter_config["company_id"] = advertiser_id
                    logger.info(f"[ADAPTER_CONFIG] Set adapter_config['company_id']={advertiser_id}")
                else:
                    adapter_config["company_id"] = None
                    logger.info("[ADAPTER_CONFIG] principal.platform_mappings is None/empty, set company_id=None")
            elif adapter_type == "kevel":
                adapter_config["network_id"] = config_row.kevel_network_id or ""
                adapter_config["api_key"] = config_row.kevel_api_key or ""
                # Default to True (require approval) for safety
                adapter_config["manual_approval_required"] = (
                    config_row.kevel_manual_approval_required
                    if config_row.kevel_manual_approval_required is not None
                    else True
                )
            elif adapter_type == "triton":
                adapter_config["station_id"] = config_row.triton_station_id or ""
                adapter_config["api_key"] = config_row.triton_api_key or ""

    if not selected_adapter:
        # Default to mock if no adapter specified
        selected_adapter = "mock"
        if not adapter_config:
            adapter_config = {"enabled": True}

    # Create the appropriate adapter instance with tenant_id and testing context
    tenant_id = tenant["tenant_id"]
    logger.info(f"[ADAPTER_SELECT] FINAL selected_adapter: {selected_adapter}")
    if selected_adapter == "mock":
        logger.info("[ADAPTER_SELECT] Instantiating MockAdServerAdapter")
        return MockAdServerAdapter(
            adapter_config, principal, dry_run, tenant_id=tenant_id, strategy_context=testing_context
        )
    elif selected_adapter == "google_ad_manager":
        # network_code is required for GoogleAdManager
        network_code = adapter_config.get("network_code")
        if not network_code or not isinstance(network_code, str):
            raise ValueError("network_code is required for GoogleAdManager adapter")

        logger.info("[ADAPTER_SELECT] Instantiating GoogleAdManager")
        logger.info(
            f"[ADAPTER_SELECT] GAM params: network_code={adapter_config.get('network_code')}, advertiser_id={adapter_config.get('company_id')}, trafficker_id={adapter_config.get('trafficker_id')}, dry_run={dry_run}"
        )
        return GoogleAdManager(
            adapter_config,
            principal,
            network_code=network_code,
            advertiser_id=adapter_config.get("company_id"),
            trafficker_id=adapter_config.get("trafficker_id"),
            dry_run=dry_run,
            tenant_id=tenant_id,
        )
    elif selected_adapter == "kevel":
        return Kevel(adapter_config, principal, dry_run, tenant_id=tenant_id)
    elif selected_adapter in ["triton", "triton_digital"]:
        return TritonDigital(adapter_config, principal, dry_run, tenant_id=tenant_id)
    elif selected_adapter == "yahoo_dsp":
        logger.info("[ADAPTER_SELECT] Instantiating YahooDSP (simulated)")
        return YahooDSP(adapter_config, principal, dry_run, tenant_id=tenant_id)
    elif selected_adapter == "yahoo_dsp_live":
        logger.info("[ADAPTER_SELECT] Instantiating YahooDSPLive (real API)")
        
        # Get Yahoo DSP credentials from environment variables (injected via ECS secrets)
        # These are set in the ECS task definition from AWS Secrets Manager
        yahoo_config = {
            "client_id": os.environ.get("YAHOO_DSP_CLIENT_ID", ""),
            "client_secret": os.environ.get("YAHOO_DSP_CLIENT_SECRET", ""),
            "seat_id": os.environ.get("YAHOO_DSP_SEAT_ID", ""),
            "advertiser_id": os.environ.get("YAHOO_DSP_ADVERTISER_ID", ""),
            # TEST MODE ENABLED BY DEFAULT for safety
            # Set YAHOO_DSP_TEST_MODE=false in production when ready to go live
            "test_mode": os.environ.get("YAHOO_DSP_TEST_MODE", "true").lower() == "true",
        }
        
        # Override with principal's platform_mappings if available (skip placeholder values)
        if principal.platform_mappings:
            yahoo_mappings = principal.platform_mappings.get("yahoo_dsp_live", {})
            adv_id = yahoo_mappings.get("advertiser_id", "")
            seat = yahoo_mappings.get("seat_id", "")
            # Only use platform_mappings if they're real values, not placeholders
            if adv_id and "placeholder" not in adv_id.lower():
                yahoo_config["advertiser_id"] = adv_id
            if seat and "placeholder" not in seat.lower():
                yahoo_config["seat_id"] = seat
        
        logger.info(
            f"[ADAPTER_SELECT] Yahoo DSP Live config: seat_id={yahoo_config.get('seat_id')}, "
            f"advertiser_id={yahoo_config.get('advertiser_id')}, test_mode={yahoo_config.get('test_mode')}"
        )
        
        return YahooDSPLive(
            yahoo_config,
            principal,
            dry_run=dry_run,
            test_mode=yahoo_config.get("test_mode", True),
            tenant_id=tenant_id,
        )
    else:
        # Default to mock for unsupported adapters
        logger.warning(f"[ADAPTER_SELECT] Unknown adapter '{selected_adapter}', falling back to MockAdServer")
        return MockAdServerAdapter(
            adapter_config, principal, dry_run, tenant_id=tenant_id, strategy_context=testing_context
        )
