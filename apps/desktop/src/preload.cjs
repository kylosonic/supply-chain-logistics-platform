const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('freightPilotDesktop', {
  getConfig: () => ipcRenderer.invoke('desktop:get-config'),
  saveConfig: (partial) => ipcRenderer.invoke('desktop:save-config', partial),
  testConsole: (url) => ipcRenderer.invoke('desktop:test-console', url),
  launchConsole: (url) => ipcRenderer.invoke('desktop:launch-console', url),
  openExternal: (url) => ipcRenderer.invoke('desktop:open-external', url),
});
