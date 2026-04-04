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

const channels = ['WhatsApp', 'Facebook', 'Ins（后续）', '更多渠道（后续）']

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

export default function App() {
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
  const [alerts, setAlerts] = useState([])
  const [showAlerts, setShowAlerts] = useState(true)
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

  // ── 当前选中客户有新的预生成建议时，自动刷新 AI 建议框 ──
  const pendingReplyKey = selected?.pending_ai_reply?.generated_at
  useEffect(() => {
    if (!pendingReplyKey || !selected?.pending_ai_reply?.text) return
    const pending = selected.pending_ai_reply
    // 只在文本真正变化时更新（避免重复覆盖用户正在编辑的内容）
    if (pending.text !== aiOriginalSuggestion) {
      setAiReplyText(pending.text)
      setAiOriginalSuggestion(pending.text)
      setAiSource(pending.source || 'gemini')
      setAiReplyStatus(null)
      if (!aiReplyEnabled) setAiReplyEnabled(true)
      console.log('[AI] 新消息预生成建议已自动填入:', pending.source)
    }
  }, [pendingReplyKey]) // eslint-disable-line react-hooks/exhaustive-deps

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
          <div style={{ background: '#ffffff', border: '1px solid #ef4444', borderRadius: '12px', padding: '10px 12px', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <div style={{ fontSize: '15px', fontWeight: 800, color: '#b91c1c' }}>
                预警中心（{alerts.length}）
              </div>
              <button
                onClick={() => setShowAlerts(false)}
                style={{ border: '1px solid #d1d5db', background: '#fff', borderRadius: '8px', padding: '4px 10px', cursor: 'pointer', fontSize: '12px' }}
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
              border: '1px solid #ef4444',
              background: '#fff1f2',
              color: '#b91c1c',
              borderRadius: '10px',
              padding: '8px 12px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            展开预警中心（{alerts.length}）
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

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '10px' }}>
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
          <div style={{ marginTop: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', alignItems: 'end' }}>
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

        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: '10px', alignItems: 'stretch' }}>
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

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: '10px', marginBottom: '10px' }}>
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

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '12px' }}>
        <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e5e7eb', padding: '10px' }}>
          <div style={{ fontSize: '14px', fontWeight: 800, marginBottom: '10px' }}>客户总览</div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '72vh', overflowY: 'auto' }}>
            {customers.map((item) => {
              const active = item.id === selectedId
              return (
                <div
                  key={item.id}
                  onClick={() => setSelectedId(item.id)}
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

        <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e5e7eb', padding: '12px' }}>
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

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '10px', marginBottom: '12px' }}>
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
      </div>
    </div>
  )
}
