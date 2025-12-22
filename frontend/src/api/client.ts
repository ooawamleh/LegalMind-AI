// frontend/src/api/client.ts
import axios from 'axios';

const API_URL = 'http://localhost:8000';
export const API_BASE = API_URL;

export const api = axios.create({ baseURL: API_URL });

// 1. Request Interceptor (Adds Token)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 2. NEW: Response Interceptor (Handles Invalid Tokens)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // If server says "Unauthorized", clear storage and redirect
      localStorage.removeItem('token');
      // Only redirect if we are not already on the login page to avoid loops
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const auth = {
  // ... (keep the rest of the file exactly as it was) ...
  login: async (username: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    return api.post('/token', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  register: (u: string, p: string) => api.post('/register', { username: u, password: p }),
};

export const sessions = {
  list: () => api.get('/sessions'),
  create: (title: string) => api.post('/sessions', { title }),
  rename: (id: string, title: string) => api.patch(`/sessions/${id}`, { title }),
  autoTitle: (id: string, query: string) => api.post(`/sessions/${id}/auto-title`, { query }),
  delete: (id: string) => api.delete(`/sessions/${id}`),
  getHistory: (id: string) => api.get(`/sessions/${id}/history`),
  getFiles: (id: string) => api.get(`/sessions/${id}/files`),
  deleteFile: (sid: string, fid: string) => api.delete(`/sessions/${sid}/files/${fid}`),
};

export const documents = {
  upload: (files: FileList | File[], sessionId: string) => {
    const formData = new FormData();
    const fileArray = files instanceof FileList ? Array.from(files) : files;
    fileArray.forEach((file) => formData.append('files', file));
    return api.post('/upload', formData, {
      params: { session_id: sessionId },
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }
};

// // frontend/src/api/client.ts
// import axios from 'axios';

// const API_URL = 'http://localhost:8000';
// export const API_BASE = API_URL;

// export const api = axios.create({ baseURL: API_URL });

// api.interceptors.request.use((config) => {
//   const token = localStorage.getItem('token');
//   if (token) config.headers.Authorization = `Bearer ${token}`;
//   return config;
// });

// export const auth = {
//   login: async (username: string, password: string) => {
//     const params = new URLSearchParams();
//     params.append('username', username);
//     params.append('password', password);
//     return api.post('/token', params, {
//       headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
//     });
//   },
//   register: (u: string, p: string) => api.post('/register', { username: u, password: p }),
// };

// export const sessions = {
//   list: () => api.get('/sessions'),
//   create: (title: string) => api.post('/sessions', { title }),
//   rename: (id: string, title: string) => api.patch(`/sessions/${id}`, { title }),
  
//   // --- THIS WAS MISSING ---
//   autoTitle: (id: string, query: string) => api.post(`/sessions/${id}/auto-title`, { query }),
//   // ------------------------
  
//   delete: (id: string) => api.delete(`/sessions/${id}`),
//   getHistory: (id: string) => api.get(`/sessions/${id}/history`),
//   getFiles: (id: string) => api.get(`/sessions/${id}/files`),
//   deleteFile: (sid: string, fid: string) => api.delete(`/sessions/${sid}/files/${fid}`),
// };

// export const documents = {
//   upload: (files: FileList | File[], sessionId: string) => {
//     const formData = new FormData();
//     const fileArray = files instanceof FileList ? Array.from(files) : files;
//     fileArray.forEach((file) => formData.append('files', file));
//     return api.post('/upload', formData, {
//       params: { session_id: sessionId },
//       headers: { 'Content-Type': 'multipart/form-data' },
//     });
//   }
// };

// // frontend/src/api/client.ts
// import axios from 'axios';

// const API_URL = 'http://localhost:8000';
// export const API_BASE = API_URL;

// export const api = axios.create({ baseURL: API_URL });

// // Add Token to requests
// api.interceptors.request.use((config) => {
//   const token = localStorage.getItem('token');
//   if (token) config.headers.Authorization = `Bearer ${token}`;
//   return config;
// });

// export const auth = {
//   login: async (username: string, password: string) => {
//     const params = new URLSearchParams();
//     params.append('username', username);
//     params.append('password', password);
//     return api.post('/token', params, {
//       headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
//     });
//   },
//   register: (u: string, p: string) => api.post('/register', { username: u, password: p }),
// };

// export const sessions = {
//   list: () => api.get('/sessions'),
//   create: (title: string) => api.post('/sessions', { title }),
//   delete: (id: string) => api.delete(`/sessions/${id}`),
//   getHistory: (id: string) => api.get(`/sessions/${id}/history`),
// };

// export const documents = {
//   upload: (files: FileList | File[], sessionId: string) => {
//     const formData = new FormData();
//     const fileArray = files instanceof FileList ? Array.from(files) : files;
//     fileArray.forEach((file) => formData.append('files', file)); // Must match backend 'files'
    
//     return api.post('/upload', formData, {
//       params: { session_id: sessionId },
//       headers: { 'Content-Type': 'multipart/form-data' },
//     });
//   }
// };