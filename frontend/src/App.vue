<template>
  <main class="app-shell">
    <section class="hero">
      <div>
        <p class="eyebrow">高中生物必修2</p>
        <h1>K12-learn 知识点分类</h1>
      </div>
      <div class="status" :class="{ degraded: health.status !== 'ok' }">
        <span></span>
        {{ health.status === 'ok' ? '服务正常' : '服务降级' }}
      </div>
    </section>

    <section class="layout">
      <div class="workspace">
        <div class="panel">
          <div class="panel-header">
            <h2>预测工作台</h2>
            <button class="ghost" type="button" @click="clearText">清空</button>
          </div>
          <textarea
            v-model="text"
            rows="9"
            placeholder="输入或粘贴一道高中生物题目，例如：豌豆杂交实验中 F2 出现 3:1 分离比..."
          ></textarea>
          <div class="actions">
            <button type="button" :disabled="loading" @click="handlePredict">
              {{ loading ? '预测中...' : '开始预测' }}
            </button>
            <p v-if="error" class="error">{{ error }}</p>
          </div>
        </div>

        <div v-if="result" class="panel result-panel">
          <div class="panel-header">
            <h2>{{ result.knowledge_point_name }}</h2>
            <span class="badge">{{ result.cache_hit ? '缓存命中' : '模型推理' }}</span>
          </div>
          <div class="metric-grid">
            <div>
              <span>置信度</span>
              <strong>{{ percent(result.confidence) }}</strong>
            </div>
            <div>
              <span>耗时</span>
              <strong>{{ result.elapsed_ms }} ms</strong>
            </div>
            <div>
              <span>重要程度</span>
              <strong>{{ stars(result.importance) }}</strong>
            </div>
            <div>
              <span>难度</span>
              <strong>{{ stars(result.difficulty) }}</strong>
            </div>
          </div>
          <p class="requirement">{{ result.core_requirement }}</p>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h2>最近预测</h2>
            <button class="ghost" type="button" @click="loadRecent">刷新</button>
          </div>
          <ul class="recent-list">
            <li v-for="item in recent" :key="item.id || item.created_at || item.input_text">
              <p>{{ item.input_text }}</p>
              <div>
                <span>{{ item.knowledge_point_name || `标签 ${item.knowledge_point_id}` }}</span>
                <span>{{ item.elapsed_ms }} ms</span>
                <span>{{ item.cache_hit ? '缓存' : '推理' }}</span>
              </div>
            </li>
            <li v-if="recent.length === 0" class="empty">暂无预测记录</li>
          </ul>
        </div>
      </div>

      <aside class="sidebar">
        <div class="panel">
          <h2>概览</h2>
          <div class="stat-list">
            <div><span>知识点</span><strong>{{ stats.knowledge_point_count ?? 0 }}</strong></div>
            <div><span>累计预测</span><strong>{{ stats.prediction_count ?? 0 }}</strong></div>
            <div><span>平均耗时</span><strong>{{ stats.avg_elapsed_ms ?? 0 }} ms</strong></div>
            <div><span>缓存命中</span><strong>{{ stats.cache_hit_count ?? 0 }}</strong></div>
          </div>
        </div>

        <div class="panel">
          <h2>服务状态</h2>
          <div class="health-list">
            <span :class="{ ok: health.model_loaded }">模型 {{ health.model_loaded ? '已加载' : '占位推理' }}</span>
            <span :class="{ ok: health.mysql_connected }">MySQL {{ health.mysql_connected ? '已连接' : '未连接' }}</span>
            <span :class="{ ok: health.redis_connected }">Redis {{ health.redis_connected ? '已连接' : '未连接' }}</span>
          </div>
        </div>

        <div class="panel">
          <h2>知识点列表</h2>
          <ul class="knowledge-list">
            <li v-for="item in knowledgePoints" :key="item.id">
              <span>{{ item.sort_order }}. {{ item.name }}</span>
              <small>{{ stars(item.importance) }} / {{ stars(item.difficulty) }}</small>
            </li>
          </ul>
        </div>
      </aside>
    </section>
  </main>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import {
  fetchHealth,
  fetchKnowledgePoints,
  fetchOverviewStats,
  fetchRecentPredictions,
  predictKnowledgePoint
} from './api/client'

const text = ref('豌豆高茎与矮茎杂交，F1 全为高茎，F2 中高茎与矮茎的比例约为 3:1。该现象体现了什么遗传规律？')
const loading = ref(false)
const error = ref('')
const result = ref(null)
const recent = ref([])
const knowledgePoints = ref([])
const stats = reactive({})
const health = reactive({
  status: 'degraded',
  model_loaded: false,
  mysql_connected: false,
  redis_connected: false
})

function stars(value) {
  const count = Number(value || 0)
  return '★'.repeat(count) + '☆'.repeat(Math.max(0, 5 - count))
}

function percent(value) {
  return `${Math.round(Number(value || 0) * 100)}%`
}

function clearText() {
  text.value = ''
  error.value = ''
}

async function handlePredict() {
  error.value = ''
  const currentText = text.value.trim()
  if (!currentText) {
    error.value = '请输入题目文本'
    return
  }

  loading.value = true
  try {
    result.value = await predictKnowledgePoint(currentText)
    await Promise.all([loadRecent(), loadStats(), loadHealth()])
  } catch (err) {
    error.value = err.message || '预测失败'
  } finally {
    loading.value = false
  }
}

async function loadRecent() {
  recent.value = await fetchRecentPredictions(10)
}

async function loadStats() {
  Object.assign(stats, await fetchOverviewStats())
}

async function loadHealth() {
  Object.assign(health, await fetchHealth())
}

onMounted(async () => {
  try {
    const [points] = await Promise.all([
      fetchKnowledgePoints(),
      loadRecent(),
      loadStats(),
      loadHealth()
    ])
    knowledgePoints.value = points
  } catch (err) {
    error.value = err.message || '页面初始化失败'
  }
})
</script>
