import { apiClient } from './apiClient';
import { supabase } from './supabase';


export const authApi = {
  signUp: async (email, password) => {
    return apiClient.post('/api/auth/signup', { email, password });
  },

  signIn: async (email, password) => {
    const response = await apiClient.post('/api/auth/login', { email, password });
    
    if (response && response.session) {
        await supabase.auth.setSession({
            access_token: response.session.access_token,
            refresh_token: response.session.refresh_token
        });
    }
    return response;
  },

  signOut: async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  },

  syncProfile: async (user) => {
    if (!user) return null;
    return apiClient.post('/api/auth/sync', {
      id: user.id,
      email: user.email,
      username: user.email.split('@')[0]
    });
  },

  upgradeSubscription: async (userId, subscription) => {
    return apiClient.post('/api/auth/upgrade', { subscription }, { userId });
  },

  getProfile: async (userId) => {
    return apiClient.get('/api/auth/me', { userId });
  }
};
