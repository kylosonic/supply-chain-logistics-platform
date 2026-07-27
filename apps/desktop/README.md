# FreightPilot Desktop

Desktop shell for logistics operators. This Electron app hosts the ops console login and dashboard experience.

## Run locally

```bash
npm install
npm run dev
```

The desktop package now verifies the Electron runtime binary during install and before startup.

If you want to validate the runtime without launching the app:

```bash
npm run doctor
```

Optional environment variable:

- `OPS_CONSOLE_URL` (default: `http://localhost:5173/login`)
- `PRODUCT_SIGNUP_URL` (default: hosted product signup URL)
- `DOCS_URL` (default: hosted product docs URL)

## Onboarding experience

- First launch opens a setup workspace instead of jumping straight to login.
- Teams can save their production console URL, product signup URL, and docs URL.
- Built-in connection test validates the console endpoint before dispatchers begin work.
- One-click "Open control tower" launches the console in a dedicated app window.
- Progress checklist tracks account creation, team invite, and data import readiness.

## Notes

- This shell opens external links in the system browser.
- Node integration is disabled and context isolation is enabled.
- If Electron install artifacts are missing on a machine, startup automatically repairs the binary.
