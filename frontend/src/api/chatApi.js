import { apiClient } from './apiClient';

// chat api calls
export const chatApi = {
  fetchUserChats: async (userId) => {
    return apiClient.get(`/api/chat/list/${userId}`, { userId });
  },

  fetchChatMessages: async (chatId, userId) => {
    return apiClient.get(`/api/chat/history/${chatId}`, { userId });
  },

  deleteChat: async (chatId, userId) => {
    return apiClient.delete(`/api/chat/delete/${chatId}`, { userId });
  },
};
