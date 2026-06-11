# Optimal Tankless — Home Assistant (HACS)

Unofficial Home Assistant integration for [Optimal° Opti+](https://itsoptimal.com/) Wi‑Fi tankless water heaters.

## Setup — serial number only

No Optimal° app login is required. The integration talks to Optimal's hardware backend using your heater **serial number** (from the unit label or app).

Example serial: `1212230005`

1. Install the integration (HACS custom repo or copy `custom_components/optimaltankless`)
2. Restart Home Assistant
3. **Settings → Devices & Services → Add Integration → Optimal Tankless**
4. Enter your serial number

## Features

- Water heater setpoint control
- Vacation mode (via device `configData` flags)
- Live telemetry: inlet/outlet temp, flow, power, voltage, diagnostics
- Cloud polling (default 30s, configurable 15–300s)

## Polling interval

Set when adding the integration, or later via **Configure** on the integration page (15–300 seconds).

Automations and other integrations can also change it:

```yaml
# Service call
service: optimaltankless.set_scan_interval
data:
  scan_interval: 60
target:
  config_entry_id: YOUR_ENTRY_ID

# Or the generic config entry action
action: config_entries.update
target:
  config_entry_id: YOUR_ENTRY_ID
data:
  options:
    scan_interval: 60
```

Changes apply immediately without restarting Home Assistant.

## API

Uses `https://hwbe.itsoptimal.com` — documented at [/api](https://hwbe.itsoptimal.com/api).

| Action | Endpoint |
|--------|----------|
| Live status | `GET /client/device/{serial}/snapshots` |
| Read command | `GET /client/device/{serial}/commands` |
| Set temp / vacation | `POST /client/device/{serial}/commands` |

## Security note

The Optimal hardware API currently allows read/write to any device if you know its serial number. Treat your serial as sensitive. Anyone who can reach the API and guess serials could theoretically control units — this is an Optimal platform issue, not something HA can fix.

## Developer testing

```powershell
pip install aiohttp
python tools/probe_api.py status 1212230005
python tools/probe_api.py command 1212230005
```

## Disclaimer

Community integration — not affiliated with Its Optimal LLC. Unofficial use of a public API; behaviour may change without notice.

## Support

- Optimal product support: Support@itsoptimal.com / 386-678-4625
- Integration issues: GitHub Issues on this repo
