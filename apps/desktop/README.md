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

## Notes

- This shell opens external links in the system browser.
- Node integration is disabled and context isolation is enabled.
- If Electron install artifacts are missing on a machine, startup automatically repairs the binary.
