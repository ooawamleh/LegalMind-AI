import React, { useRef, useEffect, useState } from 'react';
import { Send, Upload, Loader2, FileText, Edit2, RefreshCw, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { sessions as sessionApi, documents as docApi, API_BASE } from '../api/client';

// Types
interface Message { role: 'user' | 'assistant'; content: string; }
interface UploadedFile { file_id: string; filename: string; }
interface ChatSession { session_id: string; title: string; created_at: string; }

const WELCOME_MSG: Message = {
  role: 'assistant',
  content: "👋 **Hello! I am your Legal AI Assistant.**\n\nI can help you:\n* 📄 **Analyze** contracts and documents\n* ⚖️ **Check** regulatory compliance\n* 🔍 **Answer** complex legal queries\n\n**Upload a document** or **type a question** to get started!"
};

interface ChatAreaProps {
  currentSessionId: string | null;
  setCurrentSessionId: (id: string) => void;
  sessions: ChatSession[];
  setSessions: React.Dispatch<React.SetStateAction<ChatSession[]>>;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  files: UploadedFile[];
  setFiles: React.Dispatch<React.SetStateAction<UploadedFile[]>>;
}

export const ChatArea: React.FC<ChatAreaProps> = ({ 
  currentSessionId, setCurrentSessionId, sessions, setSessions, messages, setMessages, files, setFiles 
}) => {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [editingMsgIndex, setEditingMsgIndex] = useState<number | null>(null);
  const [editInput, setEditInput] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, isLoading]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (!selectedFiles?.length) return;

    let targetId = currentSessionId;
    if (!targetId) {
      try {
        const res = await sessionApi.create("New Chat");
        targetId = res.data.session_id;
        setCurrentSessionId(targetId);
        setSessions([res.data, ...sessions]);
      } catch (err) { alert("Failed to start session"); return; }
    }

    setIsUploading(true);
    try {
      const res = await docApi.upload(selectedFiles, targetId!);
      const newFiles = res.data.uploaded
        .filter((u: any) => u.status === 'Success')
        .map((u: any) => ({ file_id: u.file_id, filename: u.filename }));
      setFiles(prev => [...prev, ...newFiles]);
      setMessages(prev => [...prev, { role: 'assistant', content: `✅ **System:** Successfully uploaded ${newFiles.length} document(s).` }]);
    } catch (err) { alert("Upload failed"); } 
    finally { setIsUploading(false); if (fileInputRef.current) fileInputRef.current.value = ''; }
  };

  const handleDeleteFile = async (fileId: string) => {
    if (!currentSessionId || !confirm("Remove this file?")) return;
    try {
      await sessionApi.deleteFile(currentSessionId, fileId);
      setFiles(prev => prev.filter(f => f.file_id !== fileId));
    } catch (e) { alert("Failed to delete"); }
  };

  const streamResponse = async (query: string, sessionId: string) => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ query, session_id: sessionId })
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let aiText = "";

    setMessages(prev => [...prev, { role: 'assistant', content: "" }]);

    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      aiText += chunk;
      setMessages(prev => {
        const newMsg = [...prev];
        newMsg[newMsg.length - 1].content = aiText;
        return newMsg;
      });
    }
    setIsLoading(false);
  };

  const handleSend = async (e?: React.FormEvent, overrideText?: string) => {
    e?.preventDefault();
    const textToSend = overrideText || input;
    if (!textToSend.trim() || isLoading) return;

    let targetId = currentSessionId;
    let isFirstMessage = false;

    if (!targetId) {
      isFirstMessage = true;
      try {
        const res = await sessionApi.create("New Chat");
        targetId = res.data.session_id;
        setCurrentSessionId(targetId);
        setSessions([res.data, ...sessions]);
      } catch (err) { console.error(err); return; }
    } else if (messages.length === 0 || (messages.length === 1 && messages[0].content === WELCOME_MSG.content)) {
      isFirstMessage = true;
    }

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: textToSend }]);
    setIsLoading(true);

    if (isFirstMessage && targetId) {
       sessionApi.autoTitle(targetId, textToSend)
         .then(res => setSessions(prev => prev.map(s => s.session_id === targetId ? { ...s, title: res.data.title } : s)));
    }

    try { if (targetId) await streamResponse(textToSend, targetId); } 
    catch (err) { setMessages(prev => [...prev, { role: 'assistant', content: "❌ Error connecting to server." }]); setIsLoading(false); }
  };

  // Edit & Regenerate
  const submitEdit = (index: number) => {
    const newHistory = messages.slice(0, index);
    setMessages(newHistory);
    setEditingMsgIndex(null);
    handleSend(undefined, editInput);
  };

  const handleRegenerate = () => {
    if (messages.length < 2) return;
    const lastUserMsg = messages[messages.length - 2]; 
    setMessages(prev => prev.slice(0, -1));
    setIsLoading(true);
    if (currentSessionId) streamResponse(lastUserMsg.content, currentSessionId);
  };

  return (
    <div className="flex-1 flex flex-col h-screen min-w-0 bg-gray-50">
      {/* File Cards */}
      {files.length > 0 && (
        <div className="bg-white border-b p-3 flex gap-3 overflow-x-auto">
          {files.map(f => (
            <div key={f.file_id} className="flex items-center gap-2 bg-gray-100 px-3 py-1.5 rounded-md border text-sm min-w-max">
              <FileText size={14} className="text-indigo-600"/> <span className="truncate max-w-[150px]">{f.filename}</span>
              <X size={14} className="cursor-pointer text-gray-400 hover:text-red-500" onClick={() => handleDeleteFile(f.file_id)} />
            </div>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`group flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] relative ${m.role === 'user' ? 'items-end flex flex-col' : ''}`}>
              <div className={`rounded-lg p-4 shadow-sm ${m.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-white border'}`}>
                {editingMsgIndex === i ? (
                  <div className="flex flex-col gap-2 min-w-[300px]">
                    <textarea className="text-black p-2 rounded text-sm" rows={3} value={editInput} onChange={e => setEditInput(e.target.value)}/>
                    <div className="flex gap-2 justify-end">
                      <button className="text-xs hover:underline" onClick={() => setEditingMsgIndex(null)}>Cancel</button>
                      <button className="text-xs bg-white text-indigo-600 px-2 py-1 rounded font-bold" onClick={() => submitEdit(i)}>Save</button>
                    </div>
                  </div>
                ) : (
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                  </div>
                )}
              </div>
              <div className={`flex gap-2 mt-1 opacity-0 group-hover:opacity-100 transition-opacity ${m.role === 'user' ? 'justify-end text-gray-400' : 'text-gray-400'}`}>
                {m.role === 'user' && !isLoading && <button onClick={() => { setEditingMsgIndex(i); setEditInput(m.content); }}><Edit2 size={12}/></button>}
                {m.role === 'assistant' && i === messages.length - 1 && !isLoading && <button onClick={handleRegenerate} className="flex items-center gap-1 text-xs"><RefreshCw size={12}/> Regen</button>}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-white border-t">
        <form onSubmit={(e) => handleSend(e)} className="flex items-end gap-2 max-w-4xl mx-auto">
          <input type="file" ref={fileInputRef} className="hidden" multiple onChange={handleUpload} />
          <button type="button" onClick={() => fileInputRef.current?.click()} disabled={isUploading || isLoading} className="p-3 bg-gray-100 rounded-lg hover:text-indigo-600">
            {isUploading ? <Loader2 className="animate-spin" size={20}/> : <Upload size={20}/>}
          </button>
          <textarea value={input} onChange={e => setInput(e.target.value)} placeholder="Type a message..." className="flex-1 p-3 rounded-lg border outline-none resize-none" rows={1} disabled={isLoading} onKeyDown={e => { if(e.key==='Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }}} />
          <button type="submit" disabled={!input.trim() || isLoading} className="p-3 bg-indigo-600 text-white rounded-lg">
            {isLoading ? <Loader2 className="animate-spin" size={20}/> : <Send size={20}/>}
          </button>
        </form>
      </div>
    </div>
  );
};