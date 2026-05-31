import { useState, useEffect, useRef, useCallback } from 'react'

const API = 'http://127.0.0.1:8000'

const LANGUAGES = [
  'Python','JavaScript','TypeScript','React/JSX','React/TSX',
  'Java','Go','Rust','Ruby','PHP','C#','C++','C','Shell','SQL','Terraform','Other'
]

const SEV = {
  critical:   { color: '#ff4d4d', bg: 'rgba(255,77,77,0.08)',   border: 'rgba(255,77,77,0.2)',   dot: '●' },
  warning:    { color: '#ffb347', bg: 'rgba(255,179,71,0.08)',  border: 'rgba(255,179,71,0.2)',  dot: '●' },
  suggestion: { color: '#4dff91', bg: 'rgba(77,255,145,0.08)',  border: 'rgba(77,255,145,0.2)',  dot: '●' },
}
const VERDICT = {
  approve:       { color: '#4dff91', label: 'Approved',      icon: '✓' },
  needs_changes: { color: '#ff4d4d', label: 'Needs Changes', icon: '✗' },
  comment:       { color: '#ffb347', label: 'Comments',      icon: '◎' },
}
const CAT_ICON = { bug:'🐛', security:'🔒', performance:'⚡', style:'✨', readability:'📖' }

// ── Shared UI helpers ─────────────────────────────────────────────────────────

function Btn({ onClick, disabled, accent, danger, children, style = {} }) {
  const base = {
    padding: '10px 20px', border: 'none', borderRadius: 'var(--radius)',
    fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: 14,
    cursor: disabled ? 'not-allowed' : 'pointer', transition: 'all 0.15s',
    ...style,
  }
  if (accent)  return <button onClick={onClick} disabled={disabled} style={{ ...base, background: disabled ? 'var(--bg3)' : 'var(--accent)', color: disabled ? 'var(--text3)' : 'var(--bg)' }}>{children}</button>
  if (danger)  return <button onClick={onClick} disabled={disabled} style={{ ...base, background: 'var(--red-dim)', color: 'var(--red)', border: '0.5px solid rgba(255,77,77,0.3)' }}>{children}</button>
  return <button onClick={onClick} disabled={disabled} style={{ ...base, background: 'var(--bg3)', color: 'var(--text2)', border: '0.5px solid var(--border2)' }}>{children}</button>
}

function Label({ children }) {
  return <p style={{ fontSize: 11, color: 'var(--text3)', fontFamily: 'var(--font-mono)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>{children}</p>
}

// ── Setup screen (first run / no key) ────────────────────────────────────────

function SetupScreen({ onSaved }) {
  const [key, setKey] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!key.startsWith('sk-ant-')) { setError('Key should start with sk-ant-'); return }
    setSaving(true)
    await window.electron.saveApiKey(key)
    const result = await window.electron.startBackend(key)
    const ready = await window.electron.checkBackend()
    setSaving(false)
    if (ready.ready) onSaved()
    else setError('Backend failed to start. Check your key and try again.')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: 40 }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        <div style={{ width: 44, height: 44, background: 'var(--accent)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, color: 'var(--bg)', fontWeight: 700, marginBottom: 24 }}>✦</div>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, letterSpacing: '-0.02em' }}>AI Code Reviewer</h1>
        <p style={{ color: 'var(--text2)', fontSize: 14, marginBottom: 32, lineHeight: 1.6 }}>
          Enter your Anthropic API key to get started. It's stored securely on your machine and never leaves it.
        </p>

        <Label>Anthropic API Key</Label>
        <input
          type="password"
          value={key}
          onChange={e => { setKey(e.target.value); setError('') }}
          placeholder="sk-ant-..."
          onKeyDown={e => e.key === 'Enter' && handleSave()}
          style={{
            width: '100%', padding: '10px 14px', marginBottom: 8,
            background: 'var(--bg2)', border: `0.5px solid ${error ? 'var(--red)' : 'var(--border2)'}`,
            borderRadius: 'var(--radius)', color: 'var(--text)',
            fontFamily: 'var(--font-mono)', fontSize: 13, outline: 'none',
          }}
        />
        {error && <p style={{ color: 'var(--red)', fontSize: 12, fontFamily: 'var(--font-mono)', marginBottom: 12 }}>✗ {error}</p>}

        <p style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 20 }}>
          Get your key at{' '}
          <span style={{ color: 'var(--accent)', cursor: 'pointer' }} onClick={() => window.open?.('https://console.anthropic.com')}>
            console.anthropic.com
          </span>
        </p>

        <Btn accent onClick={handleSave} disabled={saving || !key} style={{ width: '100%', padding: '12px' }}>
          {saving ? '⟳ Starting...' : '✦ Save & Launch'}
        </Btn>
      </div>
    </div>
  )
}

// ── Loading screen ────────────────────────────────────────────────────────────

function LoadingScreen() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 16 }}>
      <div style={{ fontSize: 32, animation: 'spin 1s linear infinite' }}>◈</div>
      <p style={{ color: 'var(--text2)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>Starting backend...</p>
      <style>{`@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}

// ── Settings screen ───────────────────────────────────────────────────────────

function SettingsScreen({ onBack }) {
  const [key, setKey] = useState('')
  const [current, setCurrent] = useState('')
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    window.electron.getApiKey().then(k => {
      if (k) setCurrent(k.slice(0, 12) + '••••••••••••••••••••')
    })
  }, [])

  const handleUpdate = async () => {
    if (!key.startsWith('sk-ant-')) { setError('Key should start with sk-ant-'); return }
    await window.electron.saveApiKey(key)
    await window.electron.startBackend(key)
    await window.electron.checkBackend()
    setSaved(true)
    setKey('')
    setError('')
    setCurrent(key.slice(0, 12) + '••••••••••••••••••••')
  }

  const handleDelete = async () => {
    await window.electron.deleteApiKey()
    setCurrent('')
    setSaved(false)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '16px 24px', borderBottom: '0.5px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 }}>
        <button onClick={onBack} style={{ background: 'none', border: 'none', color: 'var(--text2)', cursor: 'pointer', fontSize: 18, padding: '0 4px' }}>←</button>
        <h2 style={{ fontSize: 16, fontWeight: 600 }}>Settings</h2>
      </div>

      <div style={{ padding: '32px 24px', maxWidth: 480 }}>
        <Label>Current API Key</Label>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text2)', marginBottom: 20, padding: '10px 14px', background: 'var(--bg2)', borderRadius: 'var(--radius)', border: '0.5px solid var(--border)' }}>
          {current || '— not set —'}
        </p>

        <Label>Update API Key</Label>
        <input
          type="password"
          value={key}
          onChange={e => { setKey(e.target.value); setError(''); setSaved(false) }}
          placeholder="sk-ant-..."
          style={{
            width: '100%', padding: '10px 14px', marginBottom: 8,
            background: 'var(--bg2)', border: `0.5px solid ${error ? 'var(--red)' : 'var(--border2)'}`,
            borderRadius: 'var(--radius)', color: 'var(--text)',
            fontFamily: 'var(--font-mono)', fontSize: 13, outline: 'none',
          }}
        />
        {error && <p style={{ color: 'var(--red)', fontSize: 12, fontFamily: 'var(--font-mono)', marginBottom: 8 }}>✗ {error}</p>}
        {saved && <p style={{ color: 'var(--green)', fontSize: 12, fontFamily: 'var(--font-mono)', marginBottom: 8 }}>✓ Key updated</p>}

        <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
          <Btn accent onClick={handleUpdate} disabled={!key}>Update Key</Btn>
          <Btn danger onClick={handleDelete}>Remove Key</Btn>
        </div>
      </div>
    </div>
  )
}

// ── File card ─────────────────────────────────────────────────────────────────

function FileCard({ file, onRemove }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', background: 'var(--bg3)', border: '0.5px solid var(--border)', borderRadius: 'var(--radius)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
      <span style={{ color: 'var(--accent)' }}>◈</span>
      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file.name}</span>
      <span style={{ color: 'var(--text3)', fontSize: 11 }}>{(file.size / 1024).toFixed(1)}kb</span>
      <button onClick={() => onRemove(file.name)} style={{ background: 'none', border: 'none', color: 'var(--text3)', cursor: 'pointer', fontSize: 18, lineHeight: 1 }}
        onMouseEnter={e => e.target.style.color = 'var(--red)'}
        onMouseLeave={e => e.target.style.color = 'var(--text3)'}>×</button>
    </div>
  )
}

// ── Review result card ────────────────────────────────────────────────────────

function ResultCard({ result }) {
  const [open, setOpen] = useState(true)
  const v = VERDICT[result.verdict] || VERDICT.comment
  return (
    <div style={{ border: '0.5px solid var(--border2)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', marginBottom: 12 }}>
      <div onClick={() => setOpen(o => !o)} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', background: 'var(--bg2)', cursor: 'pointer', borderBottom: open ? '0.5px solid var(--border)' : 'none' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{result.filename}</span>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {result.critical_count > 0 && <span style={{ fontSize: 11, color: '#ff4d4d', fontFamily: 'var(--font-mono)' }}>● {result.critical_count}</span>}
          {result.warning_count > 0 && <span style={{ fontSize: 11, color: '#ffb347', fontFamily: 'var(--font-mono)' }}>● {result.warning_count}</span>}
          {result.suggestion_count > 0 && <span style={{ fontSize: 11, color: '#4dff91', fontFamily: 'var(--font-mono)' }}>● {result.suggestion_count}</span>}
          <span style={{ fontSize: 11, color: v.color, padding: '2px 10px', border: `0.5px solid ${v.color}30`, borderRadius: 20, background: `${v.color}10`, fontFamily: 'var(--font-mono)' }}>{v.icon} {v.label}</span>
          <span style={{ color: 'var(--text3)', fontSize: 11 }}>{open ? '▲' : '▼'}</span>
        </div>
      </div>
      {open && (
        <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <p style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6 }}>{result.summary}</p>
          {result.comments.length === 0 && (
            <p style={{ textAlign: 'center', padding: 20, color: 'var(--text3)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>✓ no issues found</p>
          )}
          {result.comments.map((c, i) => {
            const s = SEV[c.severity] || SEV.suggestion
            return (
              <div key={i} style={{ border: `0.5px solid ${s.border}`, background: s.bg, borderRadius: 'var(--radius)', padding: '10px 12px' }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                  <span style={{ fontSize: 11, color: s.color, fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{s.dot} {c.severity}</span>
                  <span style={{ fontSize: 10, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>line {c.line_number}</span>
                  <span style={{ fontSize: 11, marginLeft: 'auto' }}>{CAT_ICON[c.category]} {c.category}</span>
                </div>
                <p style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--text)' }}>{c.comment}</p>
                {c.suggestion && (
                  <div style={{ marginTop: 8, padding: '6px 10px', background: 'rgba(232,255,71,0.05)', border: '0.5px solid rgba(232,255,71,0.15)', borderRadius: 6, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent)' }}>
                    → {c.suggestion}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ── Main reviewer screen ──────────────────────────────────────────────────────

function ReviewScreen({ onSettings }) {
  const [mode, setMode] = useState('upload')
  const [files, setFiles] = useState([])
  const [code, setCode] = useState('')
  const [lang, setLang] = useState('Python')
  const [fname, setFname] = useState('untitled.py')
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState(null)
  const fileRef = useRef(null)
  const dropRef = useRef(null)

  const addFiles = useCallback(newFiles => {
    const arr = Array.from(newFiles)
    setFiles(prev => {
      const have = new Set(prev.map(f => f.name))
      return [...prev, ...arr.filter(f => !have.has(f.name))]
    })
  }, [])

  const onDrop = useCallback(e => {
    e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files)
  }, [addFiles])

  const submit = async () => {
    setError(null); setResults([]); setLoading(true)
    try {
      if (mode === 'upload') {
        if (!files.length) { setError('Add at least one file.'); setLoading(false); return }
        const fd = new FormData()
        files.forEach(f => fd.append('files', f))
        const r = await fetch(`${API}/review/upload`, { method: 'POST', body: fd })
        if (!r.ok) throw new Error((await r.json()).detail)
        setResults(await r.json())
      } else {
        if (!code.trim()) { setError('Paste some code first.'); setLoading(false); return }
        const r = await fetch(`${API}/review`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code, language: lang, filename: fname }) })
        if (!r.ok) throw new Error((await r.json()).detail)
        setResults([await r.json()])
      }
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const reset = () => { setResults([]); setFiles([]); setCode(''); setError(null) }

  const totalCrit = results.reduce((a, r) => a + r.critical_count, 0)
  const totalWarn = results.reduce((a, r) => a + r.warning_count, 0)
  const totalSugg = results.reduce((a, r) => a + r.suggestion_count, 0)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

      {/* Title bar area */}
      <div style={{ height: 'var(--titlebar)', flexShrink: 0, WebkitAppRegion: 'drag', display: 'flex', alignItems: 'center', paddingLeft: 16, gap: 10, borderBottom: '0.5px solid var(--border)' }}>
        <div style={{ width: 22, height: 22, background: 'var(--accent)', borderRadius: 5, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, color: 'var(--bg)', fontWeight: 700, WebkitAppRegion: 'no-drag' }}>✦</div>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', WebkitAppRegion: 'no-drag' }}>AI Code Reviewer</span>
        <div style={{ flex: 1 }} />
        <button onClick={onSettings} style={{ background: 'none', border: 'none', color: 'var(--text3)', cursor: 'pointer', fontSize: 18, padding: '0 16px', height: '100%', WebkitAppRegion: 'no-drag' }}
          onMouseEnter={e => e.target.style.color = 'var(--text)'}
          onMouseLeave={e => e.target.style.color = 'var(--text3)'}>⚙</button>
      </div>

      {/* Body */}
      <div style={{ flex: 1, overflow: 'auto', padding: '24px 28px' }}>
        {results.length === 0 ? (
          <>
            {/* Mode tabs */}
            <div style={{ display: 'flex', gap: 2, marginBottom: 20, background: 'var(--bg2)', border: '0.5px solid var(--border)', borderRadius: 'var(--radius)', padding: 3, width: 'fit-content' }}>
              {['upload', 'paste'].map(m => (
                <button key={m} onClick={() => setMode(m)} style={{ padding: '7px 18px', border: 'none', cursor: 'pointer', borderRadius: 6, fontSize: 13, fontFamily: 'var(--font-sans)', fontWeight: 600, transition: 'all 0.15s', background: mode === m ? 'var(--accent)' : 'transparent', color: mode === m ? 'var(--bg)' : 'var(--text2)' }}>
                  {m === 'upload' ? '⬆ Upload' : '{ } Paste'}
                </button>
              ))}
            </div>

            {mode === 'upload' ? (
              <>
                <div ref={dropRef} onDrop={onDrop} onDragOver={e => { e.preventDefault(); setDragging(true) }} onDragLeave={e => { if (!dropRef.current?.contains(e.relatedTarget)) setDragging(false) }} onClick={() => fileRef.current?.click()}
                  style={{ border: `1.5px dashed ${dragging ? 'var(--accent)' : 'var(--border2)'}`, borderRadius: 'var(--radius-lg)', padding: '40px 20px', textAlign: 'center', cursor: 'pointer', background: dragging ? 'var(--accent-dim)' : 'var(--bg2)', transition: 'all 0.2s', marginBottom: 12 }}>
                  <input ref={fileRef} type="file" multiple style={{ display: 'none' }} onChange={e => addFiles(e.target.files)} accept=".py,.js,.ts,.jsx,.tsx,.java,.go,.rs,.rb,.php,.cs,.cpp,.c,.sh,.sql,.tf" />
                  <div style={{ fontSize: 28, marginBottom: 10 }}>⬆</div>
                  <p style={{ fontSize: 15, fontWeight: 600, color: dragging ? 'var(--accent)' : 'var(--text)', marginBottom: 4 }}>{dragging ? 'Drop to add' : 'Drag & drop files'}</p>
                  <p style={{ fontSize: 12, color: 'var(--text3)' }}>or click to browse · up to 10 files</p>
                </div>
                {files.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 5, marginBottom: 16 }}>
                    <p style={{ fontSize: 11, color: 'var(--text3)', fontFamily: 'var(--font-mono)', marginBottom: 2 }}>{files.length} file{files.length > 1 ? 's' : ''} queued</p>
                    {files.map(f => <FileCard key={f.name} file={f} onRemove={n => setFiles(p => p.filter(x => x.name !== n))} />)}
                  </div>
                )}
              </>
            ) : (
              <>
                <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                  <div style={{ flex: 1 }}>
                    <Label>filename</Label>
                    <input value={fname} onChange={e => setFname(e.target.value)} style={{ width: '100%', padding: '8px 12px', background: 'var(--bg2)', border: '0.5px solid var(--border2)', borderRadius: 'var(--radius)', color: 'var(--text)', fontFamily: 'var(--font-mono)', fontSize: 12, outline: 'none' }} />
                  </div>
                  <div style={{ width: 160 }}>
                    <Label>language</Label>
                    <select value={lang} onChange={e => setLang(e.target.value)} style={{ width: '100%', padding: '8px 10px', background: 'var(--bg2)', border: '0.5px solid var(--border2)', borderRadius: 'var(--radius)', color: 'var(--text)', fontFamily: 'var(--font-sans)', fontSize: 13, outline: 'none', cursor: 'pointer' }}>
                      {LANGUAGES.map(l => <option key={l}>{l}</option>)}
                    </select>
                  </div>
                </div>
                <textarea value={code} onChange={e => setCode(e.target.value)} placeholder="// paste your code here..." style={{ width: '100%', height: 260, padding: 14, background: 'var(--bg2)', border: '0.5px solid var(--border2)', borderRadius: 'var(--radius-lg)', color: 'var(--text)', fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.7, resize: 'none', outline: 'none', marginBottom: 12 }} onFocus={e => e.target.style.borderColor = 'var(--accent)'} onBlur={e => e.target.style.borderColor = 'var(--border2)'} />
              </>
            )}

            {error && <div style={{ padding: '8px 12px', background: 'var(--red-dim)', border: '0.5px solid rgba(255,77,77,0.3)', borderRadius: 'var(--radius)', color: 'var(--red)', fontSize: 13, marginBottom: 12, fontFamily: 'var(--font-mono)' }}>✗ {error}</div>}

            <Btn accent onClick={submit} disabled={loading} style={{ width: '100%', padding: '12px' }}>
              {loading ? '⟳ Reviewing...' : '✦ Run AI Review'}
            </Btn>
          </>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, flex: 1 }}>Results</h2>
              <Btn onClick={reset}>← New Review</Btn>
            </div>
            <div style={{ display: 'flex', gap: 10, marginBottom: 20, padding: '12px 16px', background: 'var(--bg2)', border: '0.5px solid var(--border)', borderRadius: 'var(--radius-lg)' }}>
              {[
                { label: 'files', value: results.length, color: 'var(--blue)' },
                { label: 'critical', value: totalCrit, color: 'var(--red)' },
                { label: 'warnings', value: totalWarn, color: 'var(--amber)' },
                { label: 'suggestions', value: totalSugg, color: 'var(--green)' },
              ].map(s => (
                <div key={s.label} style={{ flex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 700, color: s.color, fontFamily: 'var(--font-mono)' }}>{s.value}</div>
                  <div style={{ fontSize: 10, color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>{s.label}</div>
                </div>
              ))}
            </div>
            {results.map((r, i) => <ResultCard key={i} result={r} />)}
          </>
        )}
      </div>
    </div>
  )
}

// ── Root ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [screen, setScreen] = useState('loading') // loading | setup | review | settings

  useEffect(() => {
    const init = async () => {
      const key = await window.electron.getApiKey()
      if (!key) { setScreen('setup'); return }
      await window.electron.startBackend(key)
      const ready = await window.electron.checkBackend()
      setScreen(ready.ready ? 'review' : 'setup')
    }
    init()
  }, [])

  if (screen === 'loading')  return <LoadingScreen />
  if (screen === 'setup')    return <SetupScreen onSaved={() => setScreen('review')} />
  if (screen === 'settings') return <SettingsScreen onBack={() => setScreen('review')} />
  return <ReviewScreen onSettings={() => setScreen('settings')} />
}
