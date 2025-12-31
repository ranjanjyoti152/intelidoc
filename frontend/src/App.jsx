import { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

// Icons as simple SVG components
const Icons = {
  MessageSquare: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  ),
  Plus: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  ),
  Send: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  ),
  Paperclip: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </svg>
  ),
  Upload: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  ),
  FileText: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" />
    </svg>
  ),
  Trash: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  ),
  X: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  Folder: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  ),
  Bot: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="10" rx="2" /><circle cx="12" cy="5" r="2" /><path d="M12 7v4" /><line x1="8" y1="16" x2="8" y2="16" /><line x1="16" y1="16" x2="16" y2="16" />
    </svg>
  ),
  User: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
    </svg>
  ),
  Sparkles: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
    </svg>
  ),
  Search: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  ),
  BookOpen: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  ),
  Loader: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="spin">
      <line x1="12" y1="2" x2="12" y2="6" /><line x1="12" y1="18" x2="12" y2="22" /><line x1="4.93" y1="4.93" x2="7.76" y2="7.76" /><line x1="16.24" y1="16.24" x2="19.07" y2="19.07" /><line x1="2" y1="12" x2="6" y2="12" /><line x1="18" y1="12" x2="22" y2="12" /><line x1="4.93" y1="19.07" x2="7.76" y2="16.24" /><line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
    </svg>
  ),
  Check: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  AlertCircle: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
};

const API_BASE = 'http://localhost:8000';

// Generate unique ID
const generateId = () => Math.random().toString(36).substr(2, 9);

// Format date
const formatDate = (date) => {
  const d = new Date(date);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const formatTime = (date) => {
  const d = new Date(date);
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
};

function App() {
  // State
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [pendingFiles, setPendingFiles] = useState([]);
  const [showDocsModal, setShowDocsModal] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [processingDocs, setProcessingDocs] = useState(new Map()); // Track processing documents

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  // Load chats from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('intelidoc-chats');
    if (saved) {
      const parsed = JSON.parse(saved);
      setChats(parsed);
      if (parsed.length > 0) {
        setCurrentChatId(parsed[0].id);
        setMessages(parsed[0].messages || []);
      }
    }
  }, []);

  // Save chats to localStorage
  useEffect(() => {
    if (chats.length > 0) {
      localStorage.setItem('intelidoc-chats', JSON.stringify(chats));
    }
  }, [chats]);

  // Scroll to bottom when new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  // Fetch documents
  const fetchDocuments = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/documents`);
      const data = await res.json();
      setDocuments(data.documents || []);
      return data.documents || [];
    } catch (err) {
      console.error('Failed to fetch documents:', err);
      return [];
    }
  }, []);

  // Poll for document processing status
  const pollDocumentStatus = useCallback(async (docId, filename) => {
    const maxAttempts = 60; // 5 minutes max (5s intervals)
    let attempts = 0;

    const poll = async () => {
      attempts++;
      try {
        const res = await fetch(`${API_BASE}/documents/${docId}`);
        if (!res.ok) return;

        const doc = await res.json();

        // Update processing state
        setProcessingDocs(prev => {
          const newMap = new Map(prev);
          if (doc.status === 'completed') {
            newMap.delete(docId);
          } else if (doc.status === 'failed') {
            newMap.set(docId, { ...newMap.get(docId), status: 'failed', error: doc.error_message });
          } else {
            newMap.set(docId, {
              ...newMap.get(docId),
              status: doc.status,
              progress: doc.status === 'processing' ? 50 : 20
            });
          }
          return newMap;
        });

        // Continue polling if still processing
        if (doc.status === 'pending' || doc.status === 'processing') {
          if (attempts < maxAttempts) {
            setTimeout(poll, 5000);
          }
        } else {
          // Refresh documents list
          fetchDocuments();
        }
      } catch (err) {
        console.error('Poll error:', err);
      }
    };

    poll();
  }, [fetchDocuments]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Create new chat
  const createNewChat = () => {
    const newChat = {
      id: generateId(),
      title: 'New Chat',
      createdAt: new Date().toISOString(),
      messages: [],
    };
    setChats([newChat, ...chats]);
    setCurrentChatId(newChat.id);
    setMessages([]);
    return newChat.id;
  };

  // Select chat
  const selectChat = (chatId) => {
    setCurrentChatId(chatId);
    const chat = chats.find(c => c.id === chatId);
    setMessages(chat?.messages || []);
  };

  // Delete chat
  const deleteChat = (e, chatId) => {
    e.stopPropagation();
    const filtered = chats.filter(c => c.id !== chatId);
    setChats(filtered);
    if (currentChatId === chatId) {
      if (filtered.length > 0) {
        setCurrentChatId(filtered[0].id);
        setMessages(filtered[0].messages || []);
      } else {
        setCurrentChatId(null);
        setMessages([]);
      }
    }
  };

  // Update chat messages
  const updateChatMessages = useCallback((newMessages, chatId = null) => {
    const targetChatId = chatId || currentChatId;
    setMessages(newMessages);
    setChats(prev => prev.map(chat => {
      if (chat.id === targetChatId) {
        // Update title from first user message if still "New Chat"
        let title = chat.title;
        if (title === 'New Chat' && newMessages.length > 0) {
          const firstUserMsg = newMessages.find(m => m.role === 'user');
          if (firstUserMsg) {
            title = firstUserMsg.content.slice(0, 50) + (firstUserMsg.content.length > 50 ? '...' : '');
          }
        }
        return { ...chat, messages: newMessages, title };
      }
      return chat;
    }));
  }, [currentChatId]);

  // Handle file selection
  const handleFileSelect = async (files) => {
    const fileArray = Array.from(files);

    for (const file of fileArray) {
      const fileId = generateId();

      // Add to pending with uploading state
      setPendingFiles(prev => [...prev, {
        id: fileId,
        name: file.name,
        status: 'uploading',
        progress: 10,
      }]);

      try {
        // Upload file
        const formData = new FormData();
        formData.append('file', file);

        setPendingFiles(prev => prev.map(p =>
          p.id === fileId ? { ...p, progress: 30 } : p
        ));

        const res = await fetch(`${API_BASE}/documents/upload`, {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) {
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Upload failed');
        }

        const uploadResult = await res.json();

        // Update pending file to processing state
        setPendingFiles(prev => prev.map(p =>
          p.id === fileId ? {
            ...p,
            status: 'processing',
            progress: 50,
            docId: uploadResult.document_id
          } : p
        ));

        // Add to processing docs for global tracking
        setProcessingDocs(prev => {
          const newMap = new Map(prev);
          newMap.set(uploadResult.document_id, {
            name: file.name,
            status: 'processing',
            progress: 50
          });
          return newMap;
        });

        // Start polling for status
        pollDocumentStatus(uploadResult.document_id, file.name);

        // Remove from pending after a delay
        setTimeout(() => {
          setPendingFiles(prev => prev.filter(p => p.id !== fileId));
        }, 2000);

      } catch (err) {
        console.error('Upload error:', err);
        setPendingFiles(prev => prev.map(p =>
          p.id === fileId ? { ...p, status: 'error', error: err.message } : p
        ));
      }
    }
  };

  // Remove pending file
  const removePendingFile = (id) => {
    setPendingFiles(pendingFiles.filter(f => f.id !== id));
  };

  // Check if documents are ready for querying
  const hasCompletedDocuments = documents.some(d => d.status === 'completed');

  // Send message
  const sendMessage = async () => {
    if (!input.trim()) return;
    if (isLoading) return;

    // Create chat if none exists
    let chatId = currentChatId;
    if (!chatId) {
      chatId = createNewChat();
    }

    const userMessage = {
      id: generateId(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    const newMessages = [...messages, userMessage];
    updateChatMessages(newMessages, chatId);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: input,
          top_k: 5,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Query failed');
      }

      const data = await res.json();

      const assistantMessage = {
        id: generateId(),
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        model: data.model_used,
        timestamp: new Date().toISOString(),
      };

      updateChatMessages([...newMessages, assistantMessage], chatId);
    } catch (err) {
      console.error('Query error:', err);
      let errorContent = 'Sorry, I encountered an error processing your request.';

      if (!hasCompletedDocuments) {
        errorContent = 'No documents have been processed yet. Please upload and wait for documents to finish processing before asking questions.';
      } else {
        errorContent += `\n\nError: ${err.message}`;
      }

      const errorMessage = {
        id: generateId(),
        role: 'assistant',
        content: errorContent,
        timestamp: new Date().toISOString(),
      };
      updateChatMessages([...newMessages, errorMessage], chatId);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Drag and drop handlers
  const handleDragEnter = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length) handleFileSelect(files);
  };

  // Delete document
  const deleteDocument = async (id) => {
    try {
      await fetch(`${API_BASE}/documents/${id}`, { method: 'DELETE' });
      fetchDocuments();
    } catch (err) {
      console.error('Delete error:', err);
    }
  };

  // Get status color class
  const getStatusClass = (status) => {
    switch (status) {
      case 'completed': return 'completed';
      case 'processing': return 'processing';
      case 'pending': return 'pending';
      case 'failed': return 'failed';
      default: return 'pending';
    }
  };

  // Get status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <Icons.Check />;
      case 'processing': return <Icons.Loader />;
      case 'pending': return <Icons.Loader />;
      case 'failed': return <Icons.AlertCircle />;
      default: return <Icons.Loader />;
    }
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={createNewChat}>
            <Icons.Plus /> New Chat
          </button>
        </div>

        {/* Processing Documents Banner */}
        {processingDocs.size > 0 && (
          <div className="processing-banner">
            <div className="processing-banner-title">
              <Icons.Loader /> Processing Documents
            </div>
            {Array.from(processingDocs.entries()).map(([id, doc]) => (
              <div key={id} className="processing-item">
                <span className="processing-name">{doc.name}</span>
                <div className="processing-bar">
                  <div className="processing-bar-fill" style={{ width: `${doc.progress}%` }} />
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="chat-list">
          {chats.map(chat => (
            <div
              key={chat.id}
              className={`chat-item ${chat.id === currentChatId ? 'active' : ''}`}
              onClick={() => selectChat(chat.id)}
            >
              <span className="chat-item-icon"><Icons.MessageSquare /></span>
              <div className="chat-item-content">
                <div className="chat-item-title">{chat.title}</div>
                <div className="chat-item-date">{formatDate(chat.createdAt)}</div>
              </div>
              <button className="chat-item-delete" onClick={(e) => deleteChat(e, chat.id)}>
                <Icons.Trash />
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Header */}
        <header className="header">
          <h1 className="header-title">
            <Icons.Sparkles /> InteliDoc
          </h1>
          <div className="header-actions">
            <button className="header-btn" onClick={() => { setShowDocsModal(true); fetchDocuments(); }}>
              <Icons.Folder /> Documents ({documents.filter(d => d.status === 'completed').length})
            </button>
          </div>
        </header>

        {/* Chat Container */}
        <div
          className="chat-container"
          onDragEnter={handleDragEnter}
          onDragOver={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-icon">
                <Icons.Sparkles />
              </div>
              <h2 className="welcome-title">Welcome to InteliDoc</h2>
              <p className="welcome-subtitle">
                Upload your documents and ask questions. I'll help you find answers using AI-powered document understanding.
              </p>

              {/* Upload prompt if no documents */}
              {documents.length === 0 && (
                <div className="upload-prompt" onClick={() => fileInputRef.current?.click()}>
                  <Icons.Upload />
                  <span>Click here or drag files to upload your first document</span>
                </div>
              )}

              <div className="welcome-features">
                <div className="feature-card">
                  <div className="feature-icon"><Icons.Upload /></div>
                  <div className="feature-title">Upload Documents</div>
                  <div className="feature-desc">PDF, DOCX, TXT, HTML and more</div>
                </div>
                <div className="feature-card">
                  <div className="feature-icon"><Icons.Search /></div>
                  <div className="feature-title">Ask Questions</div>
                  <div className="feature-desc">Natural language queries</div>
                </div>
                <div className="feature-card">
                  <div className="feature-icon"><Icons.BookOpen /></div>
                  <div className="feature-title">Get Answers</div>
                  <div className="feature-desc">AI-powered with sources</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map(msg => (
                <div key={msg.id} className="message">
                  <div className={`message-avatar ${msg.role}`}>
                    {msg.role === 'user' ? <Icons.User /> : <Icons.Bot />}
                  </div>
                  <div className="message-content">
                    <div className="message-header">
                      <span className="message-role">{msg.role === 'user' ? 'You' : 'InteliDoc'}</span>
                      <span className="message-time">{formatTime(msg.timestamp)}</span>
                      {msg.model && <span className="message-model">{msg.model}</span>}
                    </div>
                    <div className="message-text">
                      {msg.content.split('\n').map((line, i) => (
                        <p key={i}>{line || '\u00A0'}</p>
                      ))}
                    </div>
                    {msg.sources?.length > 0 && (
                      <div className="message-sources">
                        <div className="sources-title"><Icons.BookOpen /> Sources</div>
                        <div className="source-list">
                          {msg.sources.map((src, i) => (
                            <span key={i} className="source-chip">
                              <Icons.FileText />
                              {src.document_filename}
                              {src.page_number && ` (p.${src.page_number})`}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="message">
                  <div className="message-avatar assistant">
                    <Icons.Bot />
                  </div>
                  <div className="message-content">
                    <div className="typing-indicator">
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="input-area">
          <div className="input-wrapper">
            {/* Drop zone overlay */}
            {isDragging && (
              <div className="upload-zone dragging">
                <div className="upload-zone-content">
                  <span className="upload-icon"><Icons.Upload /></span>
                  <span className="upload-text">Drop files here to upload</span>
                </div>
              </div>
            )}

            {/* Pending files */}
            {pendingFiles.length > 0 && (
              <div className="pending-files">
                {pendingFiles.map(file => (
                  <div key={file.id} className={`pending-file ${file.status}`}>
                    {file.status === 'uploading' && <Icons.Loader />}
                    {file.status === 'processing' && <Icons.Loader />}
                    {file.status === 'complete' && <Icons.Check />}
                    {file.status === 'error' && <Icons.AlertCircle />}
                    <span>{file.name}</span>
                    {(file.status === 'uploading' || file.status === 'processing') && (
                      <div className="pending-file-progress">
                        <div className="pending-file-progress-bar" style={{ width: `${file.progress}%` }} />
                      </div>
                    )}
                    {file.status === 'error' && (
                      <button className="pending-file-remove" onClick={() => removePendingFile(file.id)}>
                        <Icons.X />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Input container */}
            <div className="input-container">
              <button className="attach-btn" onClick={() => fileInputRef.current?.click()}>
                <Icons.Paperclip />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.txt,.md,.html"
                style={{ display: 'none' }}
                onChange={(e) => handleFileSelect(e.target.files)}
              />
              <textarea
                ref={textareaRef}
                className="input-field"
                placeholder={hasCompletedDocuments
                  ? "Ask a question about your documents..."
                  : "Upload documents first, then ask questions..."}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                rows={1}
              />
              <button
                className="send-btn"
                onClick={sendMessage}
                disabled={isLoading || !input.trim()}
              >
                <Icons.Send />
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Documents Modal */}
      {showDocsModal && (
        <div className="modal-overlay" onClick={() => setShowDocsModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Your Documents</h2>
              <button className="modal-close" onClick={() => setShowDocsModal(false)}>
                <Icons.X />
              </button>
            </div>
            <div className="modal-body">
              {/* Upload zone in modal */}
              <div
                className="upload-zone"
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="upload-zone-content">
                  <span className="upload-icon"><Icons.Upload /></span>
                  <span className="upload-text">Click or drag files to upload</span>
                  <span className="upload-hint">PDF, DOCX, TXT, HTML, MD</span>
                </div>
              </div>

              {documents.length === 0 ? (
                <div className="empty-state">
                  <Icons.Folder />
                  <p>No documents uploaded yet</p>
                </div>
              ) : (
                <div className="document-list">
                  {documents.map(doc => (
                    <div key={doc.id} className="document-item">
                      <div className="document-icon"><Icons.FileText /></div>
                      <div className="document-info">
                        <div className="document-name">{doc.original_filename}</div>
                        <div className="document-meta">
                          {doc.status === 'completed' && <span>{doc.chunk_count || 0} chunks</span>}
                          <span>{formatDate(doc.created_at)}</span>
                        </div>
                      </div>
                      <span className={`document-status ${getStatusClass(doc.status)}`}>
                        {getStatusIcon(doc.status)}
                        {doc.status}
                      </span>
                      <button className="document-delete" onClick={() => deleteDocument(doc.id)}>
                        <Icons.Trash />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
