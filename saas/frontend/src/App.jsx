import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Onboard from './pages/Onboard'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'

function PrivateRoute({ token, children }) {
  if (!token) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('wl_token') || '')

  function handleLogin(newToken) {
    localStorage.setItem('wl_token', newToken)
    setToken(newToken)
  }

  function handleLogout() {
    localStorage.removeItem('wl_token')
    setToken('')
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login onLogin={handleLogin} />} />
        <Route path="/onboard" element={
          <PrivateRoute token={token}>
            <Onboard token={token} onConnected={() => {}} />
          </PrivateRoute>
        } />
        <Route path="/dashboard" element={
          <PrivateRoute token={token}>
            <Dashboard token={token} onLogout={handleLogout} />
          </PrivateRoute>
        } />
        <Route path="*" element={<Navigate to={token ? '/dashboard' : '/login'} replace />} />
      </Routes>
    </BrowserRouter>
  )
}
