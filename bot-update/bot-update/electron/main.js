const { app, BrowserWindow, ipcMain, safeStorage } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const fs = require('fs')
const Store = require('electron-store')

const store = new Store()
let mainWindow = null
let backendProcess = null

// ── Backend launcher ──────────────────────────────────────────────────────────

function getBackendPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', 'backend.exe')
  }
  return path.join(__dirname, '..', 'backend', 'main.py')
}

function startBackend(apiKey) {
  const backendPath = getBackendPath()

  const env = { ...process.env, ANTHROPIC_API_KEY: apiKey }

  if (app.isPackaged) {
    backendProcess = spawn(backendPath, [], { env, windowsHide: true })
  } else {
    backendProcess = spawn('python', ['-m', 'uvicorn', 'main:app', '--port', '8000'], {
      cwd: path.join(__dirname, '..', 'backend'),
      env,
      windowsHide: true,
    })
  }

  backendProcess.stdout.on('data', d => console.log('[backend]', d.toString()))
  backendProcess.stderr.on('data', d => console.error('[backend]', d.toString()))
  backendProcess.on('exit', code => console.log('[backend] exited with code', code))
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
}

// ── Window ────────────────────────────────────────────────────────────────────

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 780,
    minWidth: 800,
    minHeight: 600,
    backgroundColor: '#0d0d0d',
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#141414',
      symbolColor: '#999999',
      height: 36,
    },
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
  })

  if (app.isPackaged) {
    mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'dist', 'index.html'))
  } else {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  }
}

// ── IPC handlers ──────────────────────────────────────────────────────────────

ipcMain.handle('get-api-key', () => {
  const encrypted = store.get('apiKey')
  if (!encrypted) return null
  try {
    return safeStorage.decryptString(Buffer.from(encrypted, 'base64'))
  } catch {
    return null
  }
})

ipcMain.handle('save-api-key', (_, key) => {
  try {
    const encrypted = safeStorage.encryptString(key)
    store.set('apiKey', encrypted.toString('base64'))
    return { ok: true }
  } catch (e) {
    return { ok: false, error: e.message }
  }
})

ipcMain.handle('delete-api-key', () => {
  store.delete('apiKey')
  return { ok: true }
})

ipcMain.handle('start-backend', (_, apiKey) => {
  stopBackend()
  startBackend(apiKey)
  return { ok: true }
})

ipcMain.handle('check-backend', async () => {
  // Poll until backend is ready (max 10s)
  for (let i = 0; i < 20; i++) {
    try {
      const res = await fetch('http://127.0.0.1:8000/health')
      if (res.ok) return { ready: true }
    } catch {}
    await new Promise(r => setTimeout(r, 500))
  }
  return { ready: false }
})

// ── App lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  stopBackend()
  app.quit()
})

app.on('before-quit', stopBackend)
