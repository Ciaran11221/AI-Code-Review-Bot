# Update Instructions

Extract this zip and copy files into your existing `AI Code Review Bot` folder as follows:

## New files to add:

```
AI Code Review Bot\
  ├── package.json              ← copy from this zip (ROOT level)
  ├── electron\
  │   ├── main.js               ← copy from this zip
  │   ├── preload.js            ← copy from this zip
  │   └── assets\               ← create this folder, add icon.png later
  └── frontend\
      ├── package.json          ← REPLACE with frontend-package.json from this zip
      ├── vite.config.js        ← REPLACE with vite.config.js from this zip
      └── src\
          ├── App.jsx           ← REPLACE with App.jsx from this zip
          ├── index.css         ← REPLACE with index.css from this zip
          └── main.jsx          ← REPLACE with main.jsx from this zip
```

## Then run (in order):

### 1. Frontend deps
```powershell
cd "C:\IT Projects\AI Code Review Bot\frontend"
npm install
```

### 2. Electron deps (root)
```powershell
cd "C:\IT Projects\AI Code Review Bot"
npm install
```

### 3. Dev mode
```powershell
cd "C:\IT Projects\AI Code Review Bot"
npm run dev
```
