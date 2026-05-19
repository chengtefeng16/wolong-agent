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

// ── 历史激活：意向等级颜色配置 ──
const INTENT_COLORS = {
  hot:     { bg: '#fef2f2', border: '#ef4444', badge: '#dc2626', label: '🔥 高意向' },
  warm:    { bg: '#fffbeb', border: '#f59e0b', badge: '#d97706', label: '🟡 中意向' },
  cold:    { bg: '#eff6ff', border: '#93c5fd', badge: '#2563eb', label: '🧊 低意向' },
  unknown: { bg: '#f9fafb', border: '#d1d5db', badge: '#6b7280', label: '❓ 未知' },
}

export default function App() {
  const isMobile = useIsMobile()
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
        const exists = runtimeResult.customers?.some((item) => item?.id === prev)
        return exists ? prev : (runtimeResult.customers?.[0]?.id || '')
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
  const selected = customers.find((x) => x.id === selectedId) || customers[0] || channelEmptyState || fallbackCustomers[0]
  const isHot = selected.category === '准车商'
  const { proactiveCount, exchangeCount } = useMemo(() => getCounts(selected.messages), [selected])

  const emergencyStop = () => {
    window.alert('当前按钮只做展示。真实止水动作请走 AgentOS 后端治理配置链。')
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
    <div className="page">
      <div className="top-title">卧龙代理聊天实战工作台</div>

      {newCustomerCount > 0 && (
        <div style={{ marginBottom: '10px' }}>
          <div style={{
            background: '#eff6ff',
            border: '1px solid #bfdbfe',
            borderRadius: '12px',
            padding: '10px 12px',
            color: '#1d4ed8',
            fontWeight: 800
          }}>
            新客户提醒：检测到 {newCustomerCount} 条新增客户/互动，网页标签已闪动提醒。
          </div>
        </div>
      )}

      {showAlerts && alerts.length > 0 && (
        <div style={{ marginBottom: '10px' }}>
          <div style={{ background: '#ffffff', border: '1px solid #ef4444', borderRadius: '12px', padding: isMobile ? '8px 10px' : '10px 12px', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <div style={{ fontSize: isMobile ? '14px' : '15px', fontWeight: 800, color: '#b91c1c' }}>
                预警中心（{alerts.length}）
              </div>
              <button
                onClick={() => setShowAlerts(false)}
                style={{ border: '1px solid #d1d5db', background: '#fff', borderRadius: '8px', padding: isMobile ? '6px 14px' : '4px 10px', cursor: 'pointer', fontSize: '13px', minHeight: '36px' }}
              >
                收起
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {alerts.slice(0, 5).map((alert, idx) => {
                const style = getAlertLevelStyle(alert.level)
                return (
                  <div
                    key={`${alert.type}_${alert.customer_id || idx}`}
                    style={{ border: `1px solid ${style.border}`, background: style.bg, borderRadius: '10px', padding: '10px' }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', marginBottom: '4px' }}>
                      <div style={{ fontSize: '13px', fontWeight: 800, color: style.text }}>
                        {alert.title}
                      </div>
                      <div style={{ fontSize: '11px', color: '#6b7280' }}>
                        {alert.created_at || '—'}
                      </div>
                    </div>
                    <div style={{ fontSize: '13px', color: '#111827', lineHeight: 1.6 }}>
                      {alert.message}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {!showAlerts && alerts.length > 0 && (
        <div style={{ marginBottom: '10px' }}>
          <button
            onClick={() => setShowAlerts(true)}
            style={{
              width: isMobile ? '100%' : 'auto',
              border: '1px solid #ef4444',
              background: '#fff1f2',
              color: '#b91c1c',
              borderRadius: '10px',
              padding: isMobile ? '12px 16px' : '8px 12px',
              fontWeight: 700,
              cursor: 'pointer',
              fontSize: isMobile ? '14px' : '13px',
              textAlign: 'left',
            }}
          >
            🚨 展开预警中心（{alerts.length} 条）
          </button>
        </div>
      )}

      {takeoverWorkbench.count > 0 && (
        <div style={{ marginBottom: '10px' }}>
          <div style={{ background: '#ffffff', border: '1px solid #2563eb', borderRadius: '12px', padding: '10px 12px', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginBottom: '10px', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#1d4ed8' }}>Manual Takeover 工作台</div>
                <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
                  当前待人工处理：{takeoverWorkbench.count} 条
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <div style={{ fontSize: '12px', padding: '4px 8px', borderRadius: '999px', background: '#fee2e2', color: '#b91c1c' }}>
                  高优先级 {takeoverWorkbench.level_counts?.high || 0}
                </div>
                <div style={{ fontSize: '12px', padding: '4px 8px', borderRadius: '999px', background: '#fef3c7', color: '#92400e' }}>
                  中优先级 {takeoverWorkbench.level_counts?.medium || 0}
                </div>
                <div style={{ fontSize: '12px', padding: '4px 8px', borderRadius: '999px', background: '#e5e7eb', color: '#374151' }}>
                  低优先级 {takeoverWorkbench.level_counts?.low || 0}
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, minmax(0, 1fr))', gap: '10px' }}>
              {takeoverWorkbench.items.slice(0, 6).map((item) => {
                const pStyle = getPriorityStyle(item.priority)
                return (
                  <div key={item.ticket_id} style={{ border: '1px solid #dbeafe', background: '#f8fbff', borderRadius: '10px', padding: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', marginBottom: '6px' }}>
                      <div style={{ fontSize: '14px', fontWeight: 800 }}>{item.customer_name || item.customer_id}</div>
                      <div style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '999px', background: pStyle.bg, color: pStyle.text, fontWeight: 700 }}>
                        {item.priority || 'low'}
                      </div>
                    </div>

                    <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '6px' }}>
                      {item.country || '未知国家'} · {item.bucket || '待判断'} · {item.business_stage || '待补充阶段'}
                    </div>

                    <div style={{ fontSize: '13px', color: '#111827', lineHeight: 1.6, marginBottom: '6px' }}>
                      <strong>接管原因：</strong>{item.takeover_reason || 'waiting_human_takeover'}
                    </div>

                    <div style={{ fontSize: '13px', color: '#111827', lineHeight: 1.6, marginBottom: '6px' }}>
                      <strong>摘要：</strong>{item.summary || '暂无摘要'}
                    </div>

                    <div style={{ fontSize: '13px', color: '#1f2937', lineHeight: 1.6 }}>
                      <strong>建议动作：</strong>{item.next_action || '建议人工继续推进。'}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* ═══ 人工测试发消息面板 ═══ */}
      <div style={{ background: '#fff', border: '1px solid #d7dde7', borderRadius: '12px', padding: '10px 12px', marginBottom: '10px', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700 }}>人工测试发消息</div>
            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
              开启后可模拟客户消息进入系统（H5 将在 8 秒内自动刷新）
            </div>
          </div>
          {/* 主开关 */}
          <button
            onClick={() => { setSendPanelOpen((v) => !v); setSendStatus(null); setSendErrMsg('') }}
            style={{
              padding: '6px 16px', borderRadius: '999px', fontWeight: 700, fontSize: '13px', cursor: 'pointer',
              border: sendPanelOpen ? '1px solid #16a34a' : '1px solid #d1d5db',
              background: sendPanelOpen ? '#dcfce7' : '#f3f4f6',
              color: sendPanelOpen ? '#15803d' : '#374151',
            }}
          >
            {sendPanelOpen ? '● 人工输入 已开启' : '○ 人工输入 已关闭'}
          </button>
        </div>

        {sendPanelOpen && (
          <div style={{ marginTop: '12px', display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', gap: '8px', alignItems: 'end' }}>
            <div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>电话号码 *</div>
              <input
                value={sendForm.phone}
                onChange={(e) => setSendForm((f) => ({ ...f, phone: e.target.value }))}
                placeholder="+8613900000000"
                style={{ width: '100%', padding: '6px 8px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '13px', boxSizing: 'border-box' }}
              />
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>客户名</div>
              <input
                value={sendForm.name}
                onChange={(e) => setSendForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Ahmad"
                style={{ width: '100%', padding: '6px 8px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '13px', boxSizing: 'border-box' }}
              />
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>目标国家</div>
              <input
                value={sendForm.country}
                onChange={(e) => setSendForm((f) => ({ ...f, country: e.target.value }))}
                placeholder="阿联酋"
                style={{ width: '100%', padding: '6px 8px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '13px', boxSizing: 'border-box' }}
              />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>消息内容 *</div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  value={sendForm.message}
                  onChange={(e) => setSendForm((f) => ({ ...f, message: e.target.value }))}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSendMessage() }}
                  placeholder="I need 10 SUVs for resale..."
                  style={{ flex: 1, padding: '6px 8px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '13px' }}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={sendStatus === 'sending'}
                  style={{
                    padding: '6px 16px', borderRadius: '8px', fontWeight: 700, fontSize: '13px', cursor: 'pointer',
                    border: '1px solid #2563eb', background: sendStatus === 'sending' ? '#93c5fd' : '#2563eb',
                    color: '#fff', whiteSpace: 'nowrap',
                  }}
                >
                  {sendStatus === 'sending' ? '发送中...' : '发送'}
                </button>
              </div>
            </div>
            {sendErrMsg && (
              <div style={{ gridColumn: '1 / -1', fontSize: '12px', color: '#dc2626', background: '#fef2f2', borderRadius: '8px', padding: '6px 10px' }}>
                ⚠ {sendErrMsg}
              </div>
            )}
            {sendStatus === 'ok' && (
              <div style={{ gridColumn: '1 / -1', fontSize: '12px', color: '#16a34a', background: '#f0fdf4', borderRadius: '8px', padding: '6px 10px' }}>
                ✓ 消息已写入 runtime，H5 将在 8 秒内自动刷新显示。
              </div>
            )}
          </div>
        )}
      </div>

      {/* ═══ WhatsApp 水龙头开关 ═══ */}
      <div style={{ background: '#fff', border: '1px solid #d7dde7', borderRadius: '12px', padding: '10px 12px', marginBottom: '10px', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap', marginBottom: '8px' }}>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700 }}>WhatsApp 水龙头开关（runtime 真源读取）</div>
            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
              {loadingText}
            </div>
          </div>

          <button
            onClick={emergencyStop}
            style={{
              height: '34px',
              padding: '0 14px',
              borderRadius: '10px',
              border: '1px solid #ef4444',
              background: '#fff1f2',
              color: '#d92020',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            紧急止水（前端演示）
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1.2fr 1fr 1fr', gap: '10px', alignItems: 'stretch' }}>
          <div style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px', background: '#fafafa' }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '6px' }}>第1层 · 接入层</div>
            <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: '8px' }}>WhatsApp 接入模式</div>
            <div style={{ fontSize: '14px', fontWeight: 700 }}>{getModeLabel(ingressMode)}</div>
          </div>

          <div style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px', background: '#fafafa' }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '6px' }}>第2层 · 处理层</div>
            <div style={{ fontSize: '12px', lineHeight: 1.8 }}>
              <div>自动分类：{autoClassify ? '开' : '关'}</div>
              <div>自动标签：{autoTagging ? '开' : '关'}</div>
              <div>H5可见：{h5Visible ? '开' : '关'}</div>
            </div>
          </div>

          <div style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px', background: '#fafafa' }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '6px' }}>第3层 · 输出层</div>
            <div style={{ fontSize: '12px', lineHeight: 1.8 }}>
              <div>自动回复：{autoReply ? '开' : '关'}</div>
              <div>自动外发：{autoDispatch ? '开' : '关'}</div>
              <div>当前策略：{ingressMode === 'readonly' ? '只观察不扰动' : ingressMode === 'manual' ? '人工接管 / dry_run' : '其他模式'}</div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${isMobile ? 2 : 4}, minmax(0, 1fr))`, gap: '10px', marginBottom: '10px' }}>
        {stats.map((item) => (
          <div key={item.label} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '12px' }}>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>{item.label}</div>
            <div style={{ fontSize: '24px', fontWeight: 800, marginTop: '4px' }}>{item.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }}>
        {channels.map((channel) => {
          const active = channel === activeChannel
          return (
            <button
              key={channel}
              onClick={() => setActiveChannel(channel)}
              style={{
                padding: '8px 12px',
                borderRadius: '10px',
                border: active ? '1px solid #2563eb' : '1px solid #d1d5db',
                background: active ? '#eff6ff' : '#fff',
                color: active ? '#1d4ed8' : '#111827',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              {channel}
            </button>
          )
        })}
      </div>

      {/* ── 全部客户总表 ── */}
      {activeChannel === '全部客户' && (
        <AllCustomersPanel
          customers={allCustomers}
          selectedId={allSelectedId}
          setSelectedId={setAllSelectedId}
          loading={allLoading}
        />
      )}

      {/* ── 历史客户重新激活面板 ── */}
      {activeChannel === '历史激活' && (
        <ReactivationPanel
          uploadStatus={reactUploadStatus}
          setUploadStatus={setReactUploadStatus}
          uploadError={reactUploadError}
          setUploadError={setReactUploadError}
          results={reactResults}
          setResults={setReactResults}
          myName={reactMyName}
          setMyName={setReactMyName}
          selectedId={reactSelectedId}
          setSelectedId={setReactSelectedId}
          progress={reactAnalysisProgress}
          setProgress={setReactAnalysisProgress}
        />
      )}

      {activeChannel !== '历史激活' && activeChannel !== '全部客户' && <div style={{ display: isMobile ? 'block' : 'grid', gridTemplateColumns: '360px 1fr', gap: '12px' }}>
        <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e5e7eb', padding: '10px', display: isMobile && mobileShowDetail ? 'none' : 'block' }}>
          <div style={{ fontSize: '14px', fontWeight: 800, marginBottom: '10px' }}>客户总览</div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: isMobile ? 'calc(100vh - 280px)' : '72vh', overflowY: 'auto' }}>
            {customers.map((item) => {
              const active = item.id === selectedId
              return (
                <div
                  key={item.id}
                  onClick={() => { setSelectedId(item.id); if (isMobile) { setMobileShowDetail(true); window.scrollTo(0, 0) } }}
                  style={{
                    border: active ? '1px solid #2563eb' : '1px solid #e5e7eb',
                    background: active ? '#eff6ff' : '#fff',
                    borderRadius: '10px',
                    padding: '10px',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', marginBottom: '4px' }}>
                    <div style={{ fontWeight: 800 }}>{item.name}</div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>{item.time}</div>
                  </div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '6px' }}>
                    {item.country} · {item.category} · {item.phone}
                  </div>
                  <div style={{ fontSize: '13px', color: '#111827', marginBottom: '8px' }}>{item.message}</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {item.keywords?.length ? item.keywords.map((kw) => (
                      <span key={kw} style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '999px', background: '#f3f4f6', color: '#374151' }}>
                        {kw}
                      </span>
                    )) : <span style={{ fontSize: '11px', color: '#9ca3af' }}>暂无关键词</span>}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e5e7eb', padding: '12px', display: isMobile && !mobileShowDetail ? 'none' : 'block' }}>
          {isMobile && mobileShowDetail && (
            <button onClick={() => { setMobileShowDetail(false); window.scrollTo(0, 0) }} style={{ marginBottom: '10px', padding: '10px 16px', borderRadius: '8px', border: '1px solid #d1d5db', background: '#f3f4f6', fontSize: '14px', cursor: 'pointer', fontWeight: 600, minHeight: '40px' }}>
              ← 返回列表
            </button>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center', marginBottom: '10px' }}>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 800 }}>{selected.name}</div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                {isFacebookEmptyView
                  ? ti('facebook.empty.subtitle', 'Facebook · 等待真实数据接入')
                  : `${selected.country} · ${selected.channel} · ${selected.phone}`}
              </div>
            </div>
            <div
              style={{
                padding: '6px 10px',
                borderRadius: '999px',
                background: isHot ? '#dcfce7' : '#f3f4f6',
                color: isHot ? '#166534' : '#374151',
                fontWeight: 700,
                fontSize: '12px',
              }}
            >
              {selected.category}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(3, 1fr)' : 'repeat(3, minmax(0, 1fr))', gap: '8px', marginBottom: '12px' }}>
            <div style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px' }}>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>主动消息数</div>
              <div style={{ fontSize: '20px', fontWeight: 800, marginTop: '4px' }}>{proactiveCount}</div>
            </div>
            <div style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px' }}>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>往返轮次</div>
              <div style={{ fontSize: '20px', fontWeight: 800, marginTop: '4px' }}>{exchangeCount}</div>
            </div>
            <div style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px' }}>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>人工接管</div>
              <div style={{ fontSize: '20px', fontWeight: 800, marginTop: '4px' }}>{selected.needs_human_review ? '是' : '否'}</div>
            </div>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <div style={{ fontSize: '14px', fontWeight: 800, marginBottom: '6px' }}>判断依据关键词</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {selected.keywords?.length ? selected.keywords.map((kw) => (
                <span key={kw} style={{ fontSize: '12px', padding: '4px 8px', borderRadius: '999px', background: '#eef2ff', color: '#3730a3' }}>
                  {kw}
                </span>
              )) : <span style={{ fontSize: '12px', color: '#9ca3af' }}>暂无关键词</span>}
            </div>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <div style={{ fontSize: '14px', fontWeight: 800, marginBottom: '6px' }}>判断说明</div>
            <div style={{ fontSize: '13px', lineHeight: 1.7, color: '#111827' }}>
              {isFacebookEmptyView
                ? ti('facebook.empty.detail', '当前 Facebook 真实聊天 / Feed 数据尚未进入 runtime view，请保持 webhook 在线并等待真实数据进入。')
                : selected.reason}
            </div>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <div style={{ fontSize: '14px', fontWeight: 800, marginBottom: '6px' }}>时间线</div>
            <div style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px', maxHeight: '180px', overflowY: 'auto', background: '#fafafa' }}>
              {selected.timeline?.length ? selected.timeline.map((line, idx) => (
                <div key={idx} style={{ fontSize: '12px', marginBottom: '6px', color: '#374151' }}>{line}</div>
              )) : (
                <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                  {isFacebookEmptyView ? ti('facebook.empty.timeline', '等待 Facebook runtime 时间线数据') : '暂无时间线'}
                </div>
              )}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '14px', fontWeight: 800, marginBottom: '6px' }}>聊天内容</div>
            <div style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px', maxHeight: '260px', overflowY: 'auto', background: '#fafafa' }}>
              {selected.messages?.length ? selected.messages.map((msg, idx) => {
                const isAgent = msg.role === '我方' || msg.role === 'agent'
                return (
                  <div key={idx} style={{ marginBottom: '10px', display: 'flex', flexDirection: 'column', alignItems: isAgent ? 'flex-end' : 'flex-start' }}>
                    <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '3px' }}>
                      {msg.role} · {msg.time}
                    </div>
                    <div style={{
                      fontSize: '13px',
                      lineHeight: 1.7,
                      padding: '7px 12px',
                      borderRadius: isAgent ? '14px 4px 14px 14px' : '4px 14px 14px 14px',
                      maxWidth: '85%',
                      background: isAgent ? '#dcfce7' : '#fee2e2',
                      color: isAgent ? '#14532d' : '#7f1d1d',
                      border: isAgent ? '1px solid #86efac' : '1px solid #fca5a5',
                      fontFamily: "'Noto Sans Arabic', 'PingFang SC', sans-serif",
                      direction: /[\u0600-\u06FF]/.test(msg.text || '') ? 'rtl' : 'ltr',
                      textAlign: /[\u0600-\u06FF]/.test(msg.text || '') ? 'right' : 'left',
                    }}>
                      {msg.text}
                    </div>
                  </div>
                )
              }) : (
                <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                  {isFacebookEmptyView ? ti('facebook.empty.messages', '等待 Facebook runtime 聊天 / 互动数据') : '暂无聊天内容'}
                </div>
              )}
            </div>
          </div>

          {/* ═══ AI建议回复面板 ═══ */}
          <div style={{ marginTop: '14px', border: '1px solid #dbeafe', borderRadius: '12px', padding: '12px', background: '#f8fbff' }}>
            {/* 标题行 + 主开关 */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px', marginBottom: '10px', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '14px', fontWeight: 800, color: '#1d4ed8' }}>AI 建议回复</div>
                <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>
                  AI 生成建议 → 人类审核 → 决定是否发送
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                {/* 子开关：允许AI自动发 */}
                {aiReplyEnabled && (
                  <button
                    onClick={() => setAiAutoSend((v) => !v)}
                    style={{
                      padding: '4px 12px', borderRadius: '999px', fontSize: '11px', fontWeight: 700, cursor: 'pointer',
                      border: aiAutoSend ? '1px solid #dc2626' : '1px solid #d1d5db',
                      background: aiAutoSend ? '#fef2f2' : '#f3f4f6',
                      color: aiAutoSend ? '#dc2626' : '#6b7280',
                    }}
                  >
                    {aiAutoSend ? '⚡ AI可自动发（高风险，谨慎）' : '○ AI建议模式（人类审核）'}
                  </button>
                )}
                {/* 主开关 */}
                <button
                  onClick={() => { setAiReplyEnabled((v) => !v); setAiReplyText(''); setAiReplyStatus(null) }}
                  style={{
                    padding: '4px 12px', borderRadius: '999px', fontSize: '12px', fontWeight: 700, cursor: 'pointer',
                    border: aiReplyEnabled ? '1px solid #2563eb' : '1px solid #d1d5db',
                    background: aiReplyEnabled ? '#eff6ff' : '#f3f4f6',
                    color: aiReplyEnabled ? '#1d4ed8' : '#6b7280',
                  }}
                >
                  {aiReplyEnabled ? '● AI建议 已开启' : '○ AI建议 已关闭'}
                </button>
              </div>
            </div>

            {aiReplyEnabled && (
              <div>
                {/* 获取AI建议按钮 + 来源标签 */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <button
                    onClick={handleFetchAiReply}
                    disabled={aiReplyLoading || isFacebookEmptyView || !selected.messages?.length}
                    style={{
                      padding: '6px 14px', borderRadius: '8px', fontSize: '12px', fontWeight: 700, cursor: 'pointer',
                      border: '1px solid #2563eb', background: '#2563eb', color: '#fff',
                      opacity: (aiReplyLoading || isFacebookEmptyView || !selected.messages?.length) ? 0.5 : 1,
                    }}
                  >
                    {aiReplyLoading ? '⏳ 生成中...' : '🤖 重新生成'}
                  </button>
                  {aiReplyText && (
                    <button
                      onClick={() => { setAiReplyText(''); setAiReplyStatus(null) }}
                      style={{ padding: '6px 12px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer', border: '1px solid #d1d5db', background: '#fff', color: '#374151' }}
                    >
                      清空
                    </button>
                  )}
                  {/* AI 来源标签 */}
                  {aiSource && (
                    <span style={{
                      fontSize: '11px', padding: '2px 8px', borderRadius: '999px', fontWeight: 600,
                      background: aiSource === 'gemini' ? '#f0fdf4' : aiSource === 'claude' ? '#eff6ff' : '#fef9c3',
                      color: aiSource === 'gemini' ? '#16a34a' : aiSource === 'claude' ? '#2563eb' : '#92400e',
                      border: aiSource === 'gemini' ? '1px solid #bbf7d0' : aiSource === 'claude' ? '1px solid #bfdbfe' : '1px solid #fde68a',
                    }}>
                      {aiSource === 'gemini' ? '✦ Gemini 2.5 Flash'
                        : aiSource === 'claude' ? '◆ Claude'
                        : '≈ 规则模板'}
                      {aiExpCount > 0 && ` · ${aiExpCount}条经验`}
                    </span>
                  )}
                  {aiReplyLoading && !aiSource && (
                    <span style={{ fontSize: '11px', color: '#6b7280' }}>正在调用 Gemini...</span>
                  )}
                </div>

                {/* AI建议内容 */}
                {aiReplyText && (
                  <div>
                    <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '6px' }}>
                      AI 建议回复内容（可修改后发送）：
                    </div>
                    <textarea
                      value={aiReplyText}
                      onChange={(e) => setAiReplyText(e.target.value)}
                      rows={3}
                      style={{
                        width: '100%', padding: '8px', border: '1px solid #bfdbfe', borderRadius: '8px',
                        fontSize: '13px', lineHeight: 1.7, background: '#fff', boxSizing: 'border-box',
                        resize: 'vertical',
                      }}
                    />

                    {/* 操作按钮 */}
                    <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
                      <button
                        onClick={handleApproveAiReply}
                        disabled={aiReplyStatus === 'sending'}
                        style={{
                          padding: '6px 14px', borderRadius: '8px', fontSize: '12px', fontWeight: 700, cursor: 'pointer',
                          border: '1px solid #16a34a', background: '#16a34a', color: '#fff',
                          opacity: aiReplyStatus === 'sending' ? 0.6 : 1,
                        }}
                      >
                        {aiReplyStatus === 'sending' ? '发送中...' : '✓ 采纳并发送'}
                      </button>
                      <button
                        onClick={() => { setAiReplyText(''); setAiReplyStatus(null) }}
                        style={{ padding: '6px 12px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer', border: '1px solid #d1d5db', background: '#fff', color: '#6b7280' }}
                      >
                        忽略
                      </button>
                      {aiAutoSend && (
                        <div style={{ fontSize: '11px', color: '#dc2626', display: 'flex', alignItems: 'center' }}>
                          ⚠ AI自动发已开启，采纳后将直接写入 runtime
                        </div>
                      )}
                    </div>

                    {aiReplyStatus === 'sent' && (
                      <div style={{ marginTop: '8px', fontSize: '12px', color: '#16a34a', background: '#f0fdf4', borderRadius: '8px', padding: '6px 10px' }}>
                        ✓ AI回复已发送，H5 将在 8 秒内刷新。
                      </div>
                    )}
                    {aiReplyStatus === 'err' && (
                      <div style={{ marginTop: '8px', fontSize: '12px', color: '#dc2626', background: '#fef2f2', borderRadius: '8px', padding: '6px 10px' }}>
                        ⚠ 发送失败，请检查后端 API 是否在线。
                      </div>
                    )}
                  </div>
                )}

                {!aiReplyText && !aiReplyLoading && (
                  <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                    切换客户时自动生成建议 · 由 Gemini 2.5 Flash 驱动 · 修改后再决定是否发送
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>}
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
