const { app, BrowserWindow, ipcMain, shell } = require('electron');
const fs = require('fs');
const path = require('path');

const DEFAULT_CONFIG = {
  opsConsoleUrl: process.env.OPS_CONSOLE_URL || 'http://localhost:5173/login',
  productSignupUrl: process.env.PRODUCT_SIGNUP_URL || 'https://product-web-chi.vercel.app#signup',
  docsUrl: process.env.DOCS_URL || 'https://product-web-chi.vercel.app',
  onboarding: {
    createdAccount: false,
    connectedConsole: false,
    invitedTeam: false,
    importedData: false,
  },
};

let setupWindow = null;
let consoleWindow = null;

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

function createSetupWindow() {
  if (setupWindow && !setupWindow.isDestroyed()) {
    setupWindow.focus();
    return setupWindow;
  }

  setupWindow = new BrowserWindow({
    width: 1340,
    height: 900,
    minWidth: 1080,
    minHeight: 760,
    autoHideMenuBar: true,
    title: 'FreightPilot Desktop Setup',
    backgroundColor: '#0f172a',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      preload: path.join(__dirname, 'preload.cjs'),
    },
  });

  attachExternalLinkPolicy(setupWindow);
  setupWindow.loadFile(path.join(__dirname, 'onboarding.html'));
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
    autoHideMenuBar: true,
    title: 'FreightPilot Control Tower',
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

app.whenReady().then(() => {
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
