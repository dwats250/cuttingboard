---
name: notifications
description: "Skill for the Notifications area of cuttingboard. 47 symbols across 5 files."
---

# Notifications

47 symbols | 5 files | Cohesion: 89%

## When to Use

- Working with code in `cuttingboard/`
- Understanding how test_failure_notification_body_has_no_repeated_branding, test_format_hourly_stay_flat_title_and_body, test_format_hourly_no_setup_title_and_body work
- Modifying notifications-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `cuttingboard/notifications/formatter.py` | format_ntfy_alert, _format_hourly, _format_run_summary, _format_intraday, _format_failure (+26) |
| `tests/test_hourly_alert.py` | _regime, _validation, _router_state, _hourly_event, test_format_hourly_stay_flat_title_and_body (+7) |
| `cuttingboard/notifications/__init__.py` | format_hourly_notification, format_failure_notification |
| `tests/test_notifications.py` | test_failure_notification_body_has_no_repeated_branding |
| `cuttingboard/watch.py` | regime_bias |

## Entry Points

Start here when exploring this area:

- **`test_failure_notification_body_has_no_repeated_branding`** (Function) — `tests/test_notifications.py:195`
- **`test_format_hourly_stay_flat_title_and_body`** (Function) — `tests/test_hourly_alert.py:240`
- **`test_format_hourly_no_setup_title_and_body`** (Function) — `tests/test_hourly_alert.py:247`
- **`test_format_hourly_setup_ready_title`** (Function) — `tests/test_hourly_alert.py:254`
- **`test_format_hourly_required_fields_present`** (Function) — `tests/test_hourly_alert.py:264`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_failure_notification_body_has_no_repeated_branding` | Function | `tests/test_notifications.py` | 195 |
| `test_format_hourly_stay_flat_title_and_body` | Function | `tests/test_hourly_alert.py` | 240 |
| `test_format_hourly_no_setup_title_and_body` | Function | `tests/test_hourly_alert.py` | 247 |
| `test_format_hourly_setup_ready_title` | Function | `tests/test_hourly_alert.py` | 254 |
| `test_format_hourly_required_fields_present` | Function | `tests/test_hourly_alert.py` | 264 |
| `test_format_hourly_system_halt_routes_to_halt_format` | Function | `tests/test_hourly_alert.py` | 275 |
| `test_hourly_sends_exactly_once_stay_flat` | Function | `tests/test_hourly_alert.py` | 321 |
| `test_hourly_sends_exactly_once_system_halted` | Function | `tests/test_hourly_alert.py` | 329 |
| `regime_bias` | Function | `cuttingboard/watch.py` | 444 |
| `format_ntfy_alert` | Function | `cuttingboard/notifications/formatter.py` | 58 |
| `format_hourly_notification` | Function | `cuttingboard/notifications/__init__.py` | 157 |
| `format_failure_notification` | Function | `cuttingboard/notifications/__init__.py` | 180 |
| `_regime` | Function | `tests/test_hourly_alert.py` | 26 |
| `_validation` | Function | `tests/test_hourly_alert.py` | 45 |
| `_router_state` | Function | `tests/test_hourly_alert.py` | 102 |
| `_hourly_event` | Function | `tests/test_hourly_alert.py` | 112 |
| `_patch_pipeline_stay_flat` | Function | `tests/test_hourly_alert.py` | 308 |
| `_format_hourly` | Function | `cuttingboard/notifications/formatter.py` | 80 |
| `_format_run_summary` | Function | `cuttingboard/notifications/formatter.py` | 117 |
| `_format_intraday` | Function | `cuttingboard/notifications/formatter.py` | 125 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Deliver_html → Regime_bias` | cross_community | 5 |
| `_format_run_summary → Regime_bias` | intra_community | 5 |
| `_send_alert → _mode_label` | cross_community | 5 |
| `_send_alert → _time_line` | cross_community | 5 |
| `_send_alert → _clean_reason` | cross_community | 5 |
| `_send_alert → _session_posture` | cross_community | 5 |
| `_send_alert → _vix_line` | cross_community | 5 |
| `_format_setup_forming → _clean_reason` | cross_community | 4 |
| `_format_session_check → _clean_reason` | intra_community | 4 |
| `Format_hourly_notification → _mode_label` | intra_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 2 calls |

## How to Explore

1. `gitnexus_context({name: "test_failure_notification_body_has_no_repeated_branding"})` — see callers and callees
2. `gitnexus_query({query: "notifications"})` — find related execution flows
3. Read key files listed above for implementation details
