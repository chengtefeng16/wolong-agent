import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function Login({ onLogin }) {
  const [mode, setMode] = useState('login')   // 'login' | 'register'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [tenantName, setTenantName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const url = mode === 'login'
        ? `${API_BASE}/api/v1/auth/login`
        : `${API_BASE}/api/v1/auth/register`
      const body = mode === 'login'
        ? { email, password }
        : { email, password, name, tenant_name: tenantName }
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '操作失败')
      }
      const data = await res.json()
      onLogin(data.access_token)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={S.page}>
      <div style={S.card}>
        <div style={S.logo}>🐉</div>
        <h1 style={S.title}>卧龙 AI 销售助理</h1>

        <div style={S.tabs}>
          <button style={{...S.tab, ...(mode==='login'?S.tabActive:{})}} onClick={()=>setMode('login')}>登录</button>
          <button style={{...S.tab, ...(mode==='register'?S.tabActive:{})}} onClick={()=>setMode('register')}>注册</button>
        </div>

        <form onSubmit={handleSubmit} style={S.form}>
          {mode === 'register' && <>
            <input style={S.input} placeholder="公司名称" value={tenantName} onChange={e=>setTenantName(e.target.value)} required />
            <input style={S.input} placeholder="你的名字" value={name} onChange={e=>setName(e.target.value)} required />
          </>}
          <input style={S.input} type="email" placeholder="邮箱" value={email} onChange={e=>setEmail(e.target.value)} required />
          <input style={S.input} type="password" placeholder="密码" value={password} onChange={e=>setPassword(e.target.value)} required />
          {error && <div style={S.error}>{error}</div>}
          <button style={S.btn} type="submit" disabled={loading}>
            {loading ? '请稍候…' : mode === 'login' ? '登录' : '注册并开始'}
          </button>
        </form>
      </div>
    </div>
  )
}

const S = {
  page: { minHeight:'100vh', display:'flex', alignItems:'center', justifyContent:'center',
    background:'linear-gradient(135deg,#f0fdf4,#dcfce7)', padding:20,
    fontFamily:'-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif' },
  card: { background:'#fff', borderRadius:16, padding:'48px 40px', maxWidth:400, width:'100%',
    boxShadow:'0 20px 60px rgba(0,0,0,0.10)', textAlign:'center' },
  logo: { fontSize:48, marginBottom:12 },
  title: { fontSize:22, fontWeight:700, color:'#111', margin:'0 0 24px' },
  tabs: { display:'flex', marginBottom:24, borderRadius:8, overflow:'hidden', border:'1px solid #e5e7eb' },
  tab: { flex:1, padding:'10px 0', background:'transparent', border:'none',
    cursor:'pointer', fontSize:14, color:'#6b7280' },
  tabActive: { background:'#25D366', color:'#fff', fontWeight:600 },
  form: { display:'flex', flexDirection:'column', gap:12 },
  input: { padding:'12px 16px', borderRadius:8, border:'1px solid #d1d5db',
    fontSize:15, outline:'none' },
  error: { color:'#dc2626', fontSize:13, textAlign:'left' },
  btn: { padding:'14px', background:'#25D366', color:'#fff', border:'none',
    borderRadius:8, fontSize:16, fontWeight:600, cursor:'pointer' },
}
