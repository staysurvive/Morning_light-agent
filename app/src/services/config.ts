export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'
export const API_BASE = (import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '')
export const API_ORIGIN = new URL(API_BASE, window.location.origin).origin
