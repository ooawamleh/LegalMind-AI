import React, { useState } from 'react';
import { Plus, MessageSquare, Trash2, LogOut, Check, Edit2 } from 'lucide-react';
import { sessions as sessionApi } from '../api/client';

// Inline Type definition to avoid import issues
interface ChatSession { session_id: string; title: string; created_at: string; }

interface SidebarProps {
  sessions: ChatSession[];
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  setSessions: React.Dispatch<React.SetStateAction<ChatSession[]>>;
}

export const Sidebar: React.FC<SidebarProps> = ({ sessions, currentSessionId, onSelectSession, onNewChat, setSessions }) => {
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameInput, setRenameInput] = useState('');

  const handleRenameSession = async (id: string) => {
    if (!renameInput.trim()) return;
    try {
      await sessionApi.rename(id, renameInput);
      setSessions(prev => prev.map(s => s.session_id === id ? { ...s, title: renameInput } : s));
      setRenamingId(null);
    } catch (e) { console.error(e); }
  };

  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if(!confirm("Delete this chat?")) return;
    sessionApi.delete(id).then(() => setSessions(prev => prev.filter(x => x.session_id !== id)));
  };

  return (
    <div className="w-64 bg-indigo-900 text-white flex flex-col border-r border-indigo-800 flex-shrink-0">
      <div className="p-4">
        <h1 className="text-xl font-bold mb-4 flex items-center gap-2">⚖️ Legal AI</h1>
        <button onClick={onNewChat} className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 p-2 rounded transition">
          <Plus size={18} /> New Chat
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto px-2 space-y-1">
        {sessions.map(s => (
          <div key={s.session_id} onClick={() => onSelectSession(s.session_id)} 
            className={`group flex items-center justify-between p-3 rounded cursor-pointer ${currentSessionId === s.session_id ? 'bg-indigo-800' : 'hover:bg-indigo-800/50'}`}>
            
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
                  <Trash2 size={12} className="hover:text-red-400" onClick={(e) => handleDeleteSession(s.session_id, e)}/>
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
  );
};