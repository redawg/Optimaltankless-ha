# Reverse Engineering Notes — Optimal Tankless

## Discovery summary (completed)

We did **not** need traffic capture to find the backend. Its Optimal exposes a public Swagger UI:

| Service | URL | Role |
|---------|-----|------|
| **HWBE** (Hardware Backend) | https://hwbe.itsoptimal.com | Primary REST API — **use this in HA** |
| **BFF** | https://bff.itsoptimal.com | Mobile app backend-for-frontend |
| OpenAPI JSON | https://hwbe.itsoptimal.com/api-json | Full machine-readable spec |
| Swagger UI | https://hwbe.itsoptimal.com/api | Human-readable docs |

The Android app (`com.itsoptimal.optimalapp`) is React Native and references `bff.itsoptimal.com`; the BFF proxies the same domain model as HWBE.

## Authentication

```
POST https://hwbe.itsoptimal.com/auth/login
Content-Type: application/json

{"username": "<email>", "password": "<password>"}
```

Returns a JWT used as:

```
Authorization: Bearer <token>
```

The API schema uses **`username`**, not `email` (your Optimal° app email works as the username).

## Device identity

Devices are keyed by **`serialNumber`** (numeric), visible on the unit label and in the Optimal° app.

## Integration endpoints used by HA

| Action | Method | Path |
|--------|--------|------|
| Login | POST | `/auth/login` |
| Profile (device list if exposed) | GET | `/auth/profile` |
| Live telemetry | GET | `/client/device/{serialNumber}/snapshots` |
| Read pending command | GET | `/client/device/{serialNumber}/commands` |
| Set temperature / vacation | POST | `/client/device/{serialNumber}/commands` |

### Command body (`SetDeviceCommandRequestDto`)

```json
{
  "targetTemperature": 120,
  "configData": 0,
  "voltageScale": 1
}
```

- **Temperature** → `targetTemperature`
- **Vacation mode** → bit flag in `configData` (integration uses `VACATION_MODE_CONFIG_BIT = 0x01` — validate against your unit)

### Snapshot fields (`DeviceSnapshot`)

| API field | HA entity |
|-----------|-----------|
| `outputTemp` | Outlet temperature |
| `inputTemp` | Inlet temperature |
| `targetTemp` | Target (fallback if no command) |
| `flowRate` | Flow rate (GPM) |
| `heaterPower` | Power draw |
| `acVoltage` | Input voltage |
| `heatCapacity` | Heater capacity |
| `flowCapacity` | Available flow |
| `heater` | Heating binary sensor |
| `error` / `heaterError` / `sensorError` | Error code |

## Validate with CLI

```powershell
$env:OPTIMAL_USERNAME = "you@example.com"
$env:OPTIMAL_PASSWORD = "your-password"
python tools/probe_endpoints.py login

$env:OPTIMAL_TOKEN = "<paste access token from login response>"
python tools/probe_endpoints.py

$env:OPTIMAL_SERIAL = "123456789"
python tools/probe_api.py status $env:OPTIMAL_SERIAL
```

## Optional: traffic capture

Traffic capture is still useful to:

- Confirm the exact login JSON response field names (`access_token` vs `accessToken`)
- Verify the vacation `configData` bit mask
- See if `/auth/profile` returns a device list for your account

See the checklist below if app behaviour diverges from HWBE.

## Open questions

1. **`/auth/profile` shape** — device list field names may vary; HA falls back to manual serial entry.
2. **`configData` vacation bit** — default `0x01`; toggle in the app and compare `GET .../commands` if vacation behaves incorrectly.
3. **Token refresh** — `/auth/refresh` may or may not exist; reauth flow handles expiry.

## Capture checklist (optional validation)

```
[x] Login request/response
[ ] Device list from /auth/profile
[x] Status poll endpoint
[x] Set temperature mutation
[ ] Vacation mode bit confirmed
[x] Base URL confirmed (hwbe.itsoptimal.com)
```

## References

- OpenAPI spec saved at `docs/openapi.json`
- APK analysis scripts in `tools/`
