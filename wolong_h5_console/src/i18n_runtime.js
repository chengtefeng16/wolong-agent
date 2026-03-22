# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

export async function fetchJson(url, fallback) {
  try {
    const res = await fetch(`${url}?t=${Date.now()}`)
    if (!res.ok) return fallback
    return await res.json()
  } catch {
    return fallback
  }
}

export async function loadI18nConfig() {
  return await fetchJson('/runtime/i18n_runtime_config_v1.json', {
    default_language: 'zh-CN',
    supported_languages: ['zh-CN', 'en-US'],
    ui_language: 'zh-CN'
  })
}

export async function loadLocaleDict(lang) {
  const fallback = {}
  try {
    const res = await fetch(`/runtime/i18n/${lang}.json?t=${Date.now()}`)
    if (!res.ok) return fallback
    return await res.json()
  } catch {
    return fallback
  }
}

export function t(dict, key, fallback = '') {
  return dict?.[key] || fallback || key
}
