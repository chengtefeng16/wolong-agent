/**
 * Onboard 页：「连接你的 WhatsApp」
 * 使用 Meta Embedded Signup v4（FB.login popup）
 *
 * 环境变量：
 *   VITE_META_APP_ID      — Meta App ID
 *   VITE_API_BASE         — 后端地址，如 https://api.wolong.ai
 */
import { useEffect, useState } from 'react'

const META_APP_ID = import.meta.env.VITE_META_APP_ID || ''
const API_BASE    = import.meta.env.VITE_API_BASE    || 'http://localhost:8000'

// ── Meta JS SDK loader ────────────────────────────────────────────────────────
function useMetaSDK(appId) {
  const [ready, setReady] = useState(false)
  useEffect(() => {
    if (!appId) return
    window.fbAsyncInit = function () {
      window.FB.init({
        appId,
        autoLogAppEvents: true,
        xfbml: false,
        version: 'v20.0',
      })
      setReady(true)
    }
    if (document.getElementById('fb-jssdk')) { setReady(true); return }
    const js = document.createElement('script')
    js.id = 'fb-jssdk'
    js.src = 'https://connect.facebook.net/en_US/sdk.js'
    js.async = true
    document.head.appendChild(js)
  }, [appId])
  return ready
}

// ── Main component ────────────────────────────────────────────────────────────
export default function Onboard({ token, onConnected }) {
  const sdkReady = useMetaSDK(META_APP_ID)
  const [step, setStep] = useState('idle')   // idle | loading | success | error
  const [waba, setWaba] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')

  async function handleConnect() {
    if (!sdkReady) { setErrorMsg('Meta SDK not loaded yet'); return }
    setStep('loading')

    window.FB.login(
      async (response) => {
        if (response.status !== 'connected' || !response.authResponse?.code) {
          setStep('error')
          setErrorMsg('Authorization cancelled or failed.')
          return
        }
        const code = response.authResponse.code
        try {
          const res = await fetch(`${API_BASE}/api/v1/whatsapp/connect`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ code }),
          })
          if (!res.ok) {
            const err = await res.json()
            throw new Error(err.detail || 'Connection failed')
          }
          const data = await res.json()
          setWaba(data)
          setStep('success')
          onConnected?.(data)
        } catch (e) {
          setStep('error')
          setErrorMsg(e.message)
        }
      },
      {
        // Embedded Signup v4 scopes
        scope: 'whatsapp_business_management,business_management',
        // v4 config_id: replace with your Meta App's Embedded Signup config id
        // See: https://developers.facebook.com/docs/whatsapp/embedded-signup
        extras: {
          setup: {},
          featureType: '',
          sessionInfoVersion: '3',
        },
      }
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        {/* Logo / brand */}
        <div style={styles.logo}>🐉</div>
        <h1 style={styles.title}>卧龙 AI 销售助理</h1>
        <p style={styles.subtitle}>
          连接你的 WhatsApp Business 号码，AI 自动回复全球客户，支持中/英/俄/阿拉伯语。
        </p>

        {step === 'idle' && (
          <button
            style={{...styles.btn, opacity: sdkReady ? 1 : 0.6}}
            onClick={handleConnect}
            disabled={!sdkReady}
          >
            <WhatsAppIcon />
            连接我的 WhatsApp Business
          </button>
        )}

        {step === 'loading' && (
          <div style={styles.status}>
            <Spinner />
            <span>正在连接 WhatsApp，请在弹出窗口中完成授权…</span>
          </div>
        )}

        {step === 'success' && waba && (
          <div style={styles.successBox}>
            <div style={styles.checkmark}>✅</div>
            <div style={styles.successTitle}>连接成功！</div>
            <div style={styles.phoneDisplay}>{waba.display_phone || waba.phone_number_id}</div>
            <p style={styles.successNote}>
              你的 WhatsApp 已接入卧龙 AI。现在可以开始接收和回复客户消息了。
            </p>
            <button style={styles.btnSecondary} onClick={() => window.location.href = '/dashboard'}>
              进入控制台 →
            </button>
          </div>
        )}

        {step === 'error' && (
          <div style={styles.errorBox}>
            <div>❌ {errorMsg}</div>
            <button style={styles.btnSecondary} onClick={() => setStep('idle')}>
              重试
            </button>
          </div>
        )}

        <div style={styles.steps}>
          <div style={styles.step}><span style={styles.stepNum}>1</span> 点击按钮</div>
          <div style={styles.stepArrow}>→</div>
          <div style={styles.step}><span style={styles.stepNum}>2</span> Meta 授权</div>
          <div style={styles.stepArrow}>→</div>
          <div style={styles.step}><span style={styles.stepNum}>3</span> 开始接单</div>
        </div>

        <p style={styles.note}>
          需要已有 Meta Business 账号 + WhatsApp Business 号码。
          <a href="https://business.facebook.com/" target="_blank" rel="noreferrer" style={styles.link}>
            还没有？点这里创建
          </a>
        </p>
      </div>
    </div>
  )
}

// ── Icons / micro-components ──────────────────────────────────────────────────

function WhatsAppIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style={{marginRight: 8, verticalAlign: 'middle'}}>
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
    </svg>
  )
}

function Spinner() {
  return (
    <div style={{
      width: 20, height: 20, border: '2px solid #25D366',
      borderTopColor: 'transparent', borderRadius: '50%',
      animation: 'spin 0.8s linear infinite', marginRight: 8,
      display: 'inline-block',
    }} />
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = {
  container: {
    minHeight: '100vh', display: 'flex', alignItems: 'center',
    justifyContent: 'center', background: 'linear-gradient(135deg,#f0fdf4,#dcfce7)',
    padding: 20, fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',
  },
  card: {
    background: '#fff', borderRadius: 16, padding: '48px 40px',
    maxWidth: 480, width: '100%',
    boxShadow: '0 20px 60px rgba(0,0,0,0.10)',
    textAlign: 'center',
  },
  logo: { fontSize: 48, marginBottom: 12 },
  title: { fontSize: 24, fontWeight: 700, color: '#111', margin: '0 0 8px' },
  subtitle: { color: '#555', lineHeight: 1.6, margin: '0 0 32px' },
  btn: {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    background: '#25D366', color: '#fff', border: 'none',
    padding: '14px 28px', borderRadius: 12, fontSize: 16, fontWeight: 600,
    cursor: 'pointer', width: '100%', transition: 'background 0.2s',
  },
  btnSecondary: {
    background: '#f3f4f6', color: '#374151', border: 'none',
    padding: '10px 20px', borderRadius: 8, fontSize: 14, cursor: 'pointer',
    marginTop: 12,
  },
  status: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    color: '#555', padding: 20,
  },
  successBox: {
    background: '#f0fdf4', borderRadius: 12, padding: 24, marginBottom: 24,
  },
  checkmark: { fontSize: 32, marginBottom: 8 },
  successTitle: { fontSize: 18, fontWeight: 700, color: '#15803d', marginBottom: 8 },
  phoneDisplay: {
    fontSize: 22, fontWeight: 700, color: '#111',
    fontFamily: 'monospace', marginBottom: 8,
  },
  successNote: { color: '#555', margin: '8px 0 0' },
  errorBox: {
    background: '#fef2f2', borderRadius: 12, padding: 16,
    color: '#dc2626', marginBottom: 16,
  },
  steps: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    gap: 8, margin: '32px 0 20px', color: '#555',
  },
  step: { display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 },
  stepNum: {
    background: '#dcfce7', color: '#15803d', borderRadius: '50%',
    width: 22, height: 22, display: 'inline-flex',
    alignItems: 'center', justifyContent: 'center',
    fontSize: 12, fontWeight: 700,
  },
  stepArrow: { color: '#9ca3af', fontSize: 16 },
  note: { color: '#9ca3af', fontSize: 12, marginTop: 8 },
  link: { color: '#15803d', marginLeft: 4 },
}
