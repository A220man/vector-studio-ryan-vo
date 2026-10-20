import { Routes, Route, Navigate } from 'react-router-dom'
import { Dashboard } from './components/Dashboard'
import { Login } from './components/Login'
import { Callback } from './components/Callback'
import { Settings } from './components/Settings'
import { useAuth } from './hooks/useAuth'
import { AuthProvider } from './hooks/AuthContext'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth()
  
  if (loading) {
    return <div className="loading">Loading...</div>
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth()
  
  if (loading) {
    return <div className="loading">Loading...</div>
  }
  
  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }
  
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/callback" element={<Callback />} />
      <Route path="/" element={
        <PrivateRoute>
          <Dashboard />
        </PrivateRoute>
      } />
      <Route path="/settings" element={
        <PrivateRoute>
          <Settings />
        </PrivateRoute>
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <div className="app">
        <header className="header">
          <div className="container header-content">
            <h1 className="logo">Vector Studio</h1>
            <nav className="nav">
              <a href="/" className="nav-link">Dashboard</a>
              <a href="/settings" className="nav-link">Settings</a>
            </nav>
          </div>
        </header>
        <main className="main">
          <div className="container">
            <AppRoutes />
          </div>
        </main>
        <footer className="footer">
          <div className="container">
            <p>Vector Studio - AI Agent Configuration Manager | Ryan Vo | AI & Machine Learning</p>
          </div>
        </footer>
      </div>
    </AuthProvider>
  )
}

export default App