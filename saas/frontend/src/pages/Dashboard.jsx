/**
 * Dashboard: 多租户对话工作台
 * 左: 会话列表（带状态/语言标签）
 * 右: 聊天详情 + AI 草稿审核 + 一键发送
 */
import { useState, useEffect, useRef, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// ── Language badge colors ─────────────────────────────────────────────────────
const LANG_COLOR = {
  zh: '#ef4444', en: '#3b82f6', ar: '#f59e0b',
  ru: '#8b5cf6', es: '#10b981', fr: '#06b6d4',
}

// ── Status badge ──────────────────────────────────────────────────────────────
const STATUS_LABEL = { open: '待回复', pending: '草稿待审', closed: '已关闭' }
const STATUS_COLOR = { open: '#f59e0b', pending: '#3b82f6', closed: '#9ca3af' }

// ── Helpers ───────────────────────────────────────────────────────────────────
function authHeaders(token) {
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
}

async function apiFetch(path, token, opts = {}) {
  const res = await fetch(`${API_BASE}/api/v1${path}`, { headers: authHeaders(token), ...opts })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function Dashboard({ token, onLogout }) {
  const [convos, setConvos] = useState([])
  const [selected, setSelected] = useState(null)   // full conversation object
  const [detail, setDetail] = useState(null)        // {messages, pending_draft}
  const [draftText, setDraftText] = useState('')
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [loading, setLoading] = useState(true)
  const bottomRef = useRef(null)

  // Poll conversation list every 8 seconds
  const loadConvos = useCallback(async () => {
    try {
      const status = filterStatus === 'all' ? '' : `?status=${filterStatus}`
      const data = await apiFetch(`/conversations${status}`, token)
      setConvos(data)
    } catch { /* silent */ }
    setLoading(false)
  }, [token, filterStatus])

  useEffect(() => {
    loadConvos()
    const t = setInterval(loadConvos, 8000)
    return () => clearInterval(t)
  }, [loadConvos])

  // Load detail when conversation selected
  useEffect(() => {
    if (!selected) return
    loadDetail(selected.id)
    const t = setInterval(() => loadDetail(selected.id), 5000)
    return () => clearInterval(t)
  }, [selected?.id])

  async function loadDetail(id) {
    try {
      const data = await apiFetch(`/conversations/${id}`, token)
      setDetail(data)
      if (data.pending_draft && !draftText) {
        setDraftText(data.pending_draft.text)
      }
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    } catch { /* silent */ }
  }

  async function handleSend() {
    if (!detail?.pending_draft || !draftText.trim()) return
    setSending(true)
    setSendError('')
    try {
      await apiFetch('/whatsapp/send', token, {
        method: 'POST',
        body: JSON.stringify({ draft_id: detail.pending_draft.id, final_text: draftText }),
      })
      setDraftText('')
      await loadDetail(selected.id)
      await loadConvos()
    } catch (e) {
      setSendError(e.message)
    } finally {
      setSending(false)
    }
  }

  const filtered = filterStatus === 'all' ? convos : convos.filter(c => c.status === filterStatus)

  return (
    <div style={S.shell}>
      {/* ── Sidebar ── */}
      <aside style={S.sidebar}>
        <div style={S.sidebarHeader}>
          <span style={S.brand}>🐉 卧龙</span>
          <button style={S.logoutBtn} onClick={onLogout} title="退出">↩</button>
        </div>

        {/* Filter tabs */}
        <div style={S.filterRow}>
          {['all','pending','open','closed'].map(s => (
            <button key={s}
              style={{...S.filterTab, ...(filterStatus===s ? S.filterTabActive : {})}}
              onClick={() => setFilterStatus(s)}>
              {s === 'all' ? '全部' : STATUS_LABEL[s]}
            </button>
          ))}
        </div>

        {/* Connect button */}
        <a href="/onboard" style={S.connectLink}>+ 连接新号码</a>

        {/* Conversation list */}
        <div style={S.convoList}>
          {loading && <div style={S.empty}>加载中…</div>}
          {!loading && filtered.length === 0 && (
            <div style={S.empty}>暂无会话<br/><span style={{fontSize:12,color:'#9ca3af'}}>客户发 WhatsApp 消息后自动出现</span></div>
          )}
          {filtered.map(c => (
            <div key={c.id}
              style={{...S.convoItem, ...(selected?.id===c.id ? S.convoItemActive : {})}}
              onClick={() => { setSelected(c); setDraftText('') }}>
              <div style={S.convoTop}>
                <span style={S.convoName}>{c.customer_name || c.customer_phone || c.customer_bsuid}</span>
                <span style={{...S.statusDot, background: STATUS_COLOR[c.status]}} title={STATUS_LABEL[c.status]} />
              </div>
              <div style={S.convoMeta}>
                {c.country && <span style={S.tag}>{c.country}</span>}
                {c.bucket && <span style={{...S.tag, background: LANG_COLOR[c.bucket] || '#6b7280', color:'#fff'}}>{c.bucket}</span>}
                {c.has_pending_draft && <span style={{...S.tag, background:'#3b82f6', color:'#fff'}}>草稿</span>}
              </div>
            </div>
          ))}
        </div>
      </aside>

      {/* ── Main pane ── */}
      <main style={S.main}>
        {!selected ? (
          <div style={S.placeholder}>
            <div style={{fontSize:64}}>💬</div>
            <p style={{color:'#9ca3af', marginTop:16}}>选择左侧会话查看详情</p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div style={S.chatHeader}>
              <div>
                <div style={S.chatName}>{selected.customer_name || selected.customer_phone || selected.customer_bsuid}</div>
                <div style={S.chatSub}>
                  {selected.customer_phone && <span>{selected.customer_phone}</span>}
                  {selected.country && <span style={{marginLeft:8}}>🌍 {selected.country}</span>}
                </div>
              </div>
              <span style={{...S.statusBadge, background: STATUS_COLOR[selected.status]}}>
                {STATUS_LABEL[selected.status]}
              </span>
            </div>

            {/* Messages */}
            <div style={S.msgArea}>
              {detail?.messages?.map(m => (
                <div key={m.id} style={{...S.msgRow, justifyContent: m.role==='agent' ? 'flex-end' : 'flex-start'}}>
                  <div style={{...S.bubble, ...(m.role==='agent' ? S.bubbleAgent : S.bubbleCustomer)}}>
                    {m.text}
                    <div style={S.msgTime}>
                      {m.role==='agent' ? '✓ 已发送' : '客户'}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            {/* AI Draft panel */}
            {detail?.pending_draft ? (
              <div style={S.draftPanel}>
                <div style={S.draftHeader}>
                  <span>🤖 AI 草稿</span>
                  <span style={S.draftLang}>
                    {detail.pending_draft.language_code?.toUpperCase() || 'AUTO'}
                  </span>
                </div>
                <textarea
                  style={S.draftTextarea}
                  value={draftText}
                  onChange={e => setDraftText(e.target.value)}
                  rows={4}
                  placeholder="修改草稿后点击发送…"
                />
                {sendError && <div style={S.sendError}>{sendError}</div>}
                <div style={S.draftActions}>
                  <button style={S.discardBtn} onClick={() => setDraftText('')} disabled={sending}>
                    清空
                  </button>
                  <button style={S.sendBtn} onClick={handleSend} disabled={sending || !draftText.trim()}>
                    {sending ? '发送中…' : '一键发送 →'}
                  </button>
                </div>
              </div>
            ) : (
              <div style={S.noDraft}>
                {selected.status === 'closed'
                  ? '会话已关闭（客户超过 24 小时未回复，只能发模板消息）'
                  : '等待客户消息，AI 将自动生成草稿…'}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────
const S = {
  shell: { display:'flex', height:'100vh', fontFamily:'-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',
    background:'#f9fafb', overflow:'hidden' },

  sidebar: { width:280, flexShrink:0, background:'#fff', borderRight:'1px solid #e5e7eb',
    display:'flex', flexDirection:'column', overflow:'hidden' },
  sidebarHeader: { padding:'16px 16px 12px', display:'flex', justifyContent:'space-between',
    alignItems:'center', borderBottom:'1px solid #f3f4f6' },
  brand: { fontWeight:700, fontSize:18, color:'#111' },
  logoutBtn: { background:'none', border:'none', cursor:'pointer', fontSize:18, color:'#9ca3af' },

  filterRow: { display:'flex', padding:'8px 8px 0', gap:4, flexWrap:'wrap' },
  filterTab: { flex:1, padding:'5px 0', background:'#f3f4f6', border:'none',
    borderRadius:6, fontSize:11, cursor:'pointer', color:'#6b7280', minWidth:40 },
  filterTabActive: { background:'#25D366', color:'#fff', fontWeight:600 },

  connectLink: { display:'block', margin:'8px 12px', padding:'8px',
    background:'#f0fdf4', color:'#15803d', borderRadius:8, textAlign:'center',
    fontSize:13, fontWeight:600, textDecoration:'none', border:'1px dashed #86efac' },

  convoList: { flex:1, overflowY:'auto', padding:'4px 0' },
  empty: { padding:'32px 16px', textAlign:'center', color:'#6b7280', lineHeight:1.8 },
  convoItem: { padding:'12px 16px', cursor:'pointer', borderBottom:'1px solid #f9fafb',
    transition:'background .15s' },
  convoItemActive: { background:'#f0fdf4', borderLeft:'3px solid #25D366' },
  convoTop: { display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:4 },
  convoName: { fontWeight:600, fontSize:14, color:'#111', overflow:'hidden',
    textOverflow:'ellipsis', whiteSpace:'nowrap', maxWidth:180 },
  statusDot: { width:8, height:8, borderRadius:'50%', flexShrink:0 },
  convoMeta: { display:'flex', gap:4, flexWrap:'wrap' },
  tag: { padding:'1px 6px', borderRadius:10, fontSize:11, background:'#f3f4f6', color:'#374151' },

  main: { flex:1, display:'flex', flexDirection:'column', overflow:'hidden' },
  placeholder: { flex:1, display:'flex', flexDirection:'column', alignItems:'center',
    justifyContent:'center' },

  chatHeader: { padding:'16px 24px', background:'#fff', borderBottom:'1px solid #e5e7eb',
    display:'flex', justifyContent:'space-between', alignItems:'center', flexShrink:0 },
  chatName: { fontWeight:700, fontSize:16, color:'#111' },
  chatSub: { fontSize:13, color:'#6b7280', marginTop:2 },
  statusBadge: { padding:'4px 10px', borderRadius:12, fontSize:12, fontWeight:600, color:'#fff' },

  msgArea: { flex:1, overflowY:'auto', padding:'16px 24px', display:'flex',
    flexDirection:'column', gap:10 },
  msgRow: { display:'flex' },
  bubble: { maxWidth:'72%', padding:'10px 14px', borderRadius:12, fontSize:14,
    lineHeight:1.6, wordBreak:'break-word' },
  bubbleCustomer: { background:'#fff', border:'1px solid #e5e7eb', color:'#111',
    borderRadius:'12px 12px 12px 2px' },
  bubbleAgent: { background:'#25D366', color:'#fff', borderRadius:'12px 12px 2px 12px' },
  msgTime: { fontSize:11, opacity:0.7, marginTop:4 },

  draftPanel: { padding:'12px 24px 16px', background:'#eff6ff',
    borderTop:'1px solid #bfdbfe', flexShrink:0 },
  draftHeader: { display:'flex', justifyContent:'space-between', alignItems:'center',
    marginBottom:8, fontWeight:600, fontSize:14, color:'#1d4ed8' },
  draftLang: { padding:'2px 8px', background:'#dbeafe', borderRadius:8,
    fontSize:12, fontWeight:700, color:'#1e40af' },
  draftTextarea: { width:'100%', borderRadius:8, border:'1px solid #bfdbfe',
    padding:'10px 12px', fontSize:14, resize:'vertical', outline:'none',
    fontFamily:'inherit', boxSizing:'border-box' },
  sendError: { color:'#dc2626', fontSize:12, marginTop:4 },
  draftActions: { display:'flex', justifyContent:'flex-end', gap:8, marginTop:8 },
  discardBtn: { padding:'8px 16px', background:'#fff', border:'1px solid #d1d5db',
    borderRadius:8, cursor:'pointer', fontSize:14, color:'#374151' },
  sendBtn: { padding:'8px 20px', background:'#25D366', color:'#fff', border:'none',
    borderRadius:8, cursor:'pointer', fontSize:14, fontWeight:600 },

  noDraft: { padding:'12px 24px', background:'#f9fafb', borderTop:'1px solid #e5e7eb',
    fontSize:13, color:'#9ca3af', flexShrink:0, textAlign:'center' },
}
