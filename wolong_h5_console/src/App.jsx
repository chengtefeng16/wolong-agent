/* ================================================================
 * Copyright (c) 2026 程特峰 (Tefeng Cheng)
 * All Rights Reserved.
 *
 * Project: AgentOS / Wolong Agent System
 * This source code is proprietary and confidential.
 * Unauthorized copying, modification, distribution or use
 * of this software, in whole or in part, is strictly prohibited.
 * ================================================================ */

import { useEffect, useMemo, useRef, useState } from 'react'
import './index.css'

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 768)
  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])
  return isMobile
}

const fallbackCustomers = [
  {
    id: 'fallback_1',
    name: '运行态未加载',
    category: '待判断',
    country: '未知',
    channel: 'WhatsApp',
    time: '—',
    message: '当前还没有从 runtime 真源读取到客户数据。',
    keywords: [],
    reason: '请先同步 runtime_sessions 到 runtime_views。',
    tags: [],
    phone: '-',
    timeline: [],
    messages: [{ role: '系统', text: '等待 runtime 真源数据。', time: '—' }],
    crm_status: 'unknown',
    needs_human_review: false,
    destination: '',
  },
]

const fallbackStats = [
  { label: '准车商', value: 0 },
  { label: '疑似车商', value: 0 },
  { label: '个人客户', value: 0 },
  { label: '沟通无效', value: 0 },
]

const channels = ['全部客户', 'WhatsApp', 'Facebook', '历史激活', 'Ins（后续）', '更多渠道（后续）']

function getCounts(messages) {
  const safeMessages = Array.isArray(messages) ? messages : []
  return {
    proactiveCount: safeMessages.filter((msg) => msg.role === '客户').length,
    exchangeCount: safeMessages.length,
  }
}

function getModeLabel(mode) {
  if (mode === 'off') return '关闭'
  if (mode === 'readonly') return '只读观察'
  if (mode === 'manual') return '人工接管'
  return mode || '-'
}

function getAlertLevelStyle(level) {
  if (level === 'high') return { bg: '#fff1f2', border: '#ef4444', text: '#b91c1c' }
  if (level === 'medium') return { bg: '#fff7ed', border: '#f59e0b', text: '#b45309' }
  return { bg: '#f3f4f6', border: '#d1d5db', text: '#374151' }
}

function getPriorityStyle(priority) {
  if (priority === 'high') return { bg: '#fee2e2', text: '#b91c1c' }
  if (priority === 'medium') return { bg: '#fef3c7', text: '#92400e' }
  return { bg: '#e5e7eb', text: '#374151' }
}

function mapIndexItemToCustomer(item, conversation, index) {
  const conv = conversation || {}
  const messages = Array.isArray(conv.messages)
    ? conv.messages.map((msg) => ({
        role: msg.role === 'customer' ? '客户' : msg.role === 'agent' ? '我方' : (msg.role || '系统'),
        text: msg.text || '',
        time: msg.time || msg.timestamp || '—',
      }))
    : []

  const timeline =
    messages.length > 0
      ? messages.map((msg) => `${msg.time} ${msg.role}：${msg.text}`)
      : []

  return {
    id: String(item.phone || conv.phone || `customer_${index + 1}`),
    name: conv.customer_name || item.customer_name || item.phone || `客户${index + 1}`,
    category: conv.bucket || item.bucket || '待判断',
    country: conv.country || item.country || '未知',
    channel: conv.channel || item.channel || 'WhatsApp',
    time: item.last_message_time || '—',
    message: item.latest_message || conv.summary || '暂无摘要',
    keywords: [...(Array.isArray(conv.wants) ? conv.wants : []), ...(Array.isArray(conv.conditions) ? conv.conditions : [])],
    reason: conv.summary || item.latest_message || '暂无判断说明',
    tags: Array.isArray(conv.wants) ? conv.wants : [],
    phone: conv.phone || item.phone || '-',
    timeline,
    messages,
    crm_status: conv.crm_status || item.crm_status || 'unknown',
    needs_human_review: Boolean(item.needs_human_review),
    destination: conv.destination || '',
    pending_ai_reply: conv.pending_ai_reply || item.pending_ai_reply || null,
  }
}

async function fetchJson(url, fallback = null) {
  try {
    const response = await fetch(`${url}?t=${Date.now()}`)
    if (!response.ok) return fallback
    return await response.json()
  } catch (err) {
    return fallback
  }
}

async function loadRuntimeCustomers(channel = 'WhatsApp') {
  const dashboardData = await fetchJson('/runtime/views/h5_dashboard_whatsapp.json')

  const whatsappResult = {
    customers: dashboardData?.customers && Array.isArray(dashboardData.customers)
      ? dashboardData.customers
      : fallbackCustomers,
    stats: dashboardData?.stats
      ? [
          { label: '准车商', value: dashboardData.stats['准车商'] || 0 },
          { label: '疑似车商', value: dashboardData.stats['疑似车商'] || 0 },
          { label: '个人客户', value: dashboardData.stats['个人客户'] || 0 },
          { label: '沟通无效', value: dashboardData.stats['沟通无效'] || 0 },
        ]
      : fallbackStats,
  }

  if (channel !== 'Facebook') {
    return whatsappResult
  }

  const fbChat = await fetchJson('/runtime/views/h5_dashboard_facebook.json', { customers: [], stats: {}, customer_count: 0 })
  const fbFeed = await fetchJson('/runtime/views/h5_dashboard_facebook_feed.json', { customers: [], stats: {}, customer_count: 0 })

  const fbCustomers = [
    ...(Array.isArray(fbChat?.customers) ? fbChat.customers : []),
    ...(Array.isArray(fbFeed?.customers) ? fbFeed.customers : []),
  ]

  const normalizedFbCustomers = fbCustomers.length
    ? fbCustomers.map((item, index) => ({
        id: item?.id || `facebook_${index + 1}`,
        name: item?.name || item?.customer_name || 'Facebook客户',
        category: item?.category || '待判断',
        country: item?.country || '未知',
        channel: item?.channel || 'Facebook',
        time: item?.time || '—',
        message: item?.message || '暂无摘要',
        keywords: Array.isArray(item?.keywords) ? item.keywords : [],
        reason: item?.reason || '暂无判断说明',
        tags: Array.isArray(item?.tags) ? item.tags : [],
        phone: item?.phone || '-',
        timeline: Array.isArray(item?.timeline) ? item.timeline : [],
        messages: Array.isArray(item?.messages) ? item.messages : [],
        crm_status: item?.crm_status || 'unknown',
        needs_human_review: Boolean(item?.needs_human_review),
        destination: item?.destination || '',
      }))
    : []

  const fbStatsMap = {
    准车商: 0,
    疑似车商: 0,
    个人客户: 0,
    沟通无效: 0,
  }

  normalizedFbCustomers.forEach((customer) => {
    const key = customer.category
    if (fbStatsMap[key] !== undefined) {
      fbStatsMap[key] += 1
    } else {
      fbStatsMap['沟通无效'] += 1
    }
  })

  return {
    customers: normalizedFbCustomers,
    stats: [
      { label: '准车商', value: fbStatsMap['准车商'] },
      { label: '疑似车商', value: fbStatsMap['疑似车商'] },
      { label: '个人客户', value: fbStatsMap['个人客户'] },
      { label: '沟通无效', value: fbStatsMap['沟通无效'] },
    ],
  }
}

function getCountryFlag(country) {
  if (!country) return '🌍'
  const lower = country.toLowerCase()
  const map = [
    [['阿联酋', 'uae', 'emirates', '迪拜', 'dubai'], '🇦🇪'],
    [['俄罗斯', 'russia', 'russian'], '🇷🇺'],
    [['沙特', 'saudi'], '🇸🇦'],
    [['乌兹别克斯坦', 'uzbek'], '🇺🇿'],
    [['土库曼斯坦', 'turkmen'], '🇹🇲'],
    [['哈萨克斯坦', 'kazakh'], '🇰🇿'],
    [['阿富汗', 'afghan'], '🇦🇫'],
    [['巴基斯坦', 'pakistan', 'pakistani'], '🇵🇰'],
    [['伊朗', 'iran', 'iranian'], '🇮🇷'],
    [['土耳其', 'turkey', 'turkish'], '🇹🇷'],
    [['伊拉克', 'iraq', 'iraqi'], '🇮🇶'],
    [['科威特', 'kuwait'], '🇰🇼'],
    [['卡塔尔', 'qatar'], '🇶🇦'],
    [['巴林', 'bahrain'], '🇧🇭'],
    [['约旦', 'jordan'], '🇯🇴'],
    [['叙利亚', 'syria', 'syrian'], '🇸🇾'],
    [['黎巴嫩', 'lebanon', 'lebanese'], '🇱🇧'],
    [['埃及', 'egypt', 'egyptian'], '🇪🇬'],
    [['摩洛哥', 'morocco', 'moroccan'], '🇲🇦'],
    [['尼日利亚', 'nigeria', 'nigerian'], '🇳🇬'],
    [['加纳', 'ghana', 'ghanaian'], '🇬🇭'],
    [['肯尼亚', 'kenya', 'kenyan'], '🇰🇪'],
    [['中国', 'china', 'chinese'], '🇨🇳'],
    [['美国', 'usa', 'united states', 'american'], '🇺🇸'],
    [['英国', 'uk', 'united kingdom', 'britain', 'british'], '🇬🇧'],
    [['德国', 'germany', 'german'], '🇩🇪'],
    [['法国', 'france', 'french'], '🇫🇷'],
    [['澳大利亚', 'australia', 'australian'], '🇦🇺'],
    [['印度', 'india', 'indian'], '🇮🇳'],
    [['印尼', '印度尼西亚', 'indonesia', 'indonesian'], '🇮🇩'],
    [['马来西亚', 'malaysia', 'malaysian'], '🇲🇾'],
    [['泰国', 'thailand', 'thai'], '🇹🇭'],
    [['越南', 'vietnam', 'vietnamese'], '🇻🇳'],
    [['菲律宾', 'philippines', 'filipino'], '🇵🇭'],
    [['阿塞拜疆', 'azerbaijan', 'azerbaijani'], '🇦🇿'],
    [['格鲁吉亚', 'georgia', 'georgian'], '🇬🇪'],
    [['吉尔吉斯斯坦', 'kyrgyz', 'kyrgyzstan'], '🇰🇬'],
  ]
  for (const [keys, flag] of map) {
    if (keys.some(k => lower.includes(k))) return flag
  }
  return '🌍'
}

// ── 客户标签预设 ──
const PRESET_TAGS = [
  { label: '高意向',   color: '#dc2626', bg: '#fef2f2', border: '#fca5a5' },
  { label: '待跟进',   color: '#d97706', bg: '#fffbeb', border: '#fcd34d' },
  { label: '已成交',   color: '#16a34a', bg: '#f0fdf4', border: '#86efac' },
  { label: '长期观望', color: '#2563eb', bg: '#eff6ff', border: '#93c5fd' },
  { label: '价格敏感', color: '#7c3aed', bg: '#f5f3ff', border: '#c4b5fd' },
  { label: '无效',     color: '#6b7280', bg: '#f9fafb', border: '#d1d5db' },
]

// ── 业务分类（客户所属业务线）──
const BIZ_TYPES = [
  { key: 'trade',      label: '🚗 贸易客户', desc: '坤越通二手车国际贸易', color: '#d97706', bg: '#fffbeb', border: '#fcd34d' },
  { key: 'saas',       label: '📋 SaaS客户', desc: 'cncar国家政策法规系统',  color: '#2563eb', bg: '#eff6ff', border: '#93c5fd' },
  { key: 'unclassified', label: '🔍 待分类',  desc: '尚未确定业务归属',       color: '#6b7280', bg: '#f9fafb', border: '#d1d5db' },
]

// ── 消息模板预设（后端可覆盖）──
const PRESET_TEMPLATES = [
  {
    id: 'tpl_trade_en',
    name: '贸易-英文开场',
    bizType: 'trade',
    lang: 'en',
    langLabel: '英文',
    content: 'Hi {name}, I\'m from KunYueTong Auto Export. We specialize in used vehicle exports to {country}. Would you be interested in our competitive prices and reliable service?',
  },
  {
    id: 'tpl_trade_ru',
    name: '贸易-俄文开场',
    bizType: 'trade',
    lang: 'ru',
    langLabel: '俄文',
    content: 'Здравствуйте, {name}! Я представляю компанию по экспорту подержанных автомобилей из Китая. Нас интересует сотрудничество с {country}. Готовы обсудить?',
  },
  {
    id: 'tpl_saas_zh',
    name: 'SaaS-中文开场',
    bizType: 'saas',
    lang: 'zh',
    langLabel: '中文',
    content: '您好{name}，我们是cncar国家政策法规查询系统，专为国际贸易商提供各国进口政策、关税、法规的一站式查询服务。是否方便了解一下？',
  },
]

// 渲染模板内容：把 {name}/{country} 等变量替换成实际值（未填则保留原格式）
function applyTemplateVars(content, vars = {}) {
  return content.replace(/\{(\w+)\}/g, (_, k) => vars[k] || `{${k}}`)
}

// ── 历史激活：意向等级颜色配置 ──
const INTENT_COLORS = {
  hot:     { bg: '#fef2f2', border: '#ef4444', badge: '#dc2626', label: '🔥 高意向' },
  warm:    { bg: '#fffbeb', border: '#f59e0b', badge: '#d97706', label: '🟡 中意向' },
  cold:    { bg: '#eff6ff', border: '#93c5fd', badge: '#2563eb', label: '🧊 低意向' },
  unknown: { bg: '#f9fafb', border: '#d1d5db', badge: '#6b7280', label: '❓ 未知' },
}

// ─────────────────────────────────────────────────────────────
// LoginPage
// ─────────────────────────────────────────────────────────────
function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!username.trim() || !password.trim()) { setError('请输入用户名和密码'); return }
    setLoading(true)
    setError('')
    try {
      const resp = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.trim(), password: password.trim() }),
      })
      const data = await resp.json()
      if (data.success) {
        localStorage.setItem('wolong_auth', JSON.stringify(data.user))
        onLogin(data.user)
      } else {
        setError(data.error || '登录失败')
      }
    } catch {
      setError('无法连接到服务器，请确认后端已启动')
    }
    setLoading(false)
  }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: '100vh', background: '#f8fafc',
    }}>
      <div style={{
        background: '#fff', borderRadius: '16px', padding: '40px 36px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.10)', width: '340px', maxWidth: '90vw',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🐉</div>
          <div style={{ fontSize: '22px', fontWeight: 800, color: '#1e2640' }}>卧龙 CRM</div>
          <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>请登录您的账户</div>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '14px' }}>
            <div style={{ fontSize: '12px', color: '#374151', fontWeight: 600, marginBottom: '5px' }}>用户名</div>
            <input
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="输入用户名"
              autoFocus
              style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '14px', boxSizing: 'border-box', outline: 'none' }}
            />
          </div>
          <div style={{ marginBottom: '20px' }}>
            <div style={{ fontSize: '12px', color: '#374151', fontWeight: 600, marginBottom: '5px' }}>密码</div>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="输入密码"
              style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '14px', boxSizing: 'border-box', outline: 'none' }}
            />
          </div>

          {error && (
            <div style={{ marginBottom: '14px', padding: '8px 12px', background: '#fef2f2', borderRadius: '8px', fontSize: '12px', color: '#dc2626' }}>
              ⚠ {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '11px', borderRadius: '8px', border: 'none',
              background: loading ? '#93c5fd' : '#2563eb', color: '#fff',
              fontWeight: 700, fontSize: '14px', cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? '登录中...' : '登录'}
          </button>
        </form>

        <div style={{ marginTop: '20px', padding: '12px', background: '#f9fafb', borderRadius: '8px', fontSize: '11px', color: '#6b7280' }}>
          <div style={{ fontWeight: 600, marginBottom: '4px' }}>测试账号：</div>
          <div>admin / admin888（管理员，查看全部）</div>
          <div>xiao_li / li2026（销售员）</div>
          <div>xiao_wang / wang2026（销售员）</div>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('wolong_auth')
      return saved ? JSON.parse(saved) : null
    } catch { return null }
  })
  if (!currentUser) {
    return <LoginPage onLogin={user => { localStorage.setItem('wolong_auth', JSON.stringify(user)); setCurrentUser(user) }} />
  }
  return <MainApp currentUser={currentUser} onLogout={() => { localStorage.removeItem('wolong_auth'); setCurrentUser(null) }} />
}

function MainApp({ currentUser, onLogout }) {
  const isMobile = useIsMobile()

  // ── 客户标签 & 备注 ──
  const [customerMeta, setCustomerMeta] = useState({}) // phone → {tags, notes, bizType}
  const [metaPanelOpen, setMetaPanelOpen] = useState(false)
  const [editingNotes, setEditingNotes] = useState('')
  const [tagFilter, setTagFilter] = useState(null)    // active tag filter string
  const [bizFilter, setBizFilter] = useState(null)    // active biz type filter key

  // ── 消息模板管理 ──
  const [templates, setTemplates] = useState(PRESET_TEMPLATES)
  const [tplPanelOpen, setTplPanelOpen] = useState(false)
  const [editingTpl, setEditingTpl] = useState(null) // null | template object (for edit/new)
  const [tplForm, setTplForm] = useState({ name: '', bizType: 'trade', lang: 'zh', langLabel: '中文', content: '' })

  // ── 新建联系 ──
  const [newContactOpen, setNewContactOpen] = useState(false)
  const [newContactForm, setNewContactForm] = useState({ phone: '', name: '', country: '', message: '', bizType: '' })
  const [selectedTplId, setSelectedTplId] = useState('')   // selected template id in new-contact form
  const [newContactStatus, setNewContactStatus] = useState(null) // null | 'sending' | 'ok' | 'err'
  const [newContactErr, setNewContactErr] = useState('')
  // 主动新建的联系人列表，独立于轮询不被覆盖
  const [addedContacts, setAddedContacts] = useState([])

  const [customers, setCustomers] = useState(fallbackCustomers)
  const [stats, setStats] = useState(fallbackStats)
  const [selectedId, setSelectedId] = useState(fallbackCustomers[0].id)
  const [loadingText, setLoadingText] = useState('正在读取 runtime 真源...')
  const [runtimeLocale, setRuntimeLocale] = useState('zh-CN')
  const [i18nDict, setI18nDict] = useState({})

  function ti(key, fallback) {
    const parts = key.split('.')
    let current = i18nDict
    for (const part of parts) {
      if (!current || typeof current !== 'object' || !(part in current)) return fallback
      current = current[part]
    }
    return typeof current === 'string' ? current : fallback
  }
  const [activeChannel, setActiveChannel] = useState('WhatsApp')
  const [mobileShowDetail, setMobileShowDetail] = useState(false)
  const [alerts, setAlerts] = useState([])
  // 手机端默认折叠预警中心，减少首屏干扰
  const [showAlerts, setShowAlerts] = useState(!isMobile)
  const [takeoverWorkbench, setTakeoverWorkbench] = useState({ count: 0, items: [], level_counts: { high: 0, medium: 0, low: 0 } })

  const [ingressMode, setIngressMode] = useState('readonly')
  const [autoClassify, setAutoClassify] = useState(true)
  const [autoTagging, setAutoTagging] = useState(true)
  const [h5Visible, setH5Visible] = useState(true)
  const [autoReply, setAutoReply] = useState(false)
  const [autoDispatch, setAutoDispatch] = useState(false)
  const [newCustomerCount, setNewCustomerCount] = useState(0)

  // ── 发消息面板 ──
  const [sendPanelOpen, setSendPanelOpen] = useState(false)
  const [sendForm, setSendForm] = useState({ phone: '', name: '', country: '', message: '' })
  const [sendStatus, setSendStatus] = useState(null) // null | 'sending' | 'ok' | 'err'
  const [sendErrMsg, setSendErrMsg] = useState('')

  // ── AI建议回复面板 ──
  const [aiReplyEnabled, setAiReplyEnabled] = useState(true)    // 主开关：默认开启
  const [aiAutoSend, setAiAutoSend] = useState(false)           // 子开关：允许AI自动发
  const [aiReplyText, setAiReplyText] = useState('')            // 当前AI建议文本
  const [aiReplyLoading, setAiReplyLoading] = useState(false)
  const [aiReplyStatus, setAiReplyStatus] = useState(null)      // null | 'approved' | 'sent' | 'err'
  const [aiTaskId, setAiTaskId] = useState(null)                // 当前 AI 建议的 task_id（用于回传闭环）
  const [aiOriginalSuggestion, setAiOriginalSuggestion] = useState('')  // AI 原始建议（用于判断是否被修改）
  const [aiExpCount, setAiExpCount] = useState(0)               // 注入的经验数量
  const [aiSource, setAiSource] = useState('')                  // AI 来源（gemini / claude / rule_fallback）

  // ── 历史客户重新激活 ──
  const [reactUploadStatus, setReactUploadStatus] = useState('idle') // idle | parsing | analyzing | done | error
  const [reactUploadError, setReactUploadError] = useState('')
  const [reactResults, setReactResults] = useState([])
  const [reactMyName, setReactMyName] = useState('')
  const [reactSelectedId, setReactSelectedId] = useState(null)
  const [reactAnalysisProgress, setReactAnalysisProgress] = useState({ current: 0, total: 0 })

  // ── 全部客户总表 ──
  const [allCustomers, setAllCustomers] = useState([])
  const [allSelectedId, setAllSelectedId] = useState(null)
  const [allLoading, setAllLoading] = useState(false)

  const knownIdsRef = useRef(new Set())
  const flashTimerRef = useRef(null)
  const flashToggleRef = useRef(false)
  const defaultTitleRef = useRef(typeof document !== 'undefined' ? document.title : '卧龙代理聊天实战工作台')

  useEffect(() => {
    let disposed = false

    async function loadI18nRuntime() {
      const configData = await fetchJson('/runtime/i18n_runtime_config_v1.json', {})
      const nextLocale =
        configData?.locale ||
        configData?.default_locale ||
        configData?.language ||
        configData?.lang ||
        'zh-CN'

      const rawDict = await fetchJson(`/runtime/i18n/${nextLocale}.json`, {})
      const normalizedDict =
        rawDict && typeof rawDict === 'object'
          ? (
              rawDict?.translations && typeof rawDict.translations === 'object'
                ? rawDict.translations
                : rawDict?.messages && typeof rawDict.messages === 'object'
                  ? rawDict.messages
                  : rawDict
            )
          : {}

      if (!disposed) {
        setRuntimeLocale(nextLocale)
        setI18nDict(normalizedDict)
      }
    }

    loadI18nRuntime()

    return () => {
      disposed = true
    }
  }, [])

  useEffect(() => {
    setSelectedId('')
    setNewCustomerCount(0)
    knownIdsRef.current = new Set()
    setLoadingText(ti('runtime.loading', '正在读取 runtime 真源...'))
  }, [activeChannel])


  useEffect(() => {
    let disposed = false

    async function loadAll() {
      const runtimeResult = await loadRuntimeCustomers(activeChannel)
      if (disposed) return

      setCustomers(runtimeResult.customers)
      setStats(runtimeResult.stats)
      setSelectedId((prev) => {
        const allIds = new Set([
          ...(runtimeResult.customers || []).map(c => c?.id).filter(Boolean),
          // also keep selection if it's a manually added contact
        ])
        // Check addedContacts via ref to avoid stale closure — we just preserve if prev is non-empty
        if (prev && !allIds.has(prev)) {
          // might be an addedContact — keep it (will re-check on render)
          return prev
        }
        return prev && allIds.has(prev) ? prev : (runtimeResult.customers?.[0]?.id || '')
      })

      const nextIds = new Set((runtimeResult.customers || []).map((item) => item?.id).filter(Boolean))
      if (knownIdsRef.current.size === 0) {
        knownIdsRef.current = nextIds
      } else {
        let foundNew = 0
        nextIds.forEach((id) => {
          if (!knownIdsRef.current.has(id)) foundNew += 1
        })
        if (foundNew > 0) {
          setNewCustomerCount((prev) => prev + foundNew)
        }
        knownIdsRef.current = nextIds
      }

      const controlData = await fetchJson('/runtime/views/whatsapp_control_snapshot.json', {})
      if (!disposed && controlData && typeof controlData === 'object') {
        setIngressMode(controlData.ingress_mode || 'readonly')
        setAutoClassify(Boolean(controlData.auto_classify))
        setAutoTagging(Boolean(controlData.auto_tagging))
        setH5Visible(Boolean(controlData.h5_visible))
        setAutoReply(Boolean(controlData.auto_reply))
        setAutoDispatch(Boolean(controlData.auto_dispatch))
      }

      const alertData = await fetchJson('/runtime/alerts/runtime_alerts_latest.json', { items: [] })
      if (!disposed && alertData?.items && Array.isArray(alertData.items)) {
        setAlerts(alertData.items)
      }

      const workbenchData = await fetchJson('/runtime/views/manual_takeover_workbench.json', { count: 0, items: [], level_counts: { high: 0, medium: 0, low: 0 } })
      if (!disposed && workbenchData && typeof workbenchData === 'object') {
        setTakeoverWorkbench({
          count: workbenchData.count || 0,
          items: Array.isArray(workbenchData.items) ? workbenchData.items : [],
          level_counts: workbenchData.level_counts || { high: 0, medium: 0, low: 0 },
        })
      }

      if (!disposed) {
        setLoadingText(ti('runtime.loaded', '已读取 runtime 真源'))
      }
    }

    loadAll()
    const timer = setInterval(loadAll, 8000)

    return () => {
      disposed = true
      clearInterval(timer)
    }
  }, [activeChannel])

  useEffect(() => {
    if (flashTimerRef.current) {
      clearInterval(flashTimerRef.current)
      flashTimerRef.current = null
    }

    if (newCustomerCount <= 0) {
      if (typeof document !== 'undefined') {
        document.title = defaultTitleRef.current
      }
      return
    }

    flashTimerRef.current = setInterval(() => {
      flashToggleRef.current = !flashToggleRef.current
      if (typeof document !== 'undefined') {
        document.title = flashToggleRef.current
          ? `【新客户 ${newCustomerCount}】${defaultTitleRef.current}`
          : defaultTitleRef.current
      }
    }, 1000)

    return () => {
      if (flashTimerRef.current) {
        clearInterval(flashTimerRef.current)
        flashTimerRef.current = null
      }
      if (typeof document !== 'undefined') {
        document.title = defaultTitleRef.current
      }
    }
  }, [newCustomerCount])

  useEffect(() => {
    const handleFocus = () => {
      setNewCustomerCount(0)
      if (typeof document !== 'undefined') {
        document.title = defaultTitleRef.current
      }
    }
    window.addEventListener('focus', handleFocus)
    return () => window.removeEventListener('focus', handleFocus)
  }, [])

  // ── 切换客户时自动获取 AI 建议回复 ──
  const aiReplyEnabledRef = useRef(aiReplyEnabled)
  useEffect(() => { aiReplyEnabledRef.current = aiReplyEnabled }, [aiReplyEnabled])

  useEffect(() => {
    if (!selectedId) return
    setAiReplyText('')
    setAiReplyStatus(null)
    setAiTaskId(null)
    setAiSource('')

    const t = setTimeout(() => {
      // 优先使用后台预生成的 AI 建议（webhook 收到消息后自动生成）
      const pending = selected?.pending_ai_reply
      if (pending?.text) {
        setAiReplyText(pending.text)
        setAiOriginalSuggestion(pending.text)
        setAiSource(pending.source || 'gemini')
        if (!aiReplyEnabledRef.current) setAiReplyEnabled(true)
        return
      }
      // 无预生成建议时，若 AI 面板已开启则主动请求
      if (aiReplyEnabledRef.current) {
        handleFetchAiReply() // eslint-disable-line react-hooks/exhaustive-deps
      }
    }, 400)
    return () => clearTimeout(t)
  }, [selectedId]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── 全部客户：合并 WhatsApp + Facebook + 历史激活 ──
  useEffect(() => {
    if (activeChannel !== '全部客户') return
    let disposed = false
    async function loadAll() {
      setAllLoading(true)
      const [wa, fbChat, fbFeed, react] = await Promise.all([
        fetchJson('/runtime/views/h5_dashboard_whatsapp.json', { customers: [] }),
        fetchJson('/runtime/views/h5_dashboard_facebook.json', { customers: [] }),
        fetchJson('/runtime/views/h5_dashboard_facebook_feed.json', { customers: [] }),
        fetch('/api/reactivation/list').then(r => r.ok ? r.json() : { results: [] }).catch(() => ({ results: [] })),
      ])
      if (disposed) return
      const waCusts = (wa?.customers || []).map(c => ({ ...c, _source: 'WhatsApp' }))
      const fbCusts = [
        ...(fbChat?.customers || []),
        ...(fbFeed?.customers || []),
      ].map(c => ({ ...c, _source: 'Facebook' }))
      const reactCusts = (react?.results || []).map(r => ({
        id: r.id,
        name: r.customer_name || r.filename,
        phone: r.phone || '-',
        country: r.country || '未知',
        time: r.analyzed_at || '—',
        message: r.last_contact_summary || r.no_deal_reason || '—',
        keywords: r.car_models_interested || [],
        messages: r.messages || [],
        category: r.intent_level || 'unknown',
        _source: '历史激活',
        _react: r, // keep original for detail panel
      }))
      const merged = [...reactCusts, ...waCusts, ...fbCusts]
      setAllCustomers(merged)
      if (!allSelectedId && merged.length > 0) setAllSelectedId(merged[0].id)
      setAllLoading(false)
    }
    loadAll()
    const t = setInterval(loadAll, 10000)
    return () => { disposed = true; clearInterval(t) }
  }, [activeChannel]) // eslint-disable-line react-hooks/exhaustive-deps

  const isFacebookEmptyView = activeChannel === 'Facebook' && customers.length === 0
  const channelEmptyState = isFacebookEmptyView
    ? {
        id: 'facebook_empty_view',
        name: ti('facebook.empty.name', 'Facebook 暂无数据'),
        category: '待判断',
        country: '未知',
        channel: 'Facebook',
        phone: '-',
        reason: ti('facebook.empty.reason', '请保持 Facebook webhook 在线，并等待真实聊天或公开互动进入。'),
        keywords: [],
        timeline: [],
        messages: [],
        needs_human_review: false,
      }
    : null
  const selected = customers.find((x) => x.id === selectedId) || addedContacts.find((x) => x.id === selectedId) || customers[0] || channelEmptyState || fallbackCustomers[0]
  const isHot = selected.category === '准车商'
  const { proactiveCount, exchangeCount } = useMemo(() => getCounts(selected.messages), [selected])

  const emergencyStop = () => {
    window.alert('当前按钮只做展示。真实止水动作请走 AgentOS 后端治理配置链。')
  }

  // ── 加载全部客户标签 & 业务分类 ──
  useEffect(() => {
    fetchJson('/api/customer_meta_all', {}).then(data => {
      if (data && typeof data === 'object') setCustomerMeta(data)
    })
  }, [])

  // ── 加载模板列表 ──
  useEffect(() => {
    fetchJson('/api/templates', null).then(data => {
      if (Array.isArray(data) && data.length > 0) setTemplates(data)
    })
  }, [])

  // ── 切换客户时同步备注文本 ──
  useEffect(() => {
    const phone = selected?.phone
    if (!phone || phone === '-') return
    const meta = customerMeta[phone]
    setEditingNotes(meta?.notes || '')
    setMetaPanelOpen(false)
  }, [selected?.phone]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── 标签切换 ──
  function toggleTag(phone, tag) {
    const current = customerMeta[phone] || { tags: [], notes: '', bizType: '' }
    const tags = current.tags.includes(tag)
      ? current.tags.filter(t => t !== tag)
      : [...current.tags, tag]
    const updated = { ...current, tags }
    setCustomerMeta(prev => ({ ...prev, [phone]: updated }))
    fetch('/api/customer_meta', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, tags, notes: current.notes || '', bizType: current.bizType || '' }),
    }).catch(() => {})
  }

  // ── 保存备注 ──
  async function saveNotes(phone, notes) {
    const current = customerMeta[phone] || { tags: [], notes: '', bizType: '' }
    const updated = { ...current, notes }
    setCustomerMeta(prev => ({ ...prev, [phone]: updated }))
    await fetch('/api/customer_meta', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, tags: current.tags || [], notes, bizType: current.bizType || '' }),
    }).catch(() => {})
  }

  // ── 保存业务分类 ──
  function saveBizType(phone, bizType) {
    const current = customerMeta[phone] || { tags: [], notes: '', bizType: '' }
    const updated = { ...current, bizType }
    setCustomerMeta(prev => ({ ...prev, [phone]: updated }))
    fetch('/api/customer_meta', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, tags: current.tags || [], notes: current.notes || '', bizType }),
    }).catch(() => {})
  }

  // ── 模板 CRUD ──
  async function saveTplForm() {
    const isEdit = !!editingTpl?.id && !editingTpl.id.startsWith('_new')
    const tpl = isEdit
      ? { ...editingTpl, ...tplForm }
      : { ...tplForm, id: 'tpl_' + Date.now() }
    try {
      const resp = await fetch('/api/templates', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tpl),
      })
      const data = await resp.json()
      if (data.templates) setTemplates(data.templates)
      else setTemplates(prev => {
        const idx = prev.findIndex(t => t.id === tpl.id)
        return idx >= 0 ? prev.map((t, i) => i === idx ? tpl : t) : [...prev, tpl]
      })
      setEditingTpl(null)
    } catch { /* silently fail */ }
  }

  async function deleteTpl(id) {
    try {
      const resp = await fetch(`/api/templates?id=${encodeURIComponent(id)}`, { method: 'DELETE' })
      const data = await resp.json()
      if (data.templates) setTemplates(data.templates)
      else setTemplates(prev => prev.filter(t => t.id !== id))
    } catch { /* silently fail */ }
  }

  // ── 新建联系 ──
  async function handleNewContact() {
    if (!newContactForm.phone.trim()) { setNewContactErr('手机号不能为空'); return }
    if (!newContactForm.message.trim()) { setNewContactErr('第一条消息不能为空'); return }
    setNewContactErr('')
    setNewContactStatus('sending')
    try {
      const resp = await fetch('/api/new_contact', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newContactForm),
      })
      const data = await resp.json()
      if (data.success) {
        const c = data.contact || {}
        const phone = c.phone || newContactForm.phone
        const name = c.name || newContactForm.name || phone
        const now = new Date()
        const hhmm = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`
        // 把新联系人插入到客户列表头部
        const newCust = {
          id: phone,
          phone,
          name,
          country: c.country || newContactForm.country || '',
          time: hhmm,
          message: newContactForm.message,
          category: data.mode === 'mock' ? '🧪 测试联系' : '新建联系',
          messages: [
            {
              id: Date.now(),
              role: 'agent',
              text: newContactForm.message,
              time: hhmm,
            }
          ],
          _isMock: data.mode === 'mock',
        }
        setAddedContacts(prev => {
          // 避免重复添加同一号码
          const filtered = prev.filter(c => c.phone !== phone)
          return [newCust, ...filtered]
        })
        // 自动打上业务分类标签
        if (newContactForm.bizType) {
          saveBizType(phone, newContactForm.bizType)
        }
        setSelectedId(phone)
        setSelectedTplId('')
        setNewContactStatus(data.mode === 'mock' ? 'mock_ok' : 'ok')
        setNewContactForm({ phone: '', name: '', country: '', message: '', bizType: '' })
        setTimeout(() => { setNewContactStatus(null); setNewContactOpen(false) }, 3000)
      } else {
        setNewContactStatus('err')
        setNewContactErr(data.error || '发送失败')
      }
    } catch {
      setNewContactStatus('err')
      setNewContactErr('无法连接后端')
    }
  }

  // ── 发送测试消息 ──
  async function handleSendMessage() {
    if (!sendForm.message.trim()) { setSendErrMsg('消息内容不能为空'); return }
    if (!sendForm.phone.trim()) { setSendErrMsg('电话号码不能为空'); return }
    setSendErrMsg('')
    setSendStatus('sending')
    try {
      const resp = await fetch('/api/send_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sendForm),
      })
      const data = await resp.json()
      if (data.success) {
        setSendStatus('ok')
        setSendForm((f) => ({ ...f, message: '' }))
        setTimeout(() => setSendStatus(null), 3000)
      } else {
        setSendStatus('err')
        setSendErrMsg(data.error || '发送失败')
      }
    } catch {
      setSendStatus('err')
      setSendErrMsg('无法连接到后端 API，请确认 api_server.py 已启动（端口 8765）')
    }
  }

  // ── 获取AI建议回复（走闭环管理器）──
  async function handleFetchAiReply() {
    if (!selected || !selected.id || selected.id === 'fallback_1') return
    setAiReplyLoading(true)
    setAiReplyStatus(null)
    setAiTaskId(null)
    try {
      const resp = await fetch('/api/ai_reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: selected.phone,
          customer_name: selected.name,
          country: selected.country,
          category: selected.category,
          last_message: selected.messages?.slice(-1)?.[0]?.text || selected.message || '',
          conversation_history: selected.messages || [],
          auto_send: aiAutoSend,
        }),
      })
      const data = await resp.json()
      if (data.suggested_reply) {
        setAiReplyText(data.suggested_reply)
        setAiOriginalSuggestion(data.suggested_reply)
        setAiTaskId(data.task_id || null)
        setAiExpCount(data.experience_count || 0)
        setAiSource(data.generated_by || '')
      } else {
        setAiReplyText('（AI暂时无法生成建议，请人工回复）')
      }
    } catch {
      setAiReplyText('（连接后端失败，请确认 api_server.py 已启动）')
    }
    setAiReplyLoading(false)
  }

  // ── 人工采纳/修改AI回复 → 回传闭环 ──
  async function handleApproveAiReply() {
    if (!aiReplyText.trim()) return
    setAiReplyStatus('sending')
    const humanModified = aiReplyText !== aiOriginalSuggestion
    const humanApproved = !humanModified  // 未修改 = 完全采纳

    try {
      // 1. 发送消息到 runtime
      const sendResp = await fetch('/api/send_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: selected.phone,
          name: selected.name,
          country: selected.country,
          message: aiReplyText,
          role: 'agent',
        }),
      })
      const sendData = await sendResp.json()

      // 2. 回传闭环（记录人类决策到经验库）
      if (aiTaskId) {
        await fetch('/api/approve_reply', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            task_id: aiTaskId,
            final_reply: aiReplyText,
            human_approved: humanApproved,
            customer_msg: selected.messages?.slice(-1)?.[0]?.text || selected.message || '',
            ai_suggested: aiOriginalSuggestion,
            category: selected.category,
            country: selected.country,
            outcome: 'sent',
          }),
        }).catch(() => {})  // 回传失败不影响主流程
      }

      setAiReplyStatus(sendData.success ? 'sent' : 'err')
      if (sendData.success) {
        setTimeout(() => { setAiReplyStatus(null); setAiReplyText(''); setAiTaskId(null) }, 3000)
      }
    } catch {
      setAiReplyStatus('err')
    }
  }

  // ── 忽略AI建议（记录到经验库：未采纳）──
  async function handleIgnoreAiReply() {
    if (aiTaskId) {
      await fetch('/api/approve_reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: aiTaskId,
          final_reply: '',
          human_approved: false,
          outcome: 'ignored',
          category: selected.category,
          country: selected.country,
        }),
      }).catch(() => {})
    }
    setAiReplyText('')
    setAiTaskId(null)
    setAiReplyStatus(null)
  }

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      overflow: 'hidden',
      background: '#f8fafc',
    }}>

      {/* ══════════ LEFT SIDEBAR ══════════ */}
      {(!isMobile || !mobileShowDetail) && (
        <div style={{
          width: isMobile ? '100%' : '290px',
          minWidth: isMobile ? 'unset' : '290px',
          background: '#ffffff',
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          overflow: 'hidden',
          flexShrink: 0,
        }}>
          {/* Sidebar header */}
          <div style={{ padding: '14px 14px 10px', borderBottom: '1px solid #f3f4f6' }}>
            {/* Brand + user info row */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <div>
                <div style={{ fontSize: '16px', fontWeight: 800, color: '#111827', letterSpacing: '-0.3px' }}>卧龙 CRM</div>
                <div style={{ fontSize: '10px', color: '#6b7280', marginTop: '1px' }}>{loadingText}</div>
              </div>
              <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                {newCustomerCount > 0 && (
                  <div title="新进客户数量" style={{ background: '#10b981', color: '#fff', borderRadius: '999px', padding: '2px 7px', fontSize: '10px', fontWeight: 700, cursor: 'default' }}>
                    +{newCustomerCount}
                  </div>
                )}
                {alerts.length > 0 && (
                  <button onClick={() => setShowAlerts(v => !v)}
                    title="系统警报，点击查看详情" style={{ background: '#ef4444', color: '#fff', border: 'none', borderRadius: '999px', padding: '2px 7px', fontSize: '10px', fontWeight: 700, cursor: 'pointer' }}>
                    🚨 {alerts.length}
                  </button>
                )}
              </div>
            </div>
            {/* Logged-in user info + logout */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#f9fafb', borderRadius: '8px', padding: '6px 9px', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: currentUser.role === 'admin' ? '#f59e0b' : '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px' }}>
                  {currentUser.role === 'admin' ? '👑' : '👤'}
                </div>
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#111827' }}>{currentUser.display_name}</div>
                  <div style={{ fontSize: '9px', color: '#9ca3af' }}>{currentUser.role === 'admin' ? '管理员' : '销售员'}</div>
                </div>
              </div>
              <button onClick={onLogout}
                style={{ fontSize: '10px', color: '#9ca3af', background: 'transparent', border: 'none', cursor: 'pointer', padding: '2px 6px', borderRadius: '5px' }}>
                退出
              </button>
            </div>

            {/* Stats chips */}
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
              {stats.map(s => (
                <div key={s.label} style={{ background: '#f3f4f6', borderRadius: '6px', padding: '3px 7px', fontSize: '10px', color: '#9ca3af' }}>
                  <span style={{ fontWeight: 800, color: '#111827' }}>{s.value}</span>{' '}{s.label}
                </div>
              ))}
            </div>

            {/* Takeover notice */}
            {takeoverWorkbench.count > 0 && (
              <div
                onClick={() => {
                  const first = takeoverWorkbench.items?.[0]
                  if (first?.phone) {
                    const match = customers.find(c => c.phone === first.phone || c.id === first.phone)
                    if (match) { setSelected(match); if (isMobile) setMobileShowDetail(true) }
                  }
                }}
                style={{ marginTop: '7px', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '6px', padding: '5px 10px', fontSize: '11px', color: '#1d4ed8', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>⚡ {takeoverWorkbench.count} 条待接管，点击查看</span>
                {takeoverWorkbench.level_counts?.high > 0 && (
                  <span style={{ background: '#fee2e2', color: '#b91c1c', borderRadius: '4px', padding: '1px 6px', fontSize: '10px', fontWeight: 700 }}>高优 {takeoverWorkbench.level_counts.high}</span>
                )}
              </div>
            )}
          </div>

          {/* Channel tabs */}
          <div style={{ padding: '8px 10px 6px', borderBottom: '1px solid #f3f4f6' }}>
            <div style={{ display: 'flex', gap: '3px', flexWrap: 'wrap' }}>
              {channels.map(ch => {
                const active = ch === activeChannel
                const label =
                  ch === 'WhatsApp' ? '💬 WA' :
                  ch === 'Facebook' ? '👥 FB' :
                  ch === '历史激活' ? '📂 激活' :
                  ch === '全部客户' ? '🗂 全部' :
                  ch
                return (
                  <button
                    key={ch}
                    onClick={() => setActiveChannel(ch)}
                    style={{
                      padding: '4px 9px', borderRadius: '6px', border: 'none',
                      background: active ? '#2563eb' : 'rgba(255,255,255,0.06)',
                      color: active ? '#fff' : '#94a3b8',
                      fontWeight: active ? 700 : 400,
                      cursor: 'pointer', fontSize: '11px',
                    }}
                  >
                    {label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Customer list header: filters + actions */}
          {activeChannel !== '历史激活' && activeChannel !== '全部客户' && (
            <div style={{ padding: '6px 8px 4px', borderBottom: '1px solid #f3f4f6' }}>
              {/* Biz-type filter chips */}
              <div style={{ display: 'flex', gap: '3px', flexWrap: 'wrap', marginBottom: '4px' }}>
                <button onClick={() => setBizFilter(null)}
                  style={{ padding: '2px 7px', borderRadius: '999px', fontSize: '10px', border: 'none', background: bizFilter === null ? '#2563eb' : 'rgba(255,255,255,0.08)', color: bizFilter === null ? '#fff' : '#64748b', cursor: 'pointer' }}>
                  全部
                </button>
                {BIZ_TYPES.map(bt => (
                  <button key={bt.key} onClick={() => setBizFilter(bizFilter === bt.key ? null : bt.key)}
                    style={{ padding: '2px 7px', borderRadius: '999px', fontSize: '10px', border: 'none', background: bizFilter === bt.key ? bt.bg : 'rgba(255,255,255,0.06)', color: bizFilter === bt.key ? bt.color : '#64748b', cursor: 'pointer', fontWeight: bizFilter === bt.key ? 700 : 400 }}>
                    {bt.label}
                  </button>
                ))}
              </div>
              {/* Behavior tag filter chips */}
              <div style={{ display: 'flex', gap: '3px', flexWrap: 'wrap', marginBottom: '5px' }}>
                {PRESET_TAGS.map(t => (
                  <button key={t.label} onClick={() => setTagFilter(tagFilter === t.label ? null : t.label)}
                    style={{ padding: '2px 7px', borderRadius: '999px', fontSize: '10px', border: 'none', background: tagFilter === t.label ? t.bg : 'rgba(255,255,255,0.06)', color: tagFilter === t.label ? t.color : '#64748b', cursor: 'pointer', fontWeight: tagFilter === t.label ? 700 : 400 }}>
                    {t.label}
                  </button>
                ))}
              </div>
              {/* Actions row */}
              <div style={{ display: 'flex', gap: '4px' }}>
                <button onClick={() => { setNewContactOpen(v => !v); setNewContactStatus(null); setNewContactErr(''); setSelectedTplId('') }}
                  style={{ flex: 1, padding: '6px', borderRadius: '7px', border: '1px dashed rgba(255,255,255,0.15)', background: newContactOpen ? 'rgba(37,99,235,0.2)' : 'transparent', color: newContactOpen ? '#93c5fd' : '#64748b', fontSize: '11px', cursor: 'pointer', fontWeight: 600 }}>
                  {newContactOpen ? '✕ 取消' : '+ 新建联系'}
                </button>
                <button onClick={() => setTplPanelOpen(v => !v)}
                  style={{ padding: '6px 8px', borderRadius: '7px', border: '1px dashed rgba(255,255,255,0.15)', background: tplPanelOpen ? 'rgba(124,58,237,0.2)' : 'transparent', color: tplPanelOpen ? '#c4b5fd' : '#64748b', fontSize: '11px', cursor: 'pointer' }}
                  title="模板管理">
                  📝
                </button>
              </div>

              {/* New contact form */}
              {newContactOpen && (
                <div style={{ marginTop: '7px', background: '#f9fafb', borderRadius: '8px', padding: '8px' }}>
                  {/* Biz type selector */}
                  <div style={{ marginBottom: '6px' }}>
                    <div style={{ fontSize: '9px', color: '#6b7280', marginBottom: '3px' }}>客户分类</div>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      {BIZ_TYPES.map(bt => (
                        <button key={bt.key} onClick={() => { setNewContactForm(p => ({ ...p, bizType: bt.key })); setSelectedTplId('') }}
                          style={{ flex: 1, padding: '4px 2px', borderRadius: '5px', border: `1px solid ${newContactForm.bizType === bt.key ? bt.border : 'rgba(255,255,255,0.1)'}`, background: newContactForm.bizType === bt.key ? bt.bg + '22' : 'rgba(255,255,255,0.04)', color: newContactForm.bizType === bt.key ? bt.color : '#64748b', fontSize: '10px', cursor: 'pointer', fontWeight: newContactForm.bizType === bt.key ? 700 : 400 }}>
                          {bt.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  {/* Basic fields */}
                  {[
                    { key: 'phone', placeholder: '+8613900000000  (必填)', label: '手机号' },
                    { key: 'name',  placeholder: 'Ahmad',              label: '姓名' },
                    { key: 'country', placeholder: '阿联酋',           label: '国家' },
                  ].map(f => (
                    <div key={f.key} style={{ marginBottom: '5px' }}>
                      <div style={{ fontSize: '9px', color: '#6b7280', marginBottom: '2px' }}>{f.label}</div>
                      <input value={newContactForm[f.key]} onChange={e => setNewContactForm(p => ({ ...p, [f.key]: e.target.value }))}
                        placeholder={f.placeholder}
                        style={{ width: '100%', padding: '5px 7px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '5px', background: '#f3f4f6', color: '#111827', fontSize: '11px', boxSizing: 'border-box' }} />
                    </div>
                  ))}
                  {/* Template selector */}
                  {(() => {
                    const bizTemplates = templates.filter(t => !newContactForm.bizType || t.bizType === newContactForm.bizType)
                    if (!bizTemplates.length) return null
                    return (
                      <div style={{ marginBottom: '5px' }}>
                        <div style={{ fontSize: '9px', color: '#6b7280', marginBottom: '3px' }}>选择话术模板（可选）</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                          {bizTemplates.map(tpl => (
                            <button key={tpl.id} onClick={() => {
                              setSelectedTplId(tpl.id)
                              const filled = applyTemplateVars(tpl.content, { name: newContactForm.name, country: newContactForm.country })
                              setNewContactForm(p => ({ ...p, message: filled }))
                            }}
                              style={{ textAlign: 'left', padding: '4px 7px', borderRadius: '5px', border: `1px solid ${selectedTplId === tpl.id ? '#6366f1' : 'rgba(255,255,255,0.1)'}`, background: selectedTplId === tpl.id ? 'rgba(99,102,241,0.15)' : 'rgba(255,255,255,0.04)', color: selectedTplId === tpl.id ? '#c7d2fe' : '#94a3b8', fontSize: '10px', cursor: 'pointer' }}>
                              <span style={{ fontWeight: 600, marginRight: '4px' }}>{tpl.name}</span>
                              <span style={{ opacity: 0.6 }}>[{tpl.langLabel}]</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )
                  })()}
                  {/* Message */}
                  <div style={{ marginBottom: '6px' }}>
                    <div style={{ fontSize: '9px', color: '#6b7280', marginBottom: '2px' }}>第一条消息（必填）</div>
                    <textarea value={newContactForm.message} onChange={e => { setNewContactForm(p => ({ ...p, message: e.target.value })); setSelectedTplId('') }}
                      placeholder="您好！我们是卧龙汽车..."
                      rows={3}
                      style={{ width: '100%', padding: '5px 7px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '5px', background: '#f3f4f6', color: '#111827', fontSize: '11px', boxSizing: 'border-box', resize: 'none' }} />
                  </div>
                  {newContactErr && <div style={{ fontSize: '10px', color: '#fca5a5', marginBottom: '5px' }}>⚠ {newContactErr}</div>}
                  {newContactStatus === 'ok' && <div style={{ fontSize: '10px', color: '#86efac', marginBottom: '5px' }}>✅ 已发送！联系人已加入客户列表</div>}
                  {newContactStatus === 'mock_ok' && (
                    <div style={{ fontSize: '10px', marginBottom: '5px', padding: '5px 7px', background: 'rgba(251,191,36,0.15)', border: '1px solid rgba(251,191,36,0.3)', borderRadius: '5px', color: '#fbbf24', lineHeight: '1.5' }}>
                      🧪 <strong>测试模式</strong>：联系人已加入列表<br/>（未发送真实消息）
                    </div>
                  )}
                  <button onClick={handleNewContact} disabled={newContactStatus === 'sending' || newContactStatus === 'ok' || newContactStatus === 'mock_ok'}
                    style={{ width: '100%', padding: '6px', borderRadius: '6px', border: 'none', background: (newContactStatus === 'sending') ? '#1e3a8a' : (newContactStatus === 'ok' || newContactStatus === 'mock_ok') ? '#374151' : '#2563eb', color: '#fff', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}>
                    {newContactStatus === 'sending' ? '发送中...' : (newContactStatus === 'ok' || newContactStatus === 'mock_ok') ? '✓ 完成' : '📨 发送第一条消息'}
                  </button>
                </div>
              )}

              {/* Template management panel */}
              {tplPanelOpen && (
                <div style={{ marginTop: '7px', background: 'rgba(124,58,237,0.07)', border: '1px solid rgba(124,58,237,0.2)', borderRadius: '8px', padding: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '7px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: '#c4b5fd' }}>📝 话术模板管理</span>
                    <button onClick={() => { setEditingTpl({ id: '_new' }); setTplForm({ name: '', bizType: 'trade', lang: 'zh', langLabel: '中文', content: '' }) }}
                      style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '5px', border: 'none', background: '#7c3aed', color: '#fff', cursor: 'pointer' }}>
                      + 新增
                    </button>
                  </div>
                  {/* Template list */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', maxHeight: '220px', overflowY: 'auto' }}>
                    {templates.map(tpl => {
                      const bt = BIZ_TYPES.find(b => b.key === tpl.bizType)
                      return (
                        <div key={tpl.id} style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '6px', padding: '6px 8px', border: '1px solid rgba(255,255,255,0.08)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '4px' }}>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{ fontSize: '11px', fontWeight: 600, color: '#111827', marginBottom: '2px' }}>{tpl.name}</div>
                              <div style={{ display: 'flex', gap: '4px', marginBottom: '3px' }}>
                                {bt && <span style={{ fontSize: '9px', padding: '1px 5px', borderRadius: '999px', background: bt.bg + '22', color: bt.color }}>{bt.label}</span>}
                                <span style={{ fontSize: '9px', padding: '1px 5px', borderRadius: '999px', background: '#f3f4f6', color: '#94a3b8' }}>{tpl.langLabel}</span>
                              </div>
                              <div style={{ fontSize: '10px', color: '#9ca3af', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>{tpl.content}</div>
                            </div>
                            <div style={{ display: 'flex', gap: '3px', flexShrink: 0 }}>
                              <button onClick={() => { setEditingTpl(tpl); setTplForm({ name: tpl.name, bizType: tpl.bizType, lang: tpl.lang, langLabel: tpl.langLabel, content: tpl.content }) }}
                                style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', border: 'none', background: '#f3f4f6', color: '#94a3b8', cursor: 'pointer' }}>
                                编辑
                              </button>
                              <button onClick={() => { if (window.confirm(`删除模板「${tpl.name}」？`)) deleteTpl(tpl.id) }}
                                style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', border: 'none', background: 'rgba(220,38,38,0.15)', color: '#fca5a5', cursor: 'pointer' }}>
                                删
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                  {/* Edit form */}
                  {editingTpl && (
                    <div style={{ marginTop: '8px', background: '#f9fafb', borderRadius: '6px', padding: '8px', border: '1px solid rgba(124,58,237,0.3)' }}>
                      <div style={{ fontSize: '10px', fontWeight: 700, color: '#c4b5fd', marginBottom: '6px' }}>
                        {editingTpl.id === '_new' ? '新增模板' : '编辑模板'}
                      </div>
                      {[
                        { key: 'name', label: '模板名称', placeholder: '贸易-阿文开场' },
                      ].map(f => (
                        <div key={f.key} style={{ marginBottom: '5px' }}>
                          <div style={{ fontSize: '9px', color: '#9ca3af', marginBottom: '2px' }}>{f.label}</div>
                          <input value={tplForm[f.key]} onChange={e => setTplForm(p => ({ ...p, [f.key]: e.target.value }))}
                            placeholder={f.placeholder}
                            style={{ width: '100%', padding: '4px 6px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', background: '#f3f4f6', color: '#111827', fontSize: '11px', boxSizing: 'border-box' }} />
                        </div>
                      ))}
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '5px', marginBottom: '5px' }}>
                        <div>
                          <div style={{ fontSize: '9px', color: '#9ca3af', marginBottom: '2px' }}>业务类型</div>
                          <select value={tplForm.bizType} onChange={e => setTplForm(p => ({ ...p, bizType: e.target.value }))}
                            style={{ width: '100%', padding: '4px 6px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', background: '#1e2a3a', color: '#111827', fontSize: '11px' }}>
                            {BIZ_TYPES.map(bt => <option key={bt.key} value={bt.key}>{bt.label}</option>)}
                          </select>
                        </div>
                        <div>
                          <div style={{ fontSize: '9px', color: '#9ca3af', marginBottom: '2px' }}>语言</div>
                          <select value={tplForm.lang} onChange={e => {
                            const labels = { zh: '中文', en: '英文', ru: '俄文', ar: '阿拉伯文' }
                            setTplForm(p => ({ ...p, lang: e.target.value, langLabel: labels[e.target.value] || e.target.value }))
                          }}
                            style={{ width: '100%', padding: '4px 6px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', background: '#1e2a3a', color: '#111827', fontSize: '11px' }}>
                            <option value="zh">中文</option>
                            <option value="en">英文</option>
                            <option value="ru">俄文</option>
                            <option value="ar">阿拉伯文</option>
                          </select>
                        </div>
                      </div>
                      <div style={{ marginBottom: '6px' }}>
                        <div style={{ fontSize: '9px', color: '#9ca3af', marginBottom: '2px' }}>模板内容（支持 &#123;name&#125; &#123;country&#125; 变量）</div>
                        <textarea value={tplForm.content} onChange={e => setTplForm(p => ({ ...p, content: e.target.value }))}
                          placeholder="Hi {name}, we are..."
                          rows={3}
                          style={{ width: '100%', padding: '4px 6px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', background: '#f3f4f6', color: '#111827', fontSize: '11px', boxSizing: 'border-box', resize: 'none' }} />
                      </div>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <button onClick={saveTplForm}
                          style={{ flex: 1, padding: '5px', borderRadius: '5px', border: 'none', background: '#7c3aed', color: '#fff', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}>
                          保存
                        </button>
                        <button onClick={() => setEditingTpl(null)}
                          style={{ padding: '5px 10px', borderRadius: '5px', border: '1px solid rgba(255,255,255,0.1)', background: 'transparent', color: '#9ca3af', fontSize: '11px', cursor: 'pointer' }}>
                          取消
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Customer list */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '6px 8px' }}>
            {(activeChannel === '历史激活' || activeChannel === '全部客户') && (
              <div style={{ padding: '24px 10px', textAlign: 'center', color: '#334155', fontSize: '12px' }}>
                {activeChannel === '历史激活' ? '📂 查看右侧激活面板' : '🗂 查看右侧全部客户'}
              </div>
            )}
            {activeChannel !== '历史激活' && activeChannel !== '全部客户' && (() => {
              // 合并主动新建的联系人（去重：若 phone 已存在于 customers 则不重复显示）
              const existingPhones = new Set(customers.map(c => c.phone || c.id))
              const freshAdded = addedContacts.filter(c => !existingPhones.has(c.phone))
              const allCustomers = [...freshAdded, ...customers]
              // Admin sees all; sales sees assigned phones (or all if no assignment yet)
              const assignedPhones = currentUser.assigned_phones || []
              let visibleCustomers = currentUser.role === 'admin' || assignedPhones.length === 0
                ? allCustomers
                : allCustomers.filter(c => assignedPhones.includes(c.phone))
              // Apply biz-type filter
              if (bizFilter) {
                visibleCustomers = visibleCustomers.filter(c =>
                  (customerMeta[c.phone]?.bizType || '') === bizFilter
                )
              }
              // Apply behavior tag filter
              if (tagFilter) {
                visibleCustomers = visibleCustomers.filter(c =>
                  (customerMeta[c.phone]?.tags || []).includes(tagFilter)
                )
              }
              return visibleCustomers
            })().map(item => {
              const active = item.id === selectedId
              const flag = getCountryFlag(item.country)
              const itemTags = customerMeta[item.phone]?.tags || []
              return (
                <div
                  key={item.id}
                  onClick={() => { setSelectedId(item.id); if (isMobile) { setMobileShowDetail(true); window.scrollTo(0, 0) } }}
                  style={{
                    padding: '9px 10px', borderRadius: '9px',
                    background: active ? 'rgba(37,99,235,0.22)' : 'transparent',
                    cursor: 'pointer', marginBottom: '1px',
                    display: 'flex', gap: '9px', alignItems: 'flex-start',
                  }}
                >
                  <div style={{
                    width: '38px', height: '38px', borderRadius: '50%',
                    background: active ? '#2563eb' : '#2d3a5e',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '18px', flexShrink: 0,
                  }}>
                    {flag}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: active ? '#fff' : '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '150px' }}>
                        {item.name}
                      </div>
                      <div style={{ fontSize: '9px', color: '#6b7280', flexShrink: 0 }}>
                        {item.time && item.time !== '—' ? item.time.slice(-5) : ''}
                      </div>
                    </div>
                    <div style={{ fontSize: '11px', color: active ? '#93c5fd' : '#4e6488', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: '2px' }}>
                      {item.message || '暂无消息'}
                    </div>
                    <div style={{ display: 'flex', gap: '3px', marginTop: '4px', alignItems: 'center', flexWrap: 'wrap' }}>
                      {/* Biz type badge */}
                      {(() => {
                        const biz = customerMeta[item.phone]?.bizType
                        const bt = biz ? BIZ_TYPES.find(b => b.key === biz) : null
                        if (!bt) return null
                        return (
                          <span style={{ fontSize: '8px', padding: '1px 5px', borderRadius: '999px', background: bt.bg + '22', color: bt.color, border: `1px solid ${bt.border}55`, fontWeight: 700 }}>
                            {bt.label}
                          </span>
                        )
                      })()}
                      <span style={{
                        fontSize: '9px', padding: '1px 5px', borderRadius: '999px',
                        background: item.category === '准车商' ? 'rgba(22,101,52,0.5)' : 'rgba(255,255,255,0.07)',
                        color: item.category === '准车商' ? '#86efac' : '#64748b',
                      }}>
                        {item.category}
                      </span>
                      {item.needs_human_review && <span style={{ fontSize: '9px', color: '#f87171' }}>⚠</span>}
                      {itemTags.slice(0, 2).map(tag => {
                        const preset = PRESET_TAGS.find(p => p.label === tag)
                        return (
                          <span key={tag} style={{ fontSize: '8px', padding: '1px 4px', borderRadius: '999px', background: preset ? preset.bg + '33' : 'rgba(255,255,255,0.1)', color: preset ? preset.color : '#94a3b8', border: `1px solid ${preset ? preset.border + '55' : 'rgba(255,255,255,0.1)'}` }}>
                            {tag}
                          </span>
                        )
                      })}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Sidebar footer: system status */}
          <div style={{ padding: '7px 12px', borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', gap: '10px', flexWrap: 'wrap', fontSize: '9px', color: '#334155' }}>
            <span>接入: {getModeLabel(ingressMode)}</span>
            <span>自动回复: {autoReply ? '开' : '关'}</span>
            <span>AI: {aiReplyEnabled ? '开' : '关'}</span>
          </div>
        </div>
      )}

      {/* ══════════ MAIN CONTENT ══════════ */}
      {(!isMobile || mobileShowDetail || activeChannel === '历史激活' || activeChannel === '全部客户') && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', minWidth: 0 }}>

          {/* Alert banner */}
          {showAlerts && alerts.length > 0 && (
            <div style={{ background: '#fef2f2', borderBottom: '1px solid #fecaca', padding: '7px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
              <div style={{ fontSize: '12px', color: '#b91c1c', fontWeight: 600 }}>
                🚨 {alerts[0].title}: {alerts[0].message}
                {alerts.length > 1 && <span style={{ color: '#dc2626' }}> (+{alerts.length - 1})</span>}
              </div>
              <button onClick={() => setShowAlerts(false)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#9ca3af', fontSize: '18px', lineHeight: 1 }}>×</button>
            </div>
          )}

          {/* ── 历史激活 ── */}
          {activeChannel === '历史激活' && (
            <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
              <ReactivationPanel
                uploadStatus={reactUploadStatus} setUploadStatus={setReactUploadStatus}
                uploadError={reactUploadError} setUploadError={setReactUploadError}
                results={reactResults} setResults={setReactResults}
                myName={reactMyName} setMyName={setReactMyName}
                selectedId={reactSelectedId} setSelectedId={setReactSelectedId}
                progress={reactAnalysisProgress} setProgress={setReactAnalysisProgress}
              />
            </div>
          )}

          {/* ── 全部客户 ── */}
          {activeChannel === '全部客户' && (
            <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
              <AllCustomersPanel customers={allCustomers} selectedId={allSelectedId} setSelectedId={setAllSelectedId} loading={allLoading} />
            </div>
          )}

          {/* ── WhatsApp / Facebook chat view ── */}
          {activeChannel !== '历史激活' && activeChannel !== '全部客户' && (
            <>
              {/* Customer header bar */}
              <div style={{ padding: '10px 16px', background: '#fff', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0, flexWrap: 'wrap' }}>
                {isMobile && (
                  <button onClick={() => setMobileShowDetail(false)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', fontSize: '20px', color: '#374151' }}>←</button>
                )}
                <div style={{ fontSize: '24px', lineHeight: 1, flexShrink: 0 }}>{getCountryFlag(selected.country)}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: '#111827', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{selected.name}</div>
                  <div style={{ fontSize: '11px', color: '#6b7280' }}>
                    {isFacebookEmptyView
                      ? ti('facebook.empty.subtitle', 'Facebook · 等待真实数据接入')
                      : `${selected.country} · ${selected.phone} · ${selected.channel}`}
                  </div>
                </div>
                <div style={{ padding: '3px 10px', borderRadius: '999px', background: isHot ? '#dcfce7' : '#f3f4f6', color: isHot ? '#166534' : '#374151', fontWeight: 700, fontSize: '11px', flexShrink: 0 }}>
                  {selected.category}
                </div>
                <div style={{ display: 'flex', gap: '6px', fontSize: '11px', color: '#9ca3af', flexShrink: 0, alignItems: 'center' }}>
                  <span>{proactiveCount} 条</span>
                  <span>·</span>
                  <span>{exchangeCount} 轮</span>
                  {selected.needs_human_review && <span style={{ color: '#ef4444', fontWeight: 700 }}>⚠ 待接管</span>}
                </div>
                <button
                  onClick={() => { setSendPanelOpen(v => !v); setSendStatus(null); setSendErrMsg('') }}
                  style={{ padding: '4px 10px', borderRadius: '7px', border: '1px solid #e5e7eb', background: sendPanelOpen ? '#eff6ff' : '#f9fafb', color: sendPanelOpen ? '#1d4ed8' : '#374151', fontSize: '11px', cursor: 'pointer', flexShrink: 0 }}
                >
                  {sendPanelOpen ? '收起' : '📨 测试发消息'}
                </button>
              </div>

              {/* Tags & Notes panel (collapsible, below header) */}
              {(() => {
                const phone = selected?.phone
                const meta = phone && phone !== '-' ? (customerMeta[phone] || { tags: [], notes: '' }) : null
                const activeTags = meta?.tags || []
                return (
                  <div style={{ background: '#fff', borderBottom: '1px solid #e5e7eb', flexShrink: 0 }}>
                    {/* Collapsed bar: show current tags + toggle button */}
                    <div style={{ padding: '6px 16px', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '11px', color: '#6b7280', flexShrink: 0 }}>🏷️</span>
                      {activeTags.length === 0 && (
                        <span style={{ fontSize: '11px', color: '#d1d5db' }}>暂无标签</span>
                      )}
                      {activeTags.map(tag => {
                        const preset = PRESET_TAGS.find(p => p.label === tag)
                        return (
                          <span key={tag} style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '999px', background: preset?.bg || '#f3f4f6', color: preset?.color || '#374151', border: `1px solid ${preset?.border || '#d1d5db'}`, fontWeight: 600 }}>
                            {tag}
                          </span>
                        )
                      })}
                      {meta?.notes && (
                        <span style={{ fontSize: '11px', color: '#6b7280', marginLeft: '4px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }}>
                          📝 {meta.notes}
                        </span>
                      )}
                      <button onClick={() => setMetaPanelOpen(v => !v)}
                        style={{ marginLeft: 'auto', fontSize: '10px', padding: '2px 8px', borderRadius: '6px', border: '1px solid #e5e7eb', background: metaPanelOpen ? '#eff6ff' : '#f9fafb', color: metaPanelOpen ? '#1d4ed8' : '#6b7280', cursor: 'pointer', flexShrink: 0 }}>
                        {metaPanelOpen ? '收起' : '编辑标签/备注'}
                      </button>
                    </div>

                    {/* Expanded editor */}
                    {metaPanelOpen && meta && (
                      <div style={{ padding: '10px 16px 12px', borderTop: '1px solid #f3f4f6', background: '#fafafa' }}>
                        {/* Biz type selector */}
                        <div style={{ marginBottom: '10px' }}>
                          <div style={{ fontSize: '11px', fontWeight: 600, color: '#374151', marginBottom: '6px' }}>业务分类</div>
                          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                            {BIZ_TYPES.map(bt => {
                              const active = (customerMeta[phone]?.bizType || '') === bt.key
                              return (
                                <button key={bt.key} onClick={() => saveBizType(phone, active ? '' : bt.key)}
                                  style={{ padding: '4px 10px', borderRadius: '999px', fontSize: '12px', cursor: 'pointer', fontWeight: active ? 700 : 400, border: `1px solid ${active ? bt.border : '#e5e7eb'}`, background: active ? bt.bg : '#fff', color: active ? bt.color : '#6b7280', transition: 'all 0.1s' }}
                                  title={bt.desc}>
                                  {active ? '✓ ' : ''}{bt.label}
                                </button>
                              )
                            })}
                          </div>
                        </div>

                        {/* Behavior Tag toggles */}
                        <div style={{ marginBottom: '10px' }}>
                          <div style={{ fontSize: '11px', fontWeight: 600, color: '#374151', marginBottom: '6px' }}>跟进标签</div>
                          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                            {PRESET_TAGS.map(t => {
                              const active = activeTags.includes(t.label)
                              return (
                                <button key={t.label} onClick={() => toggleTag(phone, t.label)}
                                  style={{ padding: '4px 10px', borderRadius: '999px', fontSize: '12px', cursor: 'pointer', fontWeight: active ? 700 : 400, border: `1px solid ${active ? t.border : '#e5e7eb'}`, background: active ? t.bg : '#fff', color: active ? t.color : '#6b7280', transition: 'all 0.1s' }}>
                                  {active ? '✓ ' : ''}{t.label}
                                </button>
                              )
                            })}
                          </div>
                        </div>

                        {/* Notes */}
                        <div>
                          <div style={{ fontSize: '11px', fontWeight: 600, color: '#374151', marginBottom: '5px' }}>备注</div>
                          <textarea
                            value={editingNotes}
                            onChange={e => setEditingNotes(e.target.value)}
                            placeholder="写下跟进备注、客户喜好、特殊要求..."
                            rows={2}
                            style={{ width: '100%', padding: '7px 9px', border: '1px solid #d1d5db', borderRadius: '7px', fontSize: '12px', lineHeight: 1.6, resize: 'none', boxSizing: 'border-box', background: '#fff' }}
                          />
                          <button onClick={() => saveNotes(phone, editingNotes)}
                            style={{ marginTop: '5px', padding: '5px 14px', borderRadius: '6px', border: 'none', background: '#2563eb', color: '#fff', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}>
                            保存备注
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })()}

              {/* Test send panel */}
              {sendPanelOpen && (
                <div style={{ background: '#fffbf0', borderBottom: '1px solid #fed7aa', padding: '10px 16px', flexShrink: 0 }}>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#92400e', marginBottom: '7px' }}>人工测试发消息（模拟客户来信）</div>
                  <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', gap: '6px', alignItems: 'end' }}>
                    <div>
                      <div style={{ fontSize: '10px', color: '#6b7280', marginBottom: '2px' }}>电话号码 *</div>
                      <input value={sendForm.phone} onChange={e => setSendForm(f => ({ ...f, phone: e.target.value }))} placeholder="+8613900000000"
                        style={{ width: '100%', padding: '5px 7px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                    <div>
                      <div style={{ fontSize: '10px', color: '#6b7280', marginBottom: '2px' }}>客户名</div>
                      <input value={sendForm.name} onChange={e => setSendForm(f => ({ ...f, name: e.target.value }))} placeholder="Ahmad"
                        style={{ width: '100%', padding: '5px 7px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                    <div>
                      <div style={{ fontSize: '10px', color: '#6b7280', marginBottom: '2px' }}>国家</div>
                      <input value={sendForm.country} onChange={e => setSendForm(f => ({ ...f, country: e.target.value }))} placeholder="阿联酋"
                        style={{ width: '100%', padding: '5px 7px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                    <div style={{ gridColumn: '1 / -1' }}>
                      <div style={{ fontSize: '10px', color: '#6b7280', marginBottom: '2px' }}>消息内容 *</div>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <input value={sendForm.message} onChange={e => setSendForm(f => ({ ...f, message: e.target.value }))} onKeyDown={e => { if (e.key === 'Enter') handleSendMessage() }}
                          placeholder="I need 10 SUVs for resale..."
                          style={{ flex: 1, padding: '5px 7px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '12px' }} />
                        <button onClick={handleSendMessage} disabled={sendStatus === 'sending'}
                          style={{ padding: '5px 14px', borderRadius: '6px', border: 'none', background: sendStatus === 'sending' ? '#93c5fd' : '#2563eb', color: '#fff', fontWeight: 700, fontSize: '12px', cursor: 'pointer', whiteSpace: 'nowrap' }}>
                          {sendStatus === 'sending' ? '发送中...' : '发送'}
                        </button>
                      </div>
                    </div>
                    {sendErrMsg && <div style={{ gridColumn: '1/-1', fontSize: '11px', color: '#dc2626', background: '#fef2f2', borderRadius: '5px', padding: '4px 8px' }}>⚠ {sendErrMsg}</div>}
                    {sendStatus === 'ok' && <div style={{ gridColumn: '1/-1', fontSize: '11px', color: '#16a34a', background: '#f0fdf4', borderRadius: '5px', padding: '4px 8px' }}>✓ 已写入，约 8 秒后刷新</div>}
                  </div>
                </div>
              )}

              {/* Chat bubbles area */}
              <div style={{ flex: 1, overflowY: 'auto', padding: isMobile ? '12px 10px' : '16px 24px', background: '#f8fafc', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                {isFacebookEmptyView ? (
                  <div style={{ textAlign: 'center', color: '#9ca3af', fontSize: '13px', paddingTop: '48px' }}>
                    <div style={{ fontSize: '36px', marginBottom: '10px' }}>💬</div>
                    <div>{ti('facebook.empty.reason', '请保持 Facebook webhook 在线，并等待真实聊天进入。')}</div>
                  </div>
                ) : selected.messages?.length ? (
                  selected.messages.map((msg, idx) => {
                    const isAgent = msg.role === '我方' || msg.role === 'agent'
                    const isArabic = /[؀-ۿ]/.test(msg.text || '')
                    return (
                      <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: isAgent ? 'flex-end' : 'flex-start', marginBottom: '8px' }}>
                        <div style={{ fontSize: '10px', color: '#9ca3af', marginBottom: '3px', paddingLeft: isAgent ? 0 : '4px', paddingRight: isAgent ? '4px' : 0 }}>
                          {msg.time}
                        </div>
                        <div style={{
                          maxWidth: isMobile ? '85%' : '68%',
                          padding: '9px 13px',
                          borderRadius: isAgent ? '18px 4px 18px 18px' : '4px 18px 18px 18px',
                          background: isAgent ? '#d9fdd3' : '#ffffff',
                          color: '#111827',
                          fontSize: '13px',
                          lineHeight: 1.65,
                          boxShadow: '0 1px 2px rgba(0,0,0,0.06)',
                          direction: isArabic ? 'rtl' : 'ltr',
                          textAlign: isArabic ? 'right' : 'left',
                          fontFamily: "'Noto Sans Arabic', 'PingFang SC', sans-serif",
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                        }}>
                          {msg.text}
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <div style={{ textAlign: 'center', color: '#9ca3af', fontSize: '13px', paddingTop: '48px' }}>暂无聊天内容</div>
                )}
              </div>

              {/* AI Reply panel (bottom) */}
              <div style={{ background: '#fff', borderTop: '1px solid #e5e7eb', padding: '10px 16px', flexShrink: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: '#1d4ed8' }}>AI 建议回复</span>
                    {aiSource && (
                      <span style={{
                        fontSize: '10px', padding: '2px 7px', borderRadius: '999px', fontWeight: 600,
                        background: aiSource === 'gemini' ? '#f0fdf4' : aiSource === 'claude' ? '#eff6ff' : '#fef9c3',
                        color: aiSource === 'gemini' ? '#16a34a' : aiSource === 'claude' ? '#2563eb' : '#92400e',
                        border: aiSource === 'gemini' ? '1px solid #bbf7d0' : aiSource === 'claude' ? '1px solid #bfdbfe' : '1px solid #fde68a',
                      }}>
                        {aiSource === 'gemini' ? '✦ Gemini 2.5 Flash' : aiSource === 'claude' ? '◆ Claude' : '≈ 规则模板'}
                        {aiExpCount > 0 && ` · ${aiExpCount}条经验`}
                      </span>
                    )}
                    {aiReplyLoading && <span style={{ fontSize: '11px', color: '#6b7280' }}>⏳ 正在生成...</span>}
                  </div>
                  <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                    {aiReplyEnabled && (
                      <button onClick={() => setAiAutoSend(v => !v)}
                        style={{ padding: '3px 9px', borderRadius: '999px', fontSize: '10px', fontWeight: 700, cursor: 'pointer', border: aiAutoSend ? '1px solid #dc2626' : '1px solid #d1d5db', background: aiAutoSend ? '#fef2f2' : '#f9fafb', color: aiAutoSend ? '#dc2626' : '#6b7280' }}>
                        {aiAutoSend ? '⚡ AI自动发（高风险）' : '○ 人工审核'}
                      </button>
                    )}
                    <button onClick={() => { setAiReplyEnabled(v => !v); setAiReplyText(''); setAiReplyStatus(null) }}
                      style={{ padding: '3px 9px', borderRadius: '999px', fontSize: '11px', fontWeight: 700, cursor: 'pointer', border: aiReplyEnabled ? '1px solid #2563eb' : '1px solid #d1d5db', background: aiReplyEnabled ? '#eff6ff' : '#f9fafb', color: aiReplyEnabled ? '#1d4ed8' : '#6b7280' }}>
                      {aiReplyEnabled ? '● AI 已开' : '○ AI 已关'}
                    </button>
                  </div>
                </div>

                {aiReplyEnabled && (
                  <>
                    <div style={{ display: 'flex', gap: '6px', marginBottom: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                      <button onClick={handleFetchAiReply} disabled={aiReplyLoading || isFacebookEmptyView || !selected.messages?.length}
                        style={{ padding: '5px 12px', borderRadius: '7px', fontSize: '11px', fontWeight: 700, cursor: 'pointer', border: 'none', background: '#2563eb', color: '#fff', opacity: (aiReplyLoading || isFacebookEmptyView || !selected.messages?.length) ? 0.5 : 1 }}>
                        {aiReplyLoading ? '⏳ 生成中...' : '🤖 重新生成'}
                      </button>
                      {aiReplyText && (
                        <button onClick={() => { setAiReplyText(''); setAiReplyStatus(null) }}
                          style={{ padding: '5px 10px', borderRadius: '7px', fontSize: '11px', cursor: 'pointer', border: '1px solid #e5e7eb', background: '#fff', color: '#6b7280' }}>
                          清空
                        </button>
                      )}
                      {!aiReplyText && !aiReplyLoading && (
                        <span style={{ fontSize: '11px', color: '#9ca3af' }}>切换客户时自动生成 · Gemini 2.5 Flash 驱动</span>
                      )}
                    </div>

                    {aiReplyText && (
                      <>
                        <textarea value={aiReplyText} onChange={e => setAiReplyText(e.target.value)} rows={3}
                          style={{ width: '100%', padding: '8px 10px', border: '1px solid #bfdbfe', borderRadius: '8px', fontSize: '13px', lineHeight: 1.6, background: '#f8fbff', boxSizing: 'border-box', resize: 'vertical', fontFamily: "'Noto Sans Arabic', 'PingFang SC', sans-serif" }} />
                        <div style={{ display: 'flex', gap: '6px', marginTop: '7px', flexWrap: 'wrap', alignItems: 'center' }}>
                          <button onClick={handleApproveAiReply} disabled={aiReplyStatus === 'sending'}
                            style={{ padding: '6px 14px', borderRadius: '7px', fontSize: '12px', fontWeight: 700, cursor: 'pointer', border: 'none', background: '#16a34a', color: '#fff', opacity: aiReplyStatus === 'sending' ? 0.6 : 1 }}>
                            {aiReplyStatus === 'sending' ? '发送中...' : '✓ 采纳并发送'}
                          </button>
                          <button onClick={handleIgnoreAiReply}
                            style={{ padding: '6px 10px', borderRadius: '7px', fontSize: '12px', cursor: 'pointer', border: '1px solid #e5e7eb', background: '#fff', color: '#6b7280' }}>
                            忽略
                          </button>
                          {aiAutoSend && <span style={{ fontSize: '10px', color: '#dc2626' }}>⚠ AI自动发已开启</span>}
                          {aiReplyStatus === 'sent' && <span style={{ fontSize: '11px', color: '#16a34a', background: '#f0fdf4', borderRadius: '5px', padding: '3px 8px' }}>✓ 已发送</span>}
                          {aiReplyStatus === 'err' && <span style={{ fontSize: '11px', color: '#dc2626', background: '#fef2f2', borderRadius: '5px', padding: '3px 8px' }}>⚠ 发送失败</span>}
                        </div>
                      </>
                    )}
                  </>
                )}
              </div>
            </>
          )}
        </div>
      )}

    </div>
  )
}
// ─────────────────────────────────────────────────────────────
// ReactivationPanel — 历史客户重新激活
// ─────────────────────────────────────────────────────────────
function ReactivationPanel({
  uploadStatus, setUploadStatus,
  uploadError, setUploadError,
  results, setResults,
  myName, setMyName,
  selectedId, setSelectedId,
  progress, setProgress,
}) {
  const isMobile = useIsMobile()
  const [mobileView, setMobileView] = useState('list')
  const fileInputRef = useRef(null)
  const selected = results.find(r => r.id === selectedId) || results[0] || null
  const [editingMsg, setEditingMsg] = useState('')
  const [sendStatus, setSendStatus] = useState(null) // null | 'sending' | 'sent' | 'err'

  // 同步编辑框到选中项
  useEffect(() => {
    if (selected) setEditingMsg(selected.reactivation_message || '')
    setSendStatus(null)
  }, [selectedId, selected?.id])

  // 加载已保存的结果
  useEffect(() => {
    fetch('/api/reactivation/list')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.results?.length) setResults(data.results) })
      .catch(() => {})
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleFileUpload(e) {
    const files = Array.from(e.target.files || [])
    if (!files.length) return

    setUploadStatus('parsing')
    setUploadError('')
    setProgress({ current: 0, total: files.length })

    // 读取所有文件内容
    const fileObjects = await Promise.all(files.map(f => new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = (ev) => resolve({
        filename: f.name,
        content: ev.target.result,
        phone: '',
      })
      reader.readAsText(f, 'utf-8')
    })))

    setUploadStatus('analyzing')
    setProgress({ current: 0, total: files.length })

    try {
      const resp = await fetch('/api/reactivation/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ files: fileObjects, my_name_hint: myName }),
      })
      const data = await resp.json()
      if (data.success) {
        setResults(prev => {
          const existingIds = new Set(prev.map(r => r.id))
          const fresh = (data.results || []).filter(r => !existingIds.has(r.id))
          return [...fresh, ...prev]
        })
        setUploadStatus('done')
        setProgress({ current: data.analyzed, total: data.total })
        if (data.results?.[0]) setSelectedId(data.results[0].id)
        if (data.errors?.length) {
          setUploadError(`成功 ${data.analyzed} 个，失败 ${data.errors.length} 个：${data.errors.map(e => e.filename).join(', ')}`)
        }
      } else {
        setUploadStatus('error')
        setUploadError(data.error || '分析失败')
      }
    } catch (err) {
      setUploadStatus('error')
      setUploadError(`请求失败：${err.message}`)
    }

    // 重置 input 以允许重复上传同一文件
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  async function handleUpdateStatus(id, status) {
    await fetch('/api/reactivation/update_status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, status }),
    })
    setResults(prev => prev.map(r => r.id === id ? { ...r, status } : r))
  }

  const pendingCount = results.filter(r => r.status === 'pending').length
  const sentCount = results.filter(r => r.status === 'sent').length

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* 顶部：上传区 + 统计 */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr auto', gap: '12px', alignItems: 'start' }}>
        {/* 上传卡片 */}
        <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e5e7eb', padding: '16px' }}>
          <div style={{ fontSize: '15px', fontWeight: 800, marginBottom: '10px' }}>
            📂 上传 WhatsApp 聊天记录（.txt）
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            <input
              type="text"
              placeholder="我方账号名称（可选，帮助区分客户/我方）"
              value={myName}
              onChange={e => setMyName(e.target.value)}
              style={{ flex: 1, minWidth: '200px', padding: '7px 10px', borderRadius: '8px', border: '1px solid #d1d5db', fontSize: '13px' }}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadStatus === 'analyzing'}
              style={{
                padding: '7px 16px', borderRadius: '8px', border: 'none',
                background: uploadStatus === 'analyzing' ? '#93c5fd' : '#2563eb',
                color: '#fff', fontWeight: 700, cursor: uploadStatus === 'analyzing' ? 'not-allowed' : 'pointer',
                fontSize: '13px',
              }}
            >
              {uploadStatus === 'analyzing' ? '⏳ Gemini 分析中...' : '选择文件'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt"
              multiple
              style={{ display: 'none' }}
              onChange={handleFileUpload}
            />
          </div>
          {/* 状态提示 */}
          {uploadStatus === 'done' && progress.total > 0 && (
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#16a34a' }}>
              ✓ 分析完成：{progress.current}/{progress.total} 个文件
            </div>
          )}
          {uploadStatus === 'analyzing' && (
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#2563eb' }}>
              ⏳ 正在调用 Gemini 2.5 Flash 逐一分析，请稍候...
            </div>
          )}
          {uploadError && (
            <div style={{ marginTop: '8px', fontSize: '12px', color: uploadStatus === 'error' ? '#dc2626' : '#d97706' }}>
              {uploadStatus === 'error' ? '⚠ ' : 'ℹ '}{uploadError}
            </div>
          )}
          <div style={{ marginTop: '8px', fontSize: '11px', color: '#9ca3af' }}>
            支持批量上传 · 每个 .txt 对应一段对话 · 数据仅存储在本地服务器
          </div>
        </div>
        {/* 统计 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '120px' }}>
          <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '12px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#6b7280' }}>待发送</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: '#2563eb' }}>{pendingCount}</div>
          </div>
          <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '12px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#6b7280' }}>已发送</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: '#16a34a' }}>{sentCount}</div>
          </div>
          <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '12px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#6b7280' }}>总计</div>
            <div style={{ fontSize: '28px', fontWeight: 800 }}>{results.length}</div>
          </div>
        </div>
      </div>

      {/* 空状态 */}
      {results.length === 0 && (
        <div style={{ background: '#fff', borderRadius: '12px', border: '1px dashed #d1d5db', padding: '48px', textAlign: 'center', color: '#9ca3af' }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>📋</div>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '4px' }}>暂无分析结果</div>
          <div style={{ fontSize: '12px' }}>上传 WhatsApp 导出的 .txt 聊天记录，Gemini 将自动提取客户画像并生成个性化重新激活消息</div>
        </div>
      )}

      {/* 主面板：列表 + 详情 */}
      {results.length > 0 && (
        <div style={{ display: isMobile ? 'block' : 'grid', gridTemplateColumns: '340px 1fr', gap: '12px' }}>
          {/* 左侧列表 */}
          <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e5e7eb', padding: '10px', display: isMobile && mobileView === 'detail' ? 'none' : 'block' }}>
            <div style={{ fontSize: '14px', fontWeight: 800, marginBottom: '8px' }}>客户列表</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: isMobile ? 'calc(100vh - 260px)' : '65vh', overflowY: 'auto' }}>
              {results.map(r => {
                const ic = INTENT_COLORS[r.intent_level] || INTENT_COLORS.unknown
                const active = r.id === selectedId
                return (
                  <div
                    key={r.id}
                    onClick={() => { setSelectedId(r.id); if (isMobile) { setMobileView('detail'); window.scrollTo(0, 0) } }}
                    style={{
                      border: active ? `1px solid ${ic.border}` : '1px solid #e5e7eb',
                      background: active ? ic.bg : '#fff',
                      borderRadius: '10px', padding: '10px', cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0 }}>
                        {r.phone && (
                          <span style={{ fontSize: '11px', color: '#6b7280', background: '#f3f4f6', borderRadius: '6px', padding: '2px 6px', whiteSpace: 'nowrap', fontFamily: 'monospace' }}>
                            {r.phone}
                          </span>
                        )}
                        <div style={{ fontWeight: 800, fontSize: '14px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.customer_name || r.filename}</div>
                      </div>
                      <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '999px', background: ic.badge, color: '#fff', fontWeight: 700, flexShrink: 0 }}>
                        {ic.label}
                      </span>
                    </div>
                    <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>
                      {r.country || '国家未知'} · {(r.car_models_interested || []).join(', ') || '车型未知'}
                    </div>
                    <div style={{ fontSize: '11px', color: '#374151' }}>{r.no_deal_reason || '—'}</div>
                    <div style={{ marginTop: '6px', display: 'flex', gap: '4px' }}>
                      <span style={{
                        fontSize: '10px', padding: '2px 6px', borderRadius: '999px',
                        background: r.status === 'sent' ? '#dcfce7' : r.status === 'skipped' ? '#f3f4f6' : '#dbeafe',
                        color: r.status === 'sent' ? '#16a34a' : r.status === 'skipped' ? '#6b7280' : '#1d4ed8',
                        fontWeight: 600,
                      }}>
                        {r.status === 'sent' ? '✓ 已发送' : r.status === 'skipped' ? '— 跳过' : '待发送'}
                      </span>
                      <span style={{ fontSize: '10px', color: '#9ca3af' }}>{r.message_count} 条消息</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* 右侧详情 */}
          {selected ? (
            <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e5e7eb', padding: '16px', display: isMobile && mobileView === 'list' ? 'none' : 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* 手机端返回按钮 */}
              {isMobile && mobileView === 'detail' && (
                <button onClick={() => { setMobileView('list'); window.scrollTo(0, 0) }} style={{ alignSelf: 'flex-start', padding: '10px 16px', borderRadius: '8px', border: '1px solid #d1d5db', background: '#f3f4f6', fontSize: '14px', cursor: 'pointer', fontWeight: 600, minHeight: '40px' }}>
                  ← 返回列表
                </button>
              )}
              {/* 客户信息头部 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', flexWrap: 'wrap', gap: '8px' }}>
                <div>
                  <div style={{ fontSize: '20px', fontWeight: 800 }}>{selected.customer_name}</div>
                  <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '2px' }}>
                    {selected.country || '国家未知'} · {selected.phone || '电话未知'} · {selected.message_count} 条消息
                  </div>
                </div>
                <span style={{
                  fontSize: '12px', padding: '4px 10px', borderRadius: '999px',
                  background: (INTENT_COLORS[selected.intent_level] || INTENT_COLORS.unknown).badge,
                  color: '#fff', fontWeight: 700,
                }}>
                  {(INTENT_COLORS[selected.intent_level] || INTENT_COLORS.unknown).label}
                </span>
              </div>

              {/* 分析结果 */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div style={{ background: '#f9fafb', borderRadius: '10px', padding: '12px' }}>
                  <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px', fontWeight: 600 }}>询问车型</div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>
                    {(selected.car_models_interested || []).join(' · ') || '—'}
                  </div>
                </div>
                <div style={{ background: '#f9fafb', borderRadius: '10px', padding: '12px' }}>
                  <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px', fontWeight: 600 }}>未成交原因</div>
                  <div style={{ fontSize: '13px' }}>{selected.no_deal_reason || '—'}</div>
                </div>
                <div style={{ background: '#f9fafb', borderRadius: '10px', padding: '12px' }}>
                  <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px', fontWeight: 600 }}>意向判断</div>
                  <div style={{ fontSize: '13px' }}>{selected.intent_reason || '—'}</div>
                </div>
                <div style={{ background: '#f9fafb', borderRadius: '10px', padding: '12px' }}>
                  <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px', fontWeight: 600 }}>最后沟通摘要</div>
                  <div style={{ fontSize: '13px' }}>{selected.last_contact_summary || '—'}</div>
                </div>
              </div>

              {/* 重新激活消息编辑区 */}
              <div style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '12px' }}>
                <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: '8px', color: '#1d4ed8' }}>
                  ✉ 个性化重新激活消息（英文）
                </div>
                <textarea
                  value={editingMsg}
                  onChange={e => setEditingMsg(e.target.value)}
                  rows={5}
                  style={{
                    width: '100%', padding: '8px', borderRadius: '8px',
                    border: '1px solid #d1d5db', fontSize: '13px',
                    fontFamily: 'inherit', resize: 'vertical', boxSizing: 'border-box',
                  }}
                />
                <div style={{ display: 'flex', gap: '8px', marginTop: '8px', alignItems: 'center' }}>
                  <button
                    onClick={() => {
                      setSendStatus('sending')
                      handleUpdateStatus(selected.id, 'confirmed')
                        .then(() => {
                          setSendStatus('sent')
                          handleUpdateStatus(selected.id, 'sent')
                        })
                        .catch(() => setSendStatus('err'))
                    }}
                    disabled={selected.status === 'sent' || sendStatus === 'sending'}
                    style={{
                      padding: '7px 16px', borderRadius: '8px', border: 'none',
                      background: selected.status === 'sent' ? '#6b7280' : '#16a34a',
                      color: '#fff', fontWeight: 700, cursor: selected.status === 'sent' ? 'not-allowed' : 'pointer',
                      fontSize: '13px',
                    }}
                  >
                    {sendStatus === 'sending' ? '处理中...' : selected.status === 'sent' ? '✓ 已标记发送' : '✓ 确认发送'}
                  </button>
                  <button
                    onClick={() => handleUpdateStatus(selected.id, 'skipped')}
                    style={{ padding: '7px 12px', borderRadius: '8px', border: '1px solid #d1d5db', background: '#fff', color: '#6b7280', fontWeight: 600, cursor: 'pointer', fontSize: '13px' }}
                  >
                    跳过
                  </button>
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginLeft: 'auto' }}>
                    分析于 {selected.analyzed_at} · 来源文件：{selected.filename}
                  </div>
                </div>
                {sendStatus === 'sent' && (
                  <div style={{ marginTop: '6px', fontSize: '12px', color: '#16a34a' }}>
                    ✓ 已标记为发送。客户回复后将进入卧龙正常跟进流程。
                  </div>
                )}
                {sendStatus === 'err' && (
                  <div style={{ marginTop: '6px', fontSize: '12px', color: '#dc2626' }}>⚠ 更新失败，请检查后端服务。</div>
                )}
              </div>

              {/* 历史沟通记录 */}
              {selected.messages?.length > 0 && (
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: '8px' }}>
                    📜 历史沟通记录（{selected.messages.length} 条）
                  </div>
                  <div style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px', maxHeight: '320px', overflowY: 'auto', background: '#fafafa', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {selected.messages.map((msg, idx) => {
                      const isAgent = msg.role === '我方' || msg.role === 'agent'
                      return (
                        <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: isAgent ? 'flex-end' : 'flex-start' }}>
                          <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '2px' }}>
                            {msg.role} · {msg.time}
                          </div>
                          <div style={{
                            fontSize: '13px', lineHeight: 1.6,
                            padding: '7px 12px',
                            borderRadius: isAgent ? '14px 4px 14px 14px' : '4px 14px 14px 14px',
                            maxWidth: '85%',
                            background: isAgent ? '#dcfce7' : '#dbeafe',
                            color: isAgent ? '#14532d' : '#1e3a5f',
                            border: isAgent ? '1px solid #86efac' : '1px solid #93c5fd',
                            fontFamily: "'Noto Sans Arabic', 'PingFang SC', sans-serif",
                            direction: /[\u0600-\u06FF]/.test(msg.text || '') ? 'rtl' : 'ltr',
                            textAlign: /[\u0600-\u06FF]/.test(msg.text || '') ? 'right' : 'left',
                            whiteSpace: 'pre-wrap',
                          }}>
                            {msg.text}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* 操作提示 */}
              <div style={{ fontSize: '11px', color: '#9ca3af', background: '#f9fafb', borderRadius: '8px', padding: '8px 12px' }}>
                💡 确认后请手动将消息复制到 WhatsApp 发送，或等待第3步（WhatsApp API自动发送）功能上线。客户回复后，通过 WhatsApp Webhook 自动进入卧龙跟进流程。
              </div>
            </div>
          ) : (
            <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e5e7eb', padding: '32px', textAlign: 'center', color: '#9ca3af' }}>
              ← 从左侧选择一个客户查看详情
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// AllCustomersPanel — 全部客户总表（WhatsApp + Facebook + 历史激活）
// ─────────────────────────────────────────────────────────────
const SOURCE_STYLE = {
  'WhatsApp':  { bg: '#dcfce7', color: '#166534', border: '#86efac' },
  'Facebook':  { bg: '#dbeafe', color: '#1e40af', border: '#93c5fd' },
  '历史激活':  { bg: '#fef3c7', color: '#92400e', border: '#fde68a' },
}

function AllCustomersPanel({ customers, selectedId, setSelectedId, loading }) {
  const isMobile = useIsMobile()
  const [mobileView, setMobileView] = useState('list') // 'list' | 'detail'
  const selected = customers.find(c => c.id === selectedId) || customers[0] || null
  const [showCN, setShowCN] = useState(false)
  const [translations, setTranslations] = useState({}) // { customerId: ['cn1','cn2',...] }
  const [translating, setTranslating] = useState(false)
  const [sendStatus, setSendStatus] = useState({}) // { customerId: 'sending'|'sent'|'error' }

  async function fetchTranslations(cust) {
    if (!cust?.messages?.length) return
    if (translations[cust.id]) { setShowCN(true); return }
    setTranslating(true)
    try {
      const texts = cust.messages.map(m => m.text || '')
      const res = await fetch('/api/translate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texts }),
      })
      const data = await res.json()
      if (data.translations) {
        setTranslations(prev => ({ ...prev, [cust.id]: data.translations }))
        setShowCN(true)
      }
    } catch (e) { console.error('translate error', e) }
    setTranslating(false)
  }

  return (
    <div style={{ display: isMobile ? 'block' : 'grid', gridTemplateColumns: '380px 1fr', gap: '12px' }}>
      {/* 左侧列表 */}
      <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e5e7eb', padding: '10px', display: isMobile && mobileView === 'detail' ? 'none' : 'block' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <div style={{ fontSize: '14px', fontWeight: 800 }}>全部客户</div>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>
            {loading ? '加载中...' : `共 ${customers.length} 位`}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: isMobile ? 'calc(100vh - 240px)' : '72vh', overflowY: 'auto' }}>
          {customers.length === 0 && (
            <div style={{ fontSize: '12px', color: '#9ca3af', textAlign: 'center', padding: '24px' }}>
              {loading ? '正在加载...' : '暂无客户数据'}
            </div>
          )}
          {customers.map(c => {
            const ss = SOURCE_STYLE[c._source] || SOURCE_STYLE['WhatsApp']
            const active = c.id === selectedId
            return (
              <div
                key={c.id}
                onClick={() => { setSelectedId(c.id); if (isMobile) { setMobileView('detail'); window.scrollTo(0, 0) } }}
                style={{
                  border: active ? '1px solid #2563eb' : '1px solid #e5e7eb',
                  background: active ? '#eff6ff' : '#fff',
                  borderRadius: '10px', padding: '10px', cursor: 'pointer',
                }}
              >
                {/* 第一行：手机号 + 姓名 + 来源标签 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '3px', flexWrap: 'wrap' }}>
                  {c.phone && c.phone !== '-' && (
                    <span style={{ fontSize: '11px', color: '#6b7280', background: '#f3f4f6', borderRadius: '6px', padding: '1px 5px', fontFamily: 'monospace', whiteSpace: 'nowrap', flexShrink: 0 }}>
                      {c.phone}
                    </span>
                  )}
                  <span style={{ fontWeight: 800, fontSize: '13px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '120px' }}>
                    {c.name}
                  </span>
                  <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px', background: ss.bg, color: ss.color, border: `1px solid ${ss.border}`, fontWeight: 700, whiteSpace: 'nowrap', flexShrink: 0 }}>
                    {c._source}
                  </span>
                </div>
                {/* 第二行：国家 + 摘要 */}
                <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '2px' }}>
                  {c.country || '国家未知'}{c.time ? ` · ${c.time}` : ''}
                </div>
                <div style={{ fontSize: '11px', color: '#374151', overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                  {c.message || '—'}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* 右侧详情 */}
      {selected ? (
        <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e5e7eb', padding: '16px', display: isMobile && mobileView === 'list' ? 'none' : 'flex', flexDirection: 'column', gap: '14px', overflowY: 'auto', maxHeight: isMobile ? 'calc(100vh - 60px)' : '80vh' }}>
          {/* 手机端返回按钮 */}
          {isMobile && mobileView === 'detail' && (
            <button onClick={() => { setMobileView('list'); window.scrollTo(0, 0) }} style={{ alignSelf: 'flex-start', padding: '10px 16px', borderRadius: '8px', border: '1px solid #d1d5db', background: '#f3f4f6', fontSize: '14px', cursor: 'pointer', fontWeight: 600, minHeight: '40px' }}>
              ← 返回列表
            </button>
          )}
          {/* 头部 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', flexWrap: 'wrap', gap: '8px' }}>
            <div>
              <div style={{ fontSize: '20px', fontWeight: 800 }}>{selected.name}</div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '3px' }}>
                {selected.country || '国家未知'} · {selected.phone && selected.phone !== '-' ? selected.phone : '电话未知'} · {selected.time || '—'}
              </div>
            </div>
            <span style={{
              fontSize: '12px', padding: '4px 10px', borderRadius: '999px', fontWeight: 700,
              background: (SOURCE_STYLE[selected._source] || SOURCE_STYLE['WhatsApp']).bg,
              color: (SOURCE_STYLE[selected._source] || SOURCE_STYLE['WhatsApp']).color,
              border: `1px solid ${(SOURCE_STYLE[selected._source] || SOURCE_STYLE['WhatsApp']).border}`,
            }}>
              来源：{selected._source}
            </span>
          </div>

          {/* 关键词 / 车型 */}
          {(selected.keywords?.length > 0) && (
            <div>
              <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: '6px' }}>关键词 / 车型</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {selected.keywords.map((kw, i) => (
                  <span key={i} style={{ fontSize: '12px', padding: '3px 8px', borderRadius: '999px', background: '#eef2ff', color: '#3730a3' }}>{kw}</span>
                ))}
              </div>
            </div>
          )}

          {/* 历史激活特有字段 */}
          {selected._source === '历史激活' && selected._react && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div style={{ background: '#f9fafb', borderRadius: '10px', padding: '10px' }}>
                <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px', fontWeight: 600 }}>意向等级</div>
                <div style={{ fontSize: '13px', fontWeight: 700 }}>
                  {(INTENT_COLORS[selected._react.intent_level] || INTENT_COLORS.unknown).label}
                </div>
              </div>
              <div style={{ background: '#f9fafb', borderRadius: '10px', padding: '10px' }}>
                <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px', fontWeight: 600 }}>未成交原因</div>
                <div style={{ fontSize: '12px' }}>{selected._react.no_deal_reason || '—'}</div>
              </div>
              {selected._react.reactivation_message && (
                <div style={{ gridColumn: '1 / -1', background: '#fffbeb', borderRadius: '10px', padding: '10px', border: '1px solid #fde68a' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <div style={{ fontSize: '11px', color: '#92400e', fontWeight: 600 }}>✉ 重新激活消息</div>
                    {selected.phone && selected.phone !== '-' && (() => {
                      const st = sendStatus[selected.id]
                      return (
                        <button
                          disabled={st === 'sending' || st === 'sent'}
                          onClick={async () => {
                            setSendStatus(p => ({ ...p, [selected.id]: 'sending' }))
                            try {
                              const res = await fetch('/api/send_message', {
                                method: 'POST', headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                  phone: selected.phone,
                                  name: selected.name,
                                  message: selected._react.reactivation_message,
                                  role: 'agent',
                                }),
                              })
                              const d = await res.json()
                              setSendStatus(p => ({ ...p, [selected.id]: d.success ? 'sent' : 'error' }))
                            } catch {
                              setSendStatus(p => ({ ...p, [selected.id]: 'error' }))
                            }
                          }}
                          style={{
                            fontSize: '11px', padding: '4px 10px', borderRadius: '999px', border: 'none', cursor: st === 'sent' ? 'default' : 'pointer', fontWeight: 700,
                            background: st === 'sent' ? '#dcfce7' : st === 'error' ? '#fee2e2' : st === 'sending' ? '#e5e7eb' : '#25d366',
                            color: st === 'sent' ? '#166534' : st === 'error' ? '#991b1b' : st === 'sending' ? '#6b7280' : '#fff',
                          }}
                        >
                          {st === 'sending' ? '发送中...' : st === 'sent' ? '✓ 已发送' : st === 'error' ? '✗ 发送失败' : '📱 发送到WhatsApp'}
                        </button>
                      )
                    })()}
                  </div>
                  <div style={{ fontSize: '12px', lineHeight: 1.6 }}>{selected._react.reactivation_message}</div>
                </div>
              )}
            </div>
          )}

          {/* 摘要 */}
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: '6px' }}>沟通摘要</div>
            <div style={{ fontSize: '13px', lineHeight: 1.7, color: '#374151', background: '#f9fafb', borderRadius: '8px', padding: '10px' }}>
              {selected.message || selected.reason || '—'}
            </div>
          </div>

          {/* 历史聊天记录 */}
          {selected.messages?.length > 0 && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div style={{ fontSize: '13px', fontWeight: 700 }}>
                  📜 历史沟通记录（{selected.messages.length} 条）
                </div>
                <button
                  onClick={() => {
                    if (!showCN) fetchTranslations(selected)
                    else setShowCN(false)
                  }}
                  style={{
                    fontSize: '11px', padding: '3px 10px', borderRadius: '999px', border: '1px solid #d1d5db',
                    background: showCN ? '#eef2ff' : '#f9fafb', color: showCN ? '#3730a3' : '#6b7280',
                    cursor: 'pointer', fontWeight: 600,
                  }}
                >
                  {translating ? '⏳ 翻译中...' : showCN ? '🔠 隐藏中文' : '🔠 显示中文'}
                </button>
              </div>
              <div style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px', maxHeight: '380px', overflowY: 'auto', background: '#fafafa', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {selected.messages.map((msg, idx) => {
                  const isAgent = msg.role === '我方' || msg.role === 'agent'
                  const cnText = showCN && translations[selected.id]?.[idx]
                  return (
                    <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: isAgent ? 'flex-end' : 'flex-start' }}>
                      <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '2px' }}>
                        {msg.role} · {msg.time}
                      </div>
                      <div style={{
                        fontSize: '13px', lineHeight: 1.6,
                        padding: '7px 12px',
                        borderRadius: isAgent ? '14px 4px 14px 14px' : '4px 14px 14px 14px',
                        maxWidth: '85%',
                        background: isAgent ? '#dcfce7' : '#dbeafe',
                        color: isAgent ? '#14532d' : '#1e3a5f',
                        border: isAgent ? '1px solid #86efac' : '1px solid #93c5fd',
                        fontFamily: "'Noto Sans Arabic', 'PingFang SC', sans-serif",
                        direction: /[\u0600-\u06FF]/.test(msg.text || '') ? 'rtl' : 'ltr',
                        textAlign: /[\u0600-\u06FF]/.test(msg.text || '') ? 'right' : 'left',
                        whiteSpace: 'pre-wrap',
                      }}>
                        {msg.text}
                        {cnText && (
                          <div style={{
                            marginTop: '5px', paddingTop: '5px',
                            borderTop: isAgent ? '1px solid #86efac' : '1px solid #93c5fd',
                            fontSize: '12px', color: isAgent ? '#166534' : '#1e40af',
                            fontFamily: "'PingFang SC', sans-serif",
                            direction: 'ltr', textAlign: 'left',
                          }}>
                            🇨🇳 {cnText}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e5e7eb', padding: '32px', textAlign: 'center', color: '#9ca3af' }}>
          ← 从左侧选择一个客户查看详情
        </div>
      )}
    </div>
  )
}
