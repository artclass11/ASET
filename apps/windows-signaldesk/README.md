# ASET SignalDesk — Windows Desktop

Native Windows desktop client for the ASET SignalDesk research service.

## Architecture

Windows desktop (Tauri) → ASET SignalDesk API → Alpha Vantage.

The desktop application never contains an Alpha Vantage API key. Set the API key on the ASET SignalDesk server instead.

## Windows build

Tauri uses Microsoft C++ Build Tools, Rust and WebView2 on Windows. Windows 10/11 generally include WebView2.

Run:

```powershell
.\build-windows.ps1
```

Or:

```powershell
npm install
npm run tauri build
```

The generated installers are under `src-tauri/target/release/bundle/`:

- NSIS setup executable: `*-setup.exe`
- MSI installer: `*.msi`

## Development

In one terminal:

```powershell
cd ..\live-signaldesk
$env:ALPHAVANTAGE_API_KEY="YOUR_SERVER_KEY"
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
npm install
npm run tauri dev
```

The desktop client defaults to `http://127.0.0.1:8000`.

## Self-hosted production

Deploy `apps/live-signaldesk` behind HTTPS on your own VPS or open-source deployment platform. Open **Connection** inside the desktop client and enter the API base URL.

Before public/paid use, put authentication, rate limiting, quota controls and TLS at the API layer.

## Commercial

Licensing and implementation support:
- https://www.instagram.com/amormagics/
- https://ig.me/m/amormagics/

Research tooling only; not investment advice.
