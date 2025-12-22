import React, { useState, useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { ChatArea } from './ChatArea';
import { sessions as sessionApi } from '../api/client';

// Types duplicated here for simplicity or export them in a shared file
interface ChatSession { session_id: string; title: string; created_at: string; }
interface Message { role: 'user' | 'assistant'; content: string; }
interface UploadedFile { file_id: string; filename: string; }

const WELCOME_MSG: Message = {
  role: 'assistant',
  content: "👋 **Hello! I am your Legal AI Assistant.**\n\nI can help you:\n* 📄 **Analyze** contracts and documents\n* ⚖️ **Check** regulatory compliance\n* 🔍 **Answer** complex legal queries\n\n**Upload a document** or **type a question** to get started!"
};

export const Dashboard = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([WELCOME_MSG]);
  const [files, setFiles] = useState<UploadedFile[]>([]);

  useEffect(() => {
    sessionApi.list().then(res => setSessions(res.data)).catch(console.error);
  }, []);

  const handleSelectSession = async (id: string) => {
    setCurrentSessionId(id);
    try {
      const [histRes, fileRes] = await Promise.all([
        sessionApi.getHistory(id),
        sessionApi.getFiles(id)
      ]);
      setMessages(histRes.data.messages.length > 0 ? histRes.data.messages : [WELCOME_MSG]);
      setFiles(fileRes.data);
    } catch (e) { console.error(e); }
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([WELCOME_MSG]);
    setFiles([]);
  };

  return (
    <div className="flex h-screen bg-gray-50 font-sans text-gray-900">
      <Sidebar 
        sessions={sessions} 
        currentSessionId={currentSessionId} 
        onSelectSession={handleSelectSession} 
        onNewChat={handleNewChat}
        setSessions={setSessions}
      />
      <ChatArea 
        currentSessionId={currentSessionId}
        setCurrentSessionId={setCurrentSessionId}
        sessions={sessions}
        setSessions={setSessions}
        messages={messages}
        setMessages={setMessages}
        files={files}
        setFiles={setFiles}
      />
    </div>
  );
};