<template>
  <main class="app-shell">
    <section class="hero">
      <div>
        <p class="eyebrow">&#x9AD8;&#x4E2D;&#x751F;&#x7269;&#x5FC5;&#x4FEE;2</p>
        <h1>K12-learn &#x9519;&#x9898;&#x5F52;&#x7C7B;&#x5F3A;&#x5316;</h1>
      </div>
      <div class="status" :class="{ degraded: health.status !== 'ok' }">
        <span></span>
        {{ health.status === 'ok' ? '\u670d\u52a1\u6b63\u5e38' : '\u670d\u52a1\u964d\u7ea7' }}
      </div>
    </section>

    <section class="layout">
      <div class="workspace">
        <div class="panel">
          <div class="panel-header">
            <h2>&#x9519;&#x9898;&#x8F93;&#x5165;</h2>
            <button class="ghost" type="button" @click="clearText">&#x6E05;&#x7A7A;</button>
          </div>
          <textarea
            v-model="text"
            rows="9"
            placeholder="&#x8F93;&#x5165;&#x6216;&#x7C98;&#x8D34;&#x4E00;&#x9053;&#x505A;&#x9519;&#x7684;&#x9AD8;&#x4E2D;&#x751F;&#x7269;&#x9898;&#xFF0C;&#x4F8B;&#x5982;&#xFF1A;&#x8C4C;&#x8C46;&#x6742;&#x4EA4;&#x5B9E;&#x9A8C;&#x4E2D; F2 &#x51FA;&#x73B0; 3:1 &#x5206;&#x79BB;&#x6BD4;..."
          ></textarea>
          <div class="actions">
            <button type="button" :disabled="loading" @click="handleClassify">
              {{ loading ? '\u5f52\u7c7b\u4e2d...' : '\u5f52\u7c7b\u5e76\u63a8\u8350' }}
            </button>
            <p v-if="error" class="error">{{ error }}</p>
          </div>
        </div>

        <div v-if="classification" class="panel result-panel">
          <div class="panel-header">
            <h2>{{ classification.knowledge_point_name }}</h2>
            <span class="badge">{{ result.cache_hit ? '\u7f13\u5b58\u547d\u4e2d' : modelStatusText(classification.model_status) }}</span>
          </div>
          <div class="metric-grid">
            <div>
              <span>{{ confidenceLabel(classification) }}</span>
              <strong>{{ percent(displayConfidence(classification)) }}</strong>
            </div>
            <div>
              <span>&#x8017;&#x65F6;</span>
              <strong>{{ result.elapsed_ms }} ms</strong>
            </div>
            <div>
              <span>&#x91CD;&#x8981;&#x7A0B;&#x5EA6;</span>
              <strong>{{ stars(classification.importance) }}</strong>
            </div>
            <div>
              <span>&#x96BE;&#x5EA6;</span>
              <strong>{{ stars(classification.difficulty) }}</strong>
            </div>
          </div>
          <p class="model-meta">
            <strong>推理模型：</strong>
            <span>{{ modelStatusText(classification.model_status) }}</span>
            <span v-if="classification.bert_confidence !== undefined">BERT {{ percent(classification.bert_confidence) }}</span>
            <span v-if="classification.fasttext_confidence !== undefined">FastText {{ percent(classification.fasttext_confidence) }}</span>
          </p>
          <p v-if="classification.fallback_used || classification.fallback_reason" class="hint">
            {{ fallbackReasonText(classification.fallback_reason) }}
          </p>
          <p class="requirement">{{ classification.core_requirement }}</p>
          <p v-if="Number(classification.confidence || 0) < 0.6" class="hint">
            &#x5F53;&#x524D;&#x5F52;&#x7C7B;&#x7F6E;&#x4FE1;&#x5EA6;&#x8F83;&#x4F4E;&#xFF0C;&#x5EFA;&#x8BAE;&#x7ED3;&#x5408;&#x9898;&#x5E72;&#x5173;&#x952E;&#x8BCD;&#x4EBA;&#x5DE5;&#x786E;&#x8BA4;&#x3002;
          </p>
        </div>

        <div v-if="result" class="panel">
          <div class="panel-header">
            <h2>&#x540C;&#x7C7B;&#x5F3A;&#x5316;&#x9898;</h2>
            <span class="badge muted">{{ result.recommendation_count }} / 5</span>
          </div>
          <p v-if="result.recommendation_count > 0 && result.recommendation_count < 5" class="hint">
            &#x5F53;&#x524D;&#x77E5;&#x8BC6;&#x70B9;&#x9898;&#x5E93;&#x4E0D;&#x8DB3; 5 &#x9053;&#xFF0C;&#x5DF2;&#x5C55;&#x793A;&#x53EF;&#x7528;&#x9898;&#x76EE;&#x3002;
          </p>
          <ol v-if="recommendedQuestions.length" class="practice-list">
            <li v-for="item in recommendedQuestions" :key="item.id">
              <div class="question-title">
                <strong>&#x9898;&#x76EE; {{ item.id }}</strong>
                <span v-if="item.difficulty">&#x96BE;&#x5EA6; {{ stars(item.difficulty) }}</span>
              </div>
              <p>{{ item.stem }}</p>
              <pre v-if="item.options">{{ item.options }}</pre>
              <details>
                <summary>&#x7B54;&#x6848;</summary>
                <div class="answer">{{ item.answer || '\u6682\u65e0\u7b54\u6848' }}</div>
                <p v-if="item.analysis" class="analysis">{{ item.analysis }}</p>
              </details>
            </li>
          </ol>
          <p v-else class="empty">&#x5F53;&#x524D;&#x77E5;&#x8BC6;&#x70B9;&#x6682;&#x65E0;&#x540C;&#x7C7B;&#x5F3A;&#x5316;&#x9898;&#x3002;</p>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h2>&#x6700;&#x8FD1;&#x9519;&#x9898;&#x5F52;&#x7C7B;</h2>
            <button class="ghost" type="button" @click="loadRecent">&#x5237;&#x65B0;</button>
          </div>
          <ul class="recent-list">
            <li v-for="item in recent" :key="item.id || item.created_at || item.input_text">
              <p>{{ item.input_text }}</p>
              <div>
                <span>{{ item.knowledge_point_name || `\u6807\u7b7e ${item.knowledge_point_id}` }}</span>
                <span>{{ item.recommendation_count ?? 0 }} &#x9053;&#x63A8;&#x8350;</span>
                <span>{{ item.elapsed_ms }} ms</span>
              </div>
            </li>
            <li v-if="recent.length === 0" class="empty">&#x6682;&#x65E0;&#x9519;&#x9898;&#x5F52;&#x7C7B;&#x8BB0;&#x5F55;</li>
          </ul>
        </div>
      </div>

      <aside class="sidebar">
        <div class="panel">
          <h2>&#x6982;&#x89C8;</h2>
          <div class="stat-list">
            <div><span>&#x77E5;&#x8BC6;&#x70B9;</span><strong>{{ stats.knowledge_point_count ?? 0 }}</strong></div>
            <div><span>&#x9898;&#x5E93;&#x9898;&#x76EE;</span><strong>{{ stats.question_count ?? 0 }}</strong></div>
            <div><span>&#x7D2F;&#x8BA1;&#x5F52;&#x7C7B;</span><strong>{{ stats.classification_count ?? 0 }}</strong></div>
            <div><span>&#x5E73;&#x5747;&#x8017;&#x65F6;</span><strong>{{ stats.avg_elapsed_ms ?? 0 }} ms</strong></div>
          </div>
        </div>

        <div class="panel">
          <h2>&#x670D;&#x52A1;&#x72B6;&#x6001;</h2>
          <div class="health-list">
            <span :class="{ ok: health.bert_loaded }">BERT {{ health.bert_loaded ? '\u5df2\u52a0\u8f7d' : '\u4e0d\u53ef\u7528' }}</span>
            <span :class="{ ok: health.fasttext_loaded }">FastText {{ health.fasttext_loaded ? '\u5df2\u52a0\u8f7d' : '\u4e0d\u53ef\u7528' }}</span>
            <span :class="{ ok: health.model_loaded }">&#x5F53;&#x524D;&#x6A21;&#x578B; {{ modelStatusText(health.model_status) }}</span>
            <span>&#x515C;&#x5E95;&#x9608;&#x503C; {{ percent(health.bert_confidence_threshold || 0.8) }}</span>
            <span :class="{ ok: health.mysql_connected }">MySQL {{ health.mysql_connected ? '\u5df2\u8fde\u63a5' : '\u672a\u8fde\u63a5' }}</span>
            <span :class="{ ok: health.redis_connected }">Redis {{ health.redis_connected ? '\u5df2\u8fde\u63a5' : '\u672a\u8fde\u63a5' }}</span>
          </div>
        </div>

        <div class="panel">
          <h2>&#x77E5;&#x8BC6;&#x70B9;&#x5217;&#x8868;</h2>
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
import { computed, onMounted, reactive, ref } from 'vue'
import {
  classifyAndRecommendWrongQuestion,
  fetchHealth,
  fetchKnowledgePoints,
  fetchOverviewStats,
  fetchRecentWrongQuestions
} from './api/client'

const text = ref('\u8c4c\u8c46\u9ad8\u830e\u4e0e\u77ee\u830e\u6742\u4ea4\uff0cF1 \u5168\u4e3a\u9ad8\u830e\uff0cF2 \u4e2d\u9ad8\u830e\u4e0e\u77ee\u830e\u7684\u6bd4\u4f8b\u7ea6\u4e3a 3:1\u3002\u8be5\u73b0\u8c61\u4f53\u73b0\u4e86\u4ec0\u4e48\u9057\u4f20\u89c4\u5f8b\uff1f')
const loading = ref(false)
const error = ref('')
const result = ref(null)
const recent = ref([])
const knowledgePoints = ref([])
const stats = reactive({})
const health = reactive({
  status: 'degraded',
  model_loaded: false,
  model_status: 'keyword_fallback',
  bert_loaded: false,
  fasttext_loaded: false,
  bert_confidence_threshold: 0.8,
  mysql_connected: false,
  redis_connected: false
})

const classification = computed(() => result.value?.classification || null)
const recommendedQuestions = computed(() => result.value?.recommended_questions || [])

function stars(value) {
  const count = Number(value || 0)
  return '*'.repeat(count) + '-'.repeat(Math.max(0, 5 - count))
}

function percent(value) {
  return `${Math.round(Number(value || 0) * 100)}%`
}

function displayConfidence(item) {
  if (!item) {
    return 0
  }
  if (item.model_status === 'fasttext_fallback' || item.model_status === 'fasttext') {
    return item.fasttext_confidence ?? item.confidence
  }
  if (item.model_status === 'bert' || item.model_status === 'bert_low_confidence_no_fasttext') {
    return item.bert_confidence ?? item.confidence
  }
  return item.confidence
}

function confidenceLabel(item) {
  if (!item) {
    return '置信度'
  }
  if (item.model_status === 'fasttext_fallback' || item.model_status === 'fasttext') {
    return 'FastText置信度'
  }
  if (item.model_status === 'bert' || item.model_status === 'bert_low_confidence_no_fasttext') {
    return 'BERT置信度'
  }
  return '置信度'
}

function modelStatusText(status) {
  const statusMap = {
    bert: 'BERT\u6a21\u578b',
    fasttext: 'FastText\u6a21\u578b',
    fasttext_fallback: 'FastText\u515c\u5e95',
    keyword_fallback: '\u5173\u952e\u8bcd\u515c\u5e95',
    bert_low_confidence_no_fasttext: 'BERT\u4f4e\u7f6e\u4fe1\u5ea6'
  }
  return statusMap[status] || '\u672a\u77e5\u6a21\u578b'
}

function fallbackReasonText(reason) {
  const reasonMap = {
    bert_unavailable: 'BERT\u6a21\u578b\u4e0d\u53ef\u7528\uff0c\u5df2\u542f\u7528 FastText \u515c\u5e95\u5206\u7c7b\u3002',
    bert_confidence_below_threshold: 'BERT\u7f6e\u4fe1\u5ea6\u4f4e\u4e8e 80%\uff0c\u5df2\u542f\u7528 FastText \u515c\u5e95\u5206\u7c7b\u3002',
    bert_and_fasttext_unavailable: 'BERT \u548c FastText \u90fd\u4e0d\u53ef\u7528\uff0c\u5df2\u4f7f\u7528\u5173\u952e\u8bcd\u515c\u5e95\u5206\u7c7b\u3002',
    fasttext_unavailable: 'BERT\u7f6e\u4fe1\u5ea6\u4f4e\uff0c\u4f46 FastText \u4e0d\u53ef\u7528\uff0c\u6682\u65f6\u4fdd\u7559 BERT \u7ed3\u679c\u3002'
  }
  return reasonMap[reason] || '\u5df2\u542f\u7528\u515c\u5e95\u5206\u7c7b\u3002'
}

function clearText() {
  text.value = ''
  error.value = ''
}

async function handleClassify() {
  error.value = ''
  const currentText = text.value.trim()
  if (!currentText) {
    error.value = '\u8bf7\u8f93\u5165\u9519\u9898\u6587\u672c'
    return
  }

  loading.value = true
  try {
    result.value = await classifyAndRecommendWrongQuestion(currentText)
    await Promise.all([loadRecent(), loadStats(), loadHealth()])
  } catch (err) {
    error.value = err.message || '\u5f52\u7c7b\u5931\u8d25'
  } finally {
    loading.value = false
  }
}

async function loadRecent() {
  recent.value = await fetchRecentWrongQuestions(10)
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
    error.value = err.message || '\u9875\u9762\u521d\u59cb\u5316\u5931\u8d25'
  }
})
</script>
