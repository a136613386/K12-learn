import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

async function unwrap(promise) {
  const response = await promise
  const payload = response.data
  if (payload.code !== 0) {
    throw new Error(payload.message || '请求失败')
  }
  return payload.data
}

export function predictKnowledgePoint(text) {
  return unwrap(client.post('/predict/knowledge-point', { text }))
}

export function classifyAndRecommendWrongQuestion(text) {
  return unwrap(client.post('/wrong-questions/classify-and-recommend', { text }))
}

export function fetchKnowledgePoints() {
  return unwrap(client.get('/knowledge-points'))
}

export function fetchRecentPredictions(limit = 10) {
  return unwrap(client.get('/predictions/recent', { params: { limit } }))
}

export function fetchRecentWrongQuestions(limit = 10) {
  return unwrap(client.get('/wrong-questions/recent', { params: { limit } }))
}

export function fetchOverviewStats() {
  return unwrap(client.get('/stats/overview'))
}

export function fetchHealth() {
  return unwrap(client.get('/health'))
}
