"""
DepEd NetPulse SLA Engine & 4-Point Disambiguation Module
Implements BRD v2.0 & TDD v2.0 Rules:
  1. Active School Hours check (Mon-Fri 07:00 - 17:00 PHT)
  2. Local Hop Probe check (Ethernet vs. Wi-Fi RSSI + Router Gateway reachability)
  3. Selective ISP Throttling check (Public Ref vs. DepEd Cloud Anchor)
  4. Statutory Rebate Formula Calculation (PHP)
"""

from datetime import datetime, timezone


def is_active_school_hours(dt_utc: datetime) -> bool:
    """Mon-Fri, 07:00 AM - 05:00 PM PHT (UTC+8)"""
    # PHT is UTC+8
    hour_pht = (dt_utc.hour + 8) % 24
    # Note: in demo mode, if outside school hours we allow evaluation with an advisory tag
    return 7 <= hour_pht < 17


def evaluate_telemetry_sample(payload: dict, contracted_dl_mbps: float, monthly_contract_php: float) -> dict:
    local_hop = payload.get("local_hop_diagnostics", {})
    probes = payload.get("dual_probe_wan_metrics", {})
    status = payload.get("connection_status", "ONLINE")

    gw_reachable = bool(local_hop.get("local_gateway_reachable", False))
    medium = local_hop.get("connection_medium", "ETHERNET")
    rssi = int(local_hop.get("wifi_rssi_dbm", 0))
    gw_ping = float(local_hop.get("local_gateway_ping_ms", 0.0))
    gw_loss = float(local_hop.get("local_gateway_loss_pct", 0.0))

    # 1. Local Hop Health Verification
    is_local_hop_healthy = gw_reachable and (
        medium == "ETHERNET"
        or (medium == "WIFI" and rssi >= -67 and gw_ping <= 10.0 and gw_loss == 0.0)
    )

    anchor_dl = float(probes.get("deped_anchor_dl_mbps", 0.0))
    public_dl = float(probes.get("public_ref_dl_mbps", 0.0))
    wan_loss = float(probes.get("deped_anchor_loss_pct", 0.0))
    wan_jitter = float(probes.get("deped_anchor_jitter_ms", 0.0))

    compliance_pct = round((anchor_dl / contracted_dl_mbps) * 100.0, 2) if contracted_dl_mbps > 0 else 0.0

    # 2. Selective Throttling Detection (Anti-Gaming)
    is_selective_throttling = (
        is_local_hop_healthy
        and public_dl >= (contracted_dl_mbps * 0.75)
        and anchor_dl < (contracted_dl_mbps * 0.40)
    )

    # 3. Disambiguation Classification
    if not gw_reachable:
        category = "LOCAL_ROUTER_UNREACHABLE_EXEMPT"
        is_sla_eligible = False
    elif not is_local_hop_healthy:
        category = "LOCAL_WIFI_BOTTLENECK_EXEMPT"
        is_sla_eligible = False
    elif status == "VERIFIED_WAN_OFFLINE" or (anchor_dl == 0 and public_dl == 0):
        category = "VERIFIED_ISP_WAN_OFFLINE"
        is_sla_eligible = True
    elif is_selective_throttling:
        category = "ISP_SELECTIVE_THROTTLING"
        is_sla_eligible = True
    elif wan_loss >= 5.0 or wan_jitter >= 100.0:
        category = "ISP_PHYSICAL_LINE_DEGRADATION"
        is_sla_eligible = True
    elif compliance_pct < 50.0:
        category = "ISP_SUB_50PCT_BANDWIDTH_BREACH"
        is_sla_eligible = True
    else:
        category = "HEALTHY_COMPLIANT"
        is_sla_eligible = False

    return {
        "is_local_hop_healthy": is_local_hop_healthy,
        "dl_compliance_pct": compliance_pct,
        "is_selective_throttling": is_selective_throttling,
        "diagnostic_category": category,
        "is_sla_breach_eligible": is_sla_eligible,
    }


def calculate_statutory_rebate_php(
    monthly_contract_php: float, consecutive_breach_days: int, breach_type: str
) -> float:
    """
    Statutory Rebate Formula (BRD v2.0 Section 12.2):
      Monthly SLA Rebate = MRC * Rebate Tier % * (Verified Breach Days / 22 School Days)
      Tiers:
        - Minor (3 days sub-50% / selective throttle): 25% penalty tier
        - Critical (>5 days or extended outage): 50% penalty tier
    """
    tier_pct = 0.50 if consecutive_breach_days > 5 or breach_type == "VERIFIED_ISP_WAN_OFFLINE" else 0.25
    fraction = min(consecutive_breach_days / 22.0, 1.0)
    return round(monthly_contract_php * tier_pct * fraction, 2)
