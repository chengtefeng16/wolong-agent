/* ================================================================
 * Copyright (c) 2026 程特峰 (Tefeng Cheng)
 * All Rights Reserved.
 *
 * Project: AgentOS / Wolong Agent System
 * This source code is proprietary and confidential.
 * Unauthorized copying, modification, distribution or use
 * of this software, in whole or in part, is strictly prohibited.
 * ================================================================ */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
