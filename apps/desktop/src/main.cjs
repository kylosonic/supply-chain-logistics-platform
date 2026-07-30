const { app, BrowserWindow, ipcMain, Menu, shell } = require('electron');
const fs = require('fs');
const path = require('path');

const DEFAULT_CONFIG = {
  opsConsoleUrl: process.env.OPS_CONSOLE_URL || 'https://ops-console-azure.vercel.app/login',
  productSignupUrl: process.env.PRODUCT_SIGNUP_URL || 'https://product-web-chi.vercel.app#signup',
  docsUrl: process.env.DOCS_URL || 'https://product-web-chi.vercel.app',
  onboarding: {
    createdAccount: false,
    connectedConsole: false,
    invitedTeam: false,
    importedData: false,
    launchedLive: false,
    roleDispatcherReady: false,
    roleDataReady: false,
    roleSecurityReady: false,
    activeStep: 0,
  },
};

let setupWindow = null;
let consoleWindow = null;

/* ── Window state persistence ───────────────────────────────── */

function getWindowStatePath() {
  return path.join(app.getPath('userData'), 'freightpilot-window-state.json');
}

function loadWindowState(defaults) {
  try {
    const statePath = getWindowStatePath();
    if (fs.existsSync(statePath)) {
      const raw = JSON.parse(fs.readFileSync(statePath, 'utf8'));
      return {
        x: typeof raw.x === 'number' ? raw.x : undefined,
        y: typeof raw.y === 'number' ? raw.y : undefined,
        width: typeof raw.width === 'number' && raw.width >= 800 ? raw.width : defaults.width,
        height: typeof raw.height === 'number' && raw.height >= 600 ? raw.height : defaults.height,
      };
    }
  } catch {
    // Ignore errors - use defaults
  }
  return defaults;
}

function saveWindowState(win) {
  if (!win || win.isDestroyed()) return;
  try {
    const bounds = win.getBounds();
    fs.writeFileSync(getWindowStatePath(), JSON.stringify(bounds, null, 2), 'utf8');
  } catch {
    // Ignore write errors
  }
}

/* ── Config management ──────────────────────────────────────── */

function getConfigPath() {
  return path.join(app.getPath('userData'), 'freightpilot-desktop-config.json');
}

function sanitizeUrl(value, fallback) {
  try {
    const parsed = new URL(value);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return fallback;
    }
    return parsed.toString();
  } catch {
    return fallback;
  }
}

function normalizeConfig(raw) {
  const merged = {
    ...DEFAULT_CONFIG,
    ...(raw || {}),
    onboarding: {
      ...DEFAULT_CONFIG.onboarding,
      ...((raw && raw.onboarding) || {}),
    },
  };

  return {
    ...merged,
    opsConsoleUrl: sanitizeUrl(merged.opsConsoleUrl, DEFAULT_CONFIG.opsConsoleUrl),
    productSignupUrl: sanitizeUrl(merged.productSignupUrl, DEFAULT_CONFIG.productSignupUrl),
    docsUrl: sanitizeUrl(merged.docsUrl, DEFAULT_CONFIG.docsUrl),
  };
}

function readConfig() {
  const configPath = getConfigPath();
  if (!fs.existsSync(configPath)) {
    return normalizeConfig(null);
  }

  try {
    const content = fs.readFileSync(configPath, 'utf8');
    return normalizeConfig(JSON.parse(content));
  } catch {
    return normalizeConfig(null);
  }
}

function writeConfig(partial) {
  const configPath = getConfigPath();
  const next = normalizeConfig({
    ...readConfig(),
    ...(partial || {}),
  });

  fs.writeFileSync(configPath, JSON.stringify(next, null, 2), 'utf8');
  return next;
}

async function testConsoleReachability(url) {
  const target = sanitizeUrl(url, DEFAULT_CONFIG.opsConsoleUrl);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);

  try {
    const response = await fetch(target, {
      method: 'GET',
      redirect: 'follow',
      signal: controller.signal,
    });

    clearTimeout(timeout);
    return {
      ok: response.ok,
      status: response.status,
      statusText: response.statusText,
      url: target,
      message: response.ok
        ? 'Console endpoint is reachable.'
        : `Console returned ${response.status} ${response.statusText}`,
    };
  } catch (error) {
    clearTimeout(timeout);
    return {
      ok: false,
      status: 0,
      statusText: 'Connection error',
      url: target,
      message: error instanceof Error ? error.message : 'Connection failed',
    };
  }
}

function attachExternalLinkPolicy(win) {
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

/* ── Application menu ───────────────────────────────────────── */

function buildAppMenu() {
  const isMac = process.platform === 'darwin';

  const template = [
    ...(isMac
      ? [
          {
            label: app.name,
            submenu: [
              { role: 'about' },
              { type: 'separator' },
              { role: 'hide' },
              { role: 'hideOthers' },
              { role: 'unhide' },
              { type: 'separator' },
              { role: 'quit' },
            ],
          },
        ]
      : []),
    {
      label: 'File',
      submenu: [
        {
          label: 'Open Control Tower',
          accelerator: 'CmdOrCtrl+Shift+O',
          click: () => {
            createConsoleWindow(readConfig().opsConsoleUrl);
          },
        },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        ...(isMac ? [{ role: 'zoom' }] : []),
        { type: 'separator' },
        {
          label: 'Show Setup Window',
          accelerator: 'CmdOrCtrl+1',
          click: () => {
            createSetupWindow();
          },
        },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Open Documentation',
          accelerator: 'F1',
          click: () => {
            shell.openExternal(readConfig().docsUrl);
          },
        },
      ],
    },
  ];

  return Menu.buildFromTemplate(template);
}

/* ── Window creation ────────────────────────────────────────── */

function createSetupWindow() {
  if (setupWindow && !setupWindow.isDestroyed()) {
    setupWindow.focus();
    return setupWindow;
  }

  const defaultBounds = { width: 1340, height: 900 };
  const restored = loadWindowState(defaultBounds);

  setupWindow = new BrowserWindow({
    ...restored,
    minWidth: 1080,
    minHeight: 760,
    autoHideMenuBar: false,
    title: 'FreightPilot Desktop Setup',
    backgroundColor: '#040c12',
    ...(process.platform === 'darwin' ? { titleBarStyle: 'hiddenInset', trafficLightPosition: { x: 16, y: 16 } } : {}),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      preload: path.join(__dirname, 'preload.cjs'),
    },
  });

  attachExternalLinkPolicy(setupWindow);
  setupWindow.loadFile(path.join(__dirname, 'onboarding.html'));

  setupWindow.on('close', () => {
    saveWindowState(setupWindow);
  });

  setupWindow.on('closed', () => {
    setupWindow = null;
  });

  return setupWindow;
}

function createConsoleWindow(url) {
  const target = sanitizeUrl(url, readConfig().opsConsoleUrl);

  if (consoleWindow && !consoleWindow.isDestroyed()) {
    consoleWindow.loadURL(target);
    consoleWindow.focus();
    return consoleWindow;
  }

  consoleWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1100,
    minHeight: 720,
    autoHideMenuBar: false,
    title: 'FreightPilot Control Tower',
    backgroundColor: '#050b12',
    ...(process.platform === 'darwin' ? { titleBarStyle: 'hiddenInset', trafficLightPosition: { x: 16, y: 16 } } : {}),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  });

  attachExternalLinkPolicy(consoleWindow);
  consoleWindow.loadURL(target);
  consoleWindow.on('closed', () => {
    consoleWindow = null;
  });

  return consoleWindow;
}

/* ── IPC handlers ───────────────────────────────────────────── */

ipcMain.handle('desktop:get-config', async () => readConfig());
ipcMain.handle('desktop:save-config', async (_, partial) => writeConfig(partial));
ipcMain.handle('desktop:test-console', async (_, url) => testConsoleReachability(url));
ipcMain.handle('desktop:open-external', async (_, url) => {
  const safe = sanitizeUrl(url, '');
  if (!safe) {
    return false;
  }
  await shell.openExternal(safe);
  return true;
});
ipcMain.handle('desktop:launch-console', async (_, url) => {
  createConsoleWindow(url || readConfig().opsConsoleUrl);
  return true;
});

/* ── App lifecycle ──────────────────────────────────────────── */

app.whenReady().then(() => {
  Menu.setApplicationMenu(buildAppMenu());
  createSetupWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createSetupWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
