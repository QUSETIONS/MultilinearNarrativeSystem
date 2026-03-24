/**
 * API Configuration — 统一前后端连接配置
 * Platform Bridge: Phase 23
 */
export const API_BASE = 'http://localhost:8095'
export const WS_BASE = 'ws://localhost:8095'

export const API = {
  STATUS: `${API_BASE}/status`,
  GENERATE: `${API_BASE}/generate`,
  REGISTER: `${API_BASE}/assets/register`,
  EXTRACT_FROM_SCRIPT: `${API_BASE}/assets/extract-from-script`,
  NARRATIVE_CONFIG: `${API_BASE}/narrative/config`,
  NARRATIVE_FEEDBACK: `${API_BASE}/narrative/feedback`,
  STATE: `${API_BASE}/state`,
  HEALTH: `${API_BASE}/health`,
  EXPORT_GODOT: `${API_BASE}/export/godot`,
  WEBSOCKET: `${WS_BASE}/ws`
}
