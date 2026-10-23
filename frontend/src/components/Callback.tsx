import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export function Callback() {
  const navigate = useNavigate()
  const { exchangeCodeForToken, setUser } = useAuth()

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

    exchangeCodeForToken(code).then((user: any) => {
      if (user) {
        setUser(user)
        navigate('/')
      } else {
        navigate('/login?error=token_exchange_failed')
      }
    })
  }, [navigate, exchangeCodeForToken, setUser])

  return (
    <div className="loading">
      Completing sign in...
    </div>
  )
}