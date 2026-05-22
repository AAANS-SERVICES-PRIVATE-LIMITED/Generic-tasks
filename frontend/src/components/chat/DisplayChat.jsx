import React from 'react'
import ChatInput from './ChatInput'
import './DisplayChat.css'
import { useChat } from '../../hooks/useChat'

export default function DisplayChat({ chatState = 'new', session, onAuthRequired, initialChatId = null, onChatCreated }) {
  const {
    messages,
    hasSentMessage,
    chatDisplayRef,
    loading,
    handleSendMessage
  } = useChat(initialChatId, session, onAuthRequired, onChatCreated)

  const isNewEmptyChat = chatState !== 'old' && !hasSentMessage

  if (loading) {
    return (
      <div className="display-chat loading">
        <div className="loading-dots">
          <span /><span /><span />
        </div>
      </div>
    )
  }

  return (
    <div className={`display-chat ${isNewEmptyChat ? 'centered' : ''}`}>
      {/* Messages area */}
      {!isNewEmptyChat && (
        <div className="chat-scroll-area" ref={chatDisplayRef}>
          <div className="messages-container">
            {messages.map((msg, index) => (
              <div key={index} className={`message-row ${msg.role}`}>
                {msg.role === 'assistant' && (
                  <div className="assistant-icon">
                    {/* Logo placeholder */}
                    <div className="assistant-logo-placeholder" />
                  </div>
                )}
                <div className={`message-bubble ${msg.role}`}>
                  {msg.media_url && (
                    <div className="message-media-attachment">
                      <img src={msg.media_url} alt="Uploaded media" className="bubble-attached-image" />
                    </div>
                  )}
                  {msg.content && <span className="message-text">{msg.content}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Welcome state — centered */}
      {isNewEmptyChat && (
        <div className="welcome-area">
          <h2 className="welcome-heading">What are you working on?</h2>
        </div>
      )}

      {/* Input always at bottom (or center when welcome) */}
      <div className={`input-dock ${isNewEmptyChat ? 'input-dock-center' : 'input-dock-bottom'}`}>
        <ChatInput onSendMessage={handleSendMessage} />
      </div>
    </div>
  )
}
