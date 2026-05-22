import { useState, useEffect, useRef } from 'react'
import { chatApi } from '../api/chatApi'
import { apiClient } from '../api/apiClient'

export function useChat(initialChatId, session, onAuthRequired, onChatCreated) {
  const [messages, setMessages] = useState([])
  const [hasSentMessage, setHasSentMessage] = useState(false)
  const [currentChatId, setCurrentChatId] = useState(initialChatId)
  const [loading, setLoading] = useState(false)
  const chatDisplayRef = useRef(null)

  // Sync internal ID with external prop
  useEffect(() => {
    setCurrentChatId(initialChatId)
    setHasSentMessage(false) 
    if (!initialChatId) {
        setMessages([])
    }
  }, [initialChatId])

  // Load History
  useEffect(() => {
    // Only fetch history if it's a pre-existing chat and we haven't started typing in it yet.
    // This prevents the history fetch from wiping out the screen during a live stream.
    if (currentChatId && !hasSentMessage && session) {
      const getHistory = async () => {
        setLoading(true)
        const history = await chatApi.fetchChatMessages(currentChatId, session.user.id)
        setMessages(history)
        setHasSentMessage(true)
        setLoading(false)
      }
      getHistory()
    }
  }, [currentChatId, hasSentMessage, session])

  // Auto-scroll
  useEffect(() => {
    if (chatDisplayRef.current) {
      chatDisplayRef.current.scrollTop = chatDisplayRef.current.scrollHeight
    }
  }, [messages])

  const handleSendMessage = async (message, model, file) => {
    if (!session) {
      if (onAuthRequired) onAuthRequired()
      return
    }

    setHasSentMessage(true)
    
    // Generate temporary public URL for local rendering of preview image
    const localUrl = file ? URL.createObjectURL(file) : null

    // Add user message locally for instant UI update
    setMessages(prev => [...prev, { role: 'user', content: message, media_url: localUrl }])
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])
    
    try {
      let base64_image = null
      let uploadChatId = currentChatId

      if (file) {
        if (file?.type === 'application/pdf') {
          // Upload PDF before generating the AI response
          const uploadRes = await apiClient.uploadDocument('/api/documents/upload', file, currentChatId, session.user.id)
          if (uploadRes.chat_id && uploadRes.chat_id !== currentChatId) {
            uploadChatId = uploadRes.chat_id
            setCurrentChatId(uploadChatId)
            window.history.pushState({}, '', `/chat/${uploadChatId}`)
            if (onChatCreated) onChatCreated(uploadChatId)
          }
        } else if (file?.type?.startsWith('image/')) {
          // Convert image to base64 for vision models
          base64_image = await new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.readAsDataURL(file)
            reader.onload = () => resolve(reader.result)
            reader.onerror = error => reject(error)
          })
        }
      }

      const response = await apiClient.stream('/api/ai/stream', {
        message,
        user_id: session.user.id,
        chat_id: uploadChatId,
        model: model,
        base64_image
      }, session.user.id)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumulatedText = ''
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        buffer += chunk
        
        const lines = buffer.split('\n')
        // Keep the last line in the buffer because it might be incomplete
        buffer = lines.pop()
        
        for (const line of lines) {
          if (!line.trim()) continue;

          try {
            const data = JSON.parse(line);
            
            if (data.chat_id) {
              const newId = data.chat_id;
              if (newId !== currentChatId) {
                  setCurrentChatId(newId);
                  window.history.pushState({}, '', `/chat/${newId}`);
                  if (onChatCreated) onChatCreated(newId); // Tell the page to refresh the sidebar!
              }
            }

            if (data.error) {
              accumulatedText += "\n\n❌ **" + data.error + "**";
              setMessages(prev => {
                const newMessages = [...prev]
                const lastMessage = newMessages[newMessages.length - 1]
                if (lastMessage && lastMessage.role === 'assistant') {
                  lastMessage.content = accumulatedText
                }
                return newMessages
              })
              break; // Stop processing the stream if there's an error
            }

            if (data.text) {
              accumulatedText += data.text;
              setMessages(prev => {
                const newMessages = [...prev]
                const lastMessage = newMessages[newMessages.length - 1]
                if (lastMessage && lastMessage.role === 'assistant') {
                  lastMessage.content = accumulatedText
                }
                return newMessages
              })
            }
          } catch (e) {
            console.error("Error parsing stream line:", line, e);
          }
        }
      }
      
    } catch (error) {
      console.log('Error sending message:', error)
      setMessages(prev => {
        const newMessages = [...prev]
        const lastMessage = newMessages[newMessages.length - 1]
        if (lastMessage && lastMessage.role === 'assistant') {
          lastMessage.content = `❌ **Error:** ${error.message}`
        }
        return newMessages
      })
    }
  }

  return {
    messages,
    hasSentMessage,
    chatDisplayRef,
    loading,
    handleSendMessage
  }
}
