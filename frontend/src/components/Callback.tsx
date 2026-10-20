import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export function Callback() {
  const navigate = useNavigate()
  const { setUser } = useAuth()

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const error = params.get('error')

    if (error) {
      console.error('OAuth error:', error)
      navigate('/login?error=' + encodeURIComponent(error))
      return
    }

    if (!code) {
      navigate('/login')
      return
    }

    // In a real implementation, exchange code for tokens with backend
    // For now, create a mock user session
    const mockUser = {
      id: '1',
      username: 'demo-user',
      email: 'demo@example.com',
      roles: ['viewer'],
    }
    
    sessionStorage.setItem('user', JSON.stringify(mockUser))
    setUser(mockUser)
    navigate('/')
  }, [navigate, setUser])

  return (
    <div className="loading">
      Completing sign in...
    </div>
  )
}