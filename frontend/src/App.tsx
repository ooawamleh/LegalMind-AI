// frontend/src/App.tsx
import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { 
  Plus, MessageSquare, Trash2, LogOut, Send, Upload, Loader2, 
  FileText, Edit2, RefreshCw, X, MoreVertical, Check 
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { auth, sessions as sessionApi, documents as docApi, API_BASE } from './api/client';

// --- TYPES ---
interface ChatSession { session_id: string; title: string; created_at: string; }
interface Message { role: 'user' | 'assistant'; content: string; }
interface UploadedFile { file_id: string; filename: string; }

// --- CONSTANTS (NEW) ---
const WELCOME_MSG: Message = {
  role: 'assistant',
  content: "👋 **Hello! I am your Legal AI Assistant.**\n\nI can help you:\n* 📄 **Analyze** contracts and documents\n* ⚖️ **Check** regulatory compliance\n* 🔍 **Answer** complex legal queries\n\n**Upload a document** or **type a question** to get started!"
};

// --- DASHBOARD ---
const Dashboard = () => {
  // State
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  
  // CHANGE 1: Initialize with Welcome Message
  const [messages, setMessages] = useState<Message[]>([WELCOME_MSG]);
  
  const [files, setFiles] = useState<UploadedFile[]>([]); 
  
  // UI State
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [editingMsgIndex, setEditingMsgIndex] = useState<number | null>(null);
  const [editInput, setEditInput] = useState('');
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameInput, setRenameInput] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initial Load
  useEffect(() => {
    loadSessions();
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const loadSessions = () => sessionApi.list().then(res => setSessions(res.data)).catch(console.error);

  // --- SESSION MANAGEMENT ---

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([WELCOME_MSG]); // CHANGE 2: Reset to Welcome Message
    setFiles([]);
    setInput('');
  };

  const handleSelectSession = async (id: string) => {
    setCurrentSessionId(id);
    setIsLoading(true);
    try {
      const [histRes, fileRes] = await Promise.all([
        sessionApi.getHistory(id),
        sessionApi.getFiles(id)
      ]);
      // CHANGE 3: If history is empty, show welcome message
      setMessages(histRes.data.messages.length > 0 ? histRes.data.messages : [WELCOME_MSG]);
      setFiles(fileRes.data);
    } catch (e) { console.error(e); } 
    finally { setIsLoading(false); }
  };

  const handleRenameSession = async (id: string) => {
    if (!renameInput.trim()) return;
    try {
      await sessionApi.rename(id, renameInput);
      setSessions(prev => prev.map(s => s.session_id === id ? { ...s, title: renameInput } : s));
      setRenamingId(null);
    } catch (e) { console.error(e); }
  };

  // --- FILE MANAGEMENT ---

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (!selectedFiles?.length) return;

    let targetSessionId = currentSessionId;

    // If new chat, create session first (using "New Chat" as placeholder title)
    if (!targetSessionId) {
      try {
        const res = await sessionApi.create("New Chat");
        targetSessionId = res.data.session_id;
        setCurrentSessionId(targetSessionId);
        setSessions([res.data, ...sessions]);
      } catch (err) { alert("Failed to start session"); return; }
    }

    setIsUploading(true);
    try {
      const res = await docApi.upload(selectedFiles, targetSessionId);
      // Backend returns list of results, we map them to file objects
      const newFiles = res.data.uploaded
        .filter((u: any) => u.status === 'Success')
        .map((u: any) => ({ file_id: u.file_id, filename: u.filename }));
      
      setFiles(prev => [...prev, ...newFiles]);
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `✅ **System:** Successfully uploaded ${newFiles.length} document(s).` 
      }]);
    } catch (err) { alert("Upload failed"); } 
    finally { 
      setIsUploading(false); 
      if (fileInputRef.current) fileInputRef.current.value = ''; 
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    if (!currentSessionId || !confirm("Remove this file? It will be deleted from the AI's context.")) return;
    try {
      await sessionApi.deleteFile(currentSessionId, fileId);
      setFiles(prev => prev.filter(f => f.file_id !== fileId));
    } catch (e) { alert("Failed to delete file"); }
  };

  // --- MESSAGING LOGIC ---

  const handleSend = async (e?: React.FormEvent, overrideText?: string) => {
    e?.preventDefault();
    const textToSend = overrideText || input;
    if (!textToSend.trim() || isLoading) return;

    let targetId = currentSessionId;
    let isFirstMessage = false; 

    // 1. Auto-Create Session if New
    if (!targetId) {
      isFirstMessage = true;
      try {
        const res = await sessionApi.create("New Chat");
        targetId = res.data.session_id;
        setCurrentSessionId(targetId);
        setSessions([res.data, ...sessions]);
      } catch (err) { console.error(err); return; }
    } 
    // CHANGE 4: Check if current view is just the welcome message
    else if (messages.length === 0 || (messages.length === 1 && messages[0] === WELCOME_MSG)) {
      isFirstMessage = true;
    }

    // 2. Clear Input & Optimistic UI
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: textToSend }]);
    setIsLoading(true);

    // 3. SMART RENAME TRIGGER (Fire & Forget)
    if (isFirstMessage && targetId) {
       sessionApi.autoTitle(targetId, textToSend)
         .then(res => {
            setSessions(prev => prev.map(s => s.session_id === targetId ? { ...s, title: res.data.title } : s));
         })
         .catch(err => console.error("Auto-title failed", err));
    }

    // 4. Stream Response
    try {
      if (targetId) await streamResponse(textToSend, targetId);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: "❌ Error connecting to server." }]);
      setIsLoading(false);
    }
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

  // --- EDIT & REGENERATE ---

  const handleEditMessage = (index: number) => {
    setEditingMsgIndex(index);
    setEditInput(messages[index].content);
  };

  const submitEdit = (index: number) => {
    const newHistory = messages.slice(0, index);
    setMessages(newHistory);
    setEditingMsgIndex(null);
    handleSend(undefined, editInput);
  };

  const handleRegenerate = () => {
    if (messages.length < 2) return;
    const lastUserMsg = messages[messages.length - 2]; 
    if (lastUserMsg.role !== 'user') return; 

    setMessages(prev => prev.slice(0, -1));
    setIsLoading(true);
    if (currentSessionId) streamResponse(lastUserMsg.content, currentSessionId);
  };

  return (
    <div className="flex h-screen bg-gray-50 font-sans text-gray-900">
      
      {/* SIDEBAR */}
      <div className="w-64 bg-indigo-900 text-white flex flex-col border-r border-indigo-800 flex-shrink-0">
        <div className="p-4">
          <h1 className="text-xl font-bold mb-4 flex items-center gap-2">⚖️ Legal AI</h1>
          <button onClick={handleNewChat} className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 p-2 rounded transition">
            <Plus size={18} /> New Chat
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {sessions.map(s => (
            <div key={s.session_id} onClick={() => handleSelectSession(s.session_id)} 
              className={`group flex items-center justify-between p-3 rounded cursor-pointer ${currentSessionId === s.session_id ? 'bg-indigo-800' : 'hover:bg-indigo-800/50'}`}>
              
              {/* Rename Logic */}
              {renamingId === s.session_id ? (
                <div className="flex items-center flex-1 gap-1" onClick={e => e.stopPropagation()}>
                  <input autoFocus className="w-full text-black text-xs p-1 rounded" 
                    value={renameInput} onChange={e => setRenameInput(e.target.value)} 
                    onKeyDown={e => e.key === 'Enter' && handleRenameSession(s.session_id)}
                  />
                  <Check size={14} className="hover:text-green-300 cursor-pointer" onClick={() => handleRenameSession(s.session_id)} />
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-2 overflow-hidden">
                    <MessageSquare size={16} className="flex-shrink-0"/> 
                    <span className="truncate text-sm">{s.title}</span>
                  </div>
                  <div className="hidden group-hover:flex gap-1">
                    <Edit2 size={12} className="hover:text-indigo-300" onClick={(e) => { e.stopPropagation(); setRenamingId(s.session_id); setRenameInput(s.title); }}/>
                    <Trash2 size={12} className="hover:text-red-400" onClick={(e) => { e.stopPropagation(); sessionApi.delete(s.session_id).then(() => setSessions(prev => prev.filter(x => x.session_id !== s.session_id))); }}/>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
        
        <div className="p-4 border-t border-indigo-800">
          <button onClick={() => { localStorage.removeItem('token'); window.location.href = '/login'; }} className="flex items-center gap-2 text-indigo-300 hover:text-white w-full">
            <LogOut size={18} /> Sign Out
          </button>
        </div>
      </div>

      {/* MAIN CHAT AREA */}
      <div className="flex-1 flex flex-col h-screen min-w-0">
        
        {/* Header / File Cards */}
        {files.length > 0 && (
          <div className="bg-white border-b p-3 flex gap-3 overflow-x-auto">
            {files.map(f => (
              <div key={f.file_id} className="flex items-center gap-2 bg-gray-100 px-3 py-1.5 rounded-md border text-sm min-w-max">
                <FileText size={14} className="text-indigo-600"/>
                <span className="truncate max-w-[150px]">{f.filename}</span>
                <X size={14} className="cursor-pointer text-gray-400 hover:text-red-500" onClick={() => handleDeleteFile(f.file_id)} />
              </div>
            ))}
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* CHANGE 5: Removed the "messages.length === 0" conditional div completely */}
          {messages.map((m, i) => (
            <div key={i} className={`group flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] relative ${m.role === 'user' ? 'items-end flex flex-col' : ''}`}>
                
                {/* Message Bubble */}
                <div className={`rounded-lg p-4 shadow-sm ${m.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-white border'}`}>
                  {editingMsgIndex === i ? (
                    <div className="flex flex-col gap-2 min-w-[300px]">
                      <textarea className="text-black p-2 rounded text-sm" rows={3} value={editInput} onChange={e => setEditInput(e.target.value)}/>
                      <div className="flex gap-2 justify-end">
                        <button className="text-xs hover:underline" onClick={() => setEditingMsgIndex(null)}>Cancel</button>
                        <button className="text-xs bg-white text-indigo-600 px-2 py-1 rounded font-bold" onClick={() => submitEdit(i)}>Save & Retry</button>
                      </div>
                    </div>
                  ) : (
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                    </div>
                  )}
                </div>

                {/* Actions (Hover) */}
                <div className={`flex gap-2 mt-1 opacity-0 group-hover:opacity-100 transition-opacity ${m.role === 'user' ? 'justify-end text-gray-400' : 'text-gray-400'}`}>
                  {m.role === 'user' && !isLoading && (
                    <button onClick={() => handleEditMessage(i)} title="Edit" className="hover:text-indigo-600"><Edit2 size={12}/></button>
                  )}
                  {m.role === 'assistant' && i === messages.length - 1 && !isLoading && (
                    <button onClick={handleRegenerate} title="Regenerate" className="hover:text-indigo-600 flex items-center gap-1 text-xs">
                      <RefreshCw size={12}/> Regenerate
                    </button>
                  )}
                </div>

              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white border-t">
          <form onSubmit={(e) => handleSend(e)} className="flex items-end gap-2 max-w-4xl mx-auto">
            <input type="file" ref={fileInputRef} className="hidden" multiple onChange={handleUpload} />
            <button type="button" onClick={() => fileInputRef.current?.click()} disabled={isUploading || isLoading} 
              className="p-3 text-gray-500 hover:text-indigo-600 bg-gray-100 rounded-lg transition-colors">
              {isUploading ? <Loader2 className="animate-spin" size={20}/> : <Upload size={20}/>}
            </button>
            <textarea 
              value={input} 
              onChange={e => setInput(e.target.value)} 
              placeholder={currentSessionId ? "Message..." : "Start a new chat..."}
              onKeyDown={e => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }}}
              className="flex-1 p-3 rounded-lg border focus:ring-2 focus:ring-indigo-500 outline-none resize-none max-h-32" 
              rows={1}
              disabled={isLoading}
            />
            <button type="submit" disabled={!input.trim() || isLoading} className="p-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
              {isLoading ? <Loader2 className="animate-spin" size={20}/> : <Send size={20}/>}
            </button>
          </form>
          <div className="text-center text-xs text-gray-400 mt-2">
            AI can make mistakes. Please review legal info.
          </div>
        </div>
      </div>
    </div>
  );
};

// --- LOGIN COMPONENT (Unchanged) ---
const Login = () => {
  const [isReg, setIsReg] = useState(false);
  const [creds, setCreds] = useState({u:'', p:''});
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if(isReg) { await auth.register(creds.u, creds.p); alert("Registered! Please login."); setIsReg(false); } 
      else { const res = await auth.login(creds.u, creds.p); localStorage.setItem('token', res.data.access_token); window.location.href = "/"; }
    } catch (err: any) { alert(err.response?.data?.detail || "Error"); }
  };
  return (
    <div className="h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded shadow-lg w-96">
        <h2 className="text-2xl font-bold mb-6 text-center text-indigo-900">{isReg ? "Register" : "Login"}</h2>
        <form onSubmit={submit} className="space-y-4">
          <input className="w-full border p-2 rounded" placeholder="Username" value={creds.u} onChange={e=>setCreds({...creds, u:e.target.value})} />
          <input className="w-full border p-2 rounded" type="password" placeholder="Password" value={creds.p} onChange={e=>setCreds({...creds, p:e.target.value})} />
          <button className="w-full bg-indigo-600 text-white p-2 rounded">{isReg ? "Sign Up" : "Sign In"}</button>
        </form>
        <button onClick={()=>setIsReg(!isReg)} className="w-full mt-4 text-indigo-600 text-sm">{isReg ? "Login instead" : "Create account"}</button>
      </div>
    </div>
  );
};

const PrivateRoute = ({ children }: { children: JSX.Element }) => {
  return localStorage.getItem('token') ? children : <Navigate to="/login" />;
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      </Routes>
    </BrowserRouter>
  );
}

// // frontend/src/App.tsx
// import React, { useState, useEffect, useRef } from 'react';
// import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
// import { Plus, MessageSquare, Trash2, LogOut, Send, Upload, Loader2, FileText } from 'lucide-react';
// import ReactMarkdown from 'react-markdown';
// import remarkGfm from 'remark-gfm';
// import { auth, sessions as sessionApi, documents as docApi, API_BASE } from './api/client';

// // --- TYPES ---
// interface ChatSession { session_id: string; title: string; created_at: string; }
// interface Message { role: 'user' | 'assistant'; content: string; }

// // --- MAIN DASHBOARD COMPONENT ---
// const Dashboard = () => {
//   const [sessions, setSessions] = useState<ChatSession[]>([]);
//   const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
//   const [messages, setMessages] = useState<Message[]>([]);
//   const [input, setInput] = useState('');
//   const [isLoading, setIsLoading] = useState(false);
//   const [isUploading, setIsUploading] = useState(false);
  
//   const messagesEndRef = useRef<HTMLDivElement>(null);
//   const fileInputRef = useRef<HTMLInputElement>(null);

//   // Load Sessions
//   useEffect(() => {
//     sessionApi.list().then(res => setSessions(res.data)).catch(console.error);
//   }, []);

//   // Scroll to bottom
//   useEffect(() => {
//     messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
//   }, [messages]);

//   const handleLogout = () => {
//     localStorage.removeItem('token');
//     window.location.href = '/login';
//   };

//   const handleSelectSession = async (id: string) => {
//     setCurrentSessionId(id);
//     setIsLoading(true);
//     try {
//       const res = await sessionApi.getHistory(id);
//       setMessages(res.data.messages);
//     } catch (e) { console.error(e); } 
//     finally { setIsLoading(false); }
//   };

//   const handleCreateSession = async () => {
//     try {
//       const res = await sessionApi.create(`New Chat ${new Date().toLocaleTimeString()}`);
//       setSessions([res.data, ...sessions]);
//       setCurrentSessionId(res.data.session_id);
//       setMessages([]);
//     } catch (e) { console.error(e); }
//   };

//   const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
//     e.stopPropagation();
//     if(!confirm("Delete this chat?")) return;
//     try {
//       await sessionApi.delete(id);
//       setSessions(sessions.filter(s => s.session_id !== id));
//       if(currentSessionId === id) { setCurrentSessionId(null); setMessages([]); }
//     } catch (e) { console.error(e); }
//   };

//   const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
//     if (!e.target.files?.length || !currentSessionId) return alert("Select a chat first!");
//     setIsUploading(true);
//     try {
//       const res = await docApi.upload(e.target.files, currentSessionId);
//       const count = res.data.uploaded.length;
//       setMessages(prev => [...prev, { role: 'assistant', content: `✅ **System:** Uploaded ${count} files.` }]);
//     } catch (err) { alert("Upload failed"); } 
//     finally { setIsUploading(false); if(fileInputRef.current) fileInputRef.current.value=''; }
//   };

//   const handleSend = async (e?: React.FormEvent) => {
//     e?.preventDefault();
//     if (!input.trim() || isLoading) return;

//     let sessionId = currentSessionId;
//     // Auto-create session if none exists
//     if (!sessionId) {
//       const res = await sessionApi.create(input.slice(0,30) + "...");
//       setSessions([res.data, ...sessions]);
//       sessionId = res.data.session_id;
//       setCurrentSessionId(sessionId);
//     }

//     const userMsg = input;
//     setInput('');
//     setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
//     setIsLoading(true);

//     try {
//       const token = localStorage.getItem('token');
//       const response = await fetch(`${API_BASE}/analyze`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
//         body: JSON.stringify({ query: userMsg, session_id: sessionId })
//       });

//       const reader = response.body?.getReader();
//       const decoder = new TextDecoder();
//       let aiText = "";

//       setMessages(prev => [...prev, { role: 'assistant', content: "" }]);

//       while (reader) {
//         const { done, value } = await reader.read();
//         if (done) break;
//         const chunk = decoder.decode(value, { stream: true });
//         aiText += chunk;
//         setMessages(prev => {
//           const newMsg = [...prev];
//           newMsg[newMsg.length - 1].content = aiText;
//           return newMsg;
//         });
//       }
//     } catch (err) {
//       setMessages(prev => [...prev, { role: 'assistant', content: "❌ Error connecting to server." }]);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   return (
//     <div className="flex h-screen bg-gray-50 font-sans text-gray-900">
//       {/* SIDEBAR */}
//       <div className="w-64 bg-indigo-900 text-white flex flex-col border-r border-indigo-800">
//         <div className="p-4">
//           <h1 className="text-xl font-bold mb-4 flex items-center gap-2">⚖️ Legal AI</h1>
//           <button onClick={handleCreateSession} className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 p-2 rounded transition">
//             <Plus size={18} /> New Chat
//           </button>
//         </div>
//         <div className="flex-1 overflow-y-auto px-2 space-y-1">
//           {sessions.map(s => (
//             <div key={s.session_id} onClick={() => handleSelectSession(s.session_id)} 
//               className={`flex items-center justify-between p-3 rounded cursor-pointer ${currentSessionId === s.session_id ? 'bg-indigo-800' : 'hover:bg-indigo-800/50'}`}>
//               <div className="flex items-center gap-2 overflow-hidden">
//                 <MessageSquare size={16} /> <span className="truncate text-sm">{s.title}</span>
//               </div>
//               <button onClick={(ev) => handleDeleteSession(s.session_id, ev)} className="hover:text-red-400"><Trash2 size={14}/></button>
//             </div>
//           ))}
//         </div>
//         <div className="p-4 border-t border-indigo-800">
//           <button onClick={handleLogout} className="flex items-center gap-2 text-indigo-300 hover:text-white w-full">
//             <LogOut size={18} /> Sign Out
//           </button>
//         </div>
//       </div>

//       {/* CHAT AREA */}
//       <div className="flex-1 flex flex-col h-screen">
//         <div className="flex-1 overflow-y-auto p-4 space-y-4">
//           {!currentSessionId ? (
//             <div className="h-full flex flex-col items-center justify-center text-gray-400">
//               <h2 className="text-2xl font-bold mb-2">Legal Assistant</h2>
//               <p>Select a chat or start a new one.</p>
//             </div>
//           ) : messages.map((m, i) => (
//             <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
//               <div className={`max-w-[80%] rounded-lg p-4 shadow-sm ${m.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-white border'}`}>
//                  {/* --- FIX APPLIED HERE: Wrapped ReactMarkdown in a div --- */}
//                  <div className="prose prose-sm max-w-none dark:prose-invert">
//                     <ReactMarkdown remarkPlugins={[remarkGfm]}>
//                         {m.content}
//                     </ReactMarkdown>
//                  </div>
//                  {/* ------------------------------------------------------- */}
//               </div>
//             </div>
//           ))}
//           <div ref={messagesEndRef} />
//         </div>

//         {/* INPUT */}
//         <div className="p-4 bg-white border-t">
//           <form onSubmit={handleSend} className="flex items-end gap-2 max-w-4xl mx-auto">
//             <input type="file" ref={fileInputRef} className="hidden" multiple onChange={handleUpload} />
//             <button type="button" onClick={() => fileInputRef.current?.click()} disabled={isUploading || isLoading} 
//               className="p-3 text-gray-500 hover:text-indigo-600 bg-gray-100 rounded-lg">
//               {isUploading ? <Loader2 className="animate-spin"/> : <Upload size={20}/>}
//             </button>
//             <input value={input} onChange={e => setInput(e.target.value)} placeholder="Type your legal question..." 
//               className="flex-1 p-3 rounded-lg border focus:ring-2 focus:ring-indigo-500 outline-none" disabled={isLoading}/>
//             <button type="submit" disabled={!input.trim() || isLoading} className="p-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
//               {isLoading ? <Loader2 className="animate-spin"/> : <Send size={20}/>}
//             </button>
//           </form>
//         </div>
//       </div>
//     </div>
//   );
// };

// // --- LOGIN PAGE ---
// const Login = () => {
//   const [isReg, setIsReg] = useState(false);
//   const [creds, setCreds] = useState({u:'', p:''});
  
//   const submit = async (e: React.FormEvent) => {
//     e.preventDefault();
//     try {
//       if(isReg) {
//         await auth.register(creds.u, creds.p);
//         alert("Registered! Please login."); setIsReg(false);
//       } else {
//         const res = await auth.login(creds.u, creds.p);
//         localStorage.setItem('token', res.data.access_token);
//         window.location.href = "/";
//       }
//     } catch (err: any) { alert(err.response?.data?.detail || "Error"); }
//   };

//   return (
//     <div className="h-screen flex items-center justify-center bg-gray-100">
//       <div className="bg-white p-8 rounded shadow-lg w-96">
//         <h2 className="text-2xl font-bold mb-6 text-center text-indigo-900">{isReg ? "Register" : "Login"}</h2>
//         <form onSubmit={submit} className="space-y-4">
//           <input className="w-full border p-2 rounded" placeholder="Username" value={creds.u} onChange={e=>setCreds({...creds, u:e.target.value})} />
//           <input className="w-full border p-2 rounded" type="password" placeholder="Password" value={creds.p} onChange={e=>setCreds({...creds, p:e.target.value})} />
//           <button className="w-full bg-indigo-600 text-white p-2 rounded">{isReg ? "Sign Up" : "Sign In"}</button>
//         </form>
//         <button onClick={()=>setIsReg(!isReg)} className="w-full mt-4 text-indigo-600 text-sm">{isReg ? "Login instead" : "Create account"}</button>
//       </div>
//     </div>
//   );
// };

// // --- ROUTER ---
// const PrivateRoute = ({ children }: { children: JSX.Element }) => {
//   return localStorage.getItem('token') ? children : <Navigate to="/login" />;
// };

// export default function App() {
//   return (
//     <BrowserRouter>
//       <Routes>
//         <Route path="/login" element={<Login />} />
//         <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
//       </Routes>
//     </BrowserRouter>
//   );
// }