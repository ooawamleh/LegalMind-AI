import React, { useState } from 'react';
import { auth } from '../api/client';

export const Login = () => {
  const [isReg, setIsReg] = useState(false);
  const [creds, setCreds] = useState({u:'', p:''});
  
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if(isReg) { 
        await auth.register(creds.u, creds.p); 
        alert("Registered! Please login."); 
        setIsReg(false); 
      } else { 
        const res = await auth.login(creds.u, creds.p); 
        localStorage.setItem('token', res.data.access_token); 
        window.location.href = "/"; 
      }
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