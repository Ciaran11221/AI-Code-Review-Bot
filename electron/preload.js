const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electron', {
  getApiKey:    ()      => ipcRenderer.invoke('get-api-key'),
  saveApiKey:   (key)   => ipcRenderer.invoke('save-api-key', key),
  deleteApiKey: ()      => ipcRenderer.invoke('delete-api-key'),
  startBackend: (key)   => ipcRenderer.invoke('start-backend', key),
  checkBackend: ()      => ipcRenderer.invoke('check-backend'),
})
