import { useState, useEffect, useRef } from 'react'
import './ChatInput.css'
import { AVAILABLE_MODELS, DEFAULT_MODEL } from '../../constants'

function ChatInput({ onSendMessage }) {
  const [message, setMessage] = useState('')
  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL)
  const textareaRef = useRef(null)
  const [isModelOpen, setIsModelOpen] = useState(false)

  const [selectedFile, setSelectedFile] = useState(null)
  const fileInputRef = useRef(null)

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
    }
  }, [message, selectedFile])

  // Close model dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!e.target.closest('.input-model-selector')) {
        setIsModelOpen(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  const handleAttachClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click()
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file && (file.type.startsWith('image/') || file.type === 'application/pdf')) {
      setSelectedFile(file)
    }
    // Reset file input value so same file can be selected again
    e.target.value = ''
  }

  const handleRemoveFile = () => {
    setSelectedFile(null)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() || selectedFile) {
      // In the future we will wire this file up to the backend
      onSendMessage(message.trim(), selectedModel, selectedFile)
      setMessage('')
      setSelectedFile(null)
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const selectedModelObj = AVAILABLE_MODELS.find(m => m.id === selectedModel)
  const selectedModelLabel = selectedModelObj ? selectedModelObj.label : 'Select Model'
  const canSend = message.trim().length > 0 || !!selectedFile

  return (
    <div className="chatgpt-input-area">
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/*,application/pdf"
        style={{ display: 'none' }}
      />

      {/* Main Input Box */}
      <div className="input-box-wrapper">
        {/* Selected image preview inside the input block */}
        {selectedFile && (
          <div className="attached-media-preview">
            <div className="media-thumbnail">
              {selectedFile?.type?.startsWith('image/') ? (
                <img src={URL.createObjectURL(selectedFile)} alt="Upload preview" />
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%', background: '#333', color: 'white', borderRadius: '8px' }}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                  </svg>
                </div>
              )}
              <button className="remove-media-btn" type="button" onClick={handleRemoveFile} title="Remove attachment">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>
        )}

        <div className="input-box">
          {/* Plus / Attach button */}
          <button
            className={`input-action-btn ${selectedFile ? 'file-attached' : ''}`}
            type="button"
            onClick={handleAttachClick}
            title="Attach image or PDF"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </button>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything"
            className="chat-textarea"
            rows={1}
          />

          {/* Right icons */}
          <div className="input-right-actions">
            {/* Microphone */}
            <button className="input-action-btn" type="button" title="Voice input">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
            </button>

            {/* Send button — dark circle with up-arrow (always visible) */}
            <button
              className={`send-btn ${canSend ? 'active' : ''}`}
              type="button"
              onClick={handleSubmit}
              title="Send"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 4l8 16-8-4-8 4 8-16z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Bottom row: chips + model selector */}
      <div className="input-bottom-row">
        {/* Suggestion chips */}
        <div className="suggestion-chips">
          <button className="chip">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
            Create an image
          </button>
          <button className="chip">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20h9"/>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
            </svg>
            Write or edit
          </button>
          <button className="chip">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="2" y1="12" x2="22" y2="12"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
            </svg>
            Look something up
          </button>
        </div>

        {/* Model Selector */}
        <div className="input-model-selector">
          <button
            className="model-trigger-btn"
            onClick={() => setIsModelOpen(!isModelOpen)}
            type="button"
          >
            {selectedModelObj && selectedModelObj.provider === 'ollama' ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
                <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
                <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
                <line x1="6" y1="6" x2="6.01" y2="6" strokeWidth="3" />
                <line x1="6" y1="18" x2="6.01" y2="18" strokeWidth="3" />
              </svg>
            ) : selectedModelObj && selectedModelObj.provider === 'groq' ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
                <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />
              </svg>
            ) : null}
            <span>{selectedModelLabel}</span>
            <svg className={`chevron ${isModelOpen ? 'open' : ''}`} width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
          {isModelOpen && (
            <div className="model-menu">
              {AVAILABLE_MODELS.map(model => (
                <button
                  key={model.id}
                  className={`model-menu-item ${selectedModel === model.id ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedModel(model.id)
                    setIsModelOpen(false)
                  }}
                >
                  <span style={{ marginRight: '8px', display: 'flex', alignItems: 'center' }}>
                    {model.provider === 'ollama' ? (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
                        <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
                        <line x1="6" y1="6" x2="6.01" y2="6" strokeWidth="3" />
                        <line x1="6" y1="18" x2="6.01" y2="18" strokeWidth="3" />
                      </svg>
                    ) : (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />
                      </svg>
                    )}
                  </span>
                  {model.label}
                  {selectedModel === model.id && (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: 'auto' }}>
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ChatInput
