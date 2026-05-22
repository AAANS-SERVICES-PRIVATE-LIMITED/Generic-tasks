import { useState, useEffect } from 'react'
import { supabase } from '../api/supabase'
import { authApi } from '../api/authApi'

export function useAuth() {
  const [session, setSession] = useState(null)
  const [userProfile, setUserProfile] = useState(null)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [authView, setAuthView] = useState('sign_in')

  const fetchProfile = async (user) => {
    if (!user) return;
    try {
      await authApi.syncProfile(user);
      const profile = await authApi.getProfile(user.id);
      setUserProfile(profile);
    } catch (e) {
      console.error('Failed to fetch user profile:', e);
    }
  };

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      if (session) {
        fetchProfile(session.user);
      } else {
        setUserProfile(null);
      }
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      if (session) {
        setShowAuthModal(false)
        fetchProfile(session.user);
      } else {
        setUserProfile(null);
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  const handleLoginClick = () => {
    setAuthView('sign_in')
    setShowAuthModal(true)
  }

  const handleSignUpClick = () => {
    setAuthView('sign_up')
    setShowAuthModal(true)
  }

  const handleLogout = async () => {
    await authApi.signOut()
    setUserProfile(null)
  }

  const closeAuthModal = () => {
    setShowAuthModal(false)
  }

  const refreshProfile = () => {
    if (session) fetchProfile(session.user);
  };

  return {
    session,
    userProfile,
    showAuthModal,
    authView,
    handleLoginClick,
    handleSignUpClick,
    handleLogout,
    closeAuthModal,
    refreshProfile,
  }
}
