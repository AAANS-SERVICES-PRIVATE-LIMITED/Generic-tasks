// API Configuration
export const API_BASE_URL = 'http://localhost:8000';

// Models available for selection (Hybrid: Ollama + Groq)
export const AVAILABLE_MODELS = [
  // Local (Ollama) - 3 text models (lowest size)
  { id: 'llama3.1',                               label: 'Llama 3.1 8B',        provider: 'ollama' },
  { id: 'phi3',                                   label: 'Phi-3 Mini',          provider: 'ollama' },
  { id: 'gemma2:2b',                              label: 'Gemma 2 2B',          provider: 'ollama' },
  // Cloud (Groq) - specific requested models
  { id: 'meta-llama/llama-4-scout-17b-16e-instruct',   label: 'Llama 4 Scout',       provider: 'groq' },
  { id: 'meta-llama/llama-4-maverick-17b-128e-instruct', label: 'Llama 4 Maverick',    provider: 'groq' },
];

export const DEFAULT_MODEL = 'llama3.1';
