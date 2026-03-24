<template>
  <div class="overview-scroll">
    <!-- Hero Banner -->
    <div class="hero-banner">
      <div class="hero-content">
        <h1 class="hero-title">欢迎回来, 编剧</h1>
        <p class="hero-subtitle">
          {{ store.filename ? `正在编辑: ${store.filename}` : '导入剧本 JSON 文件以开始创作' }}
        </p>
      </div>
      <div class="quick-actions">
        <el-button type="success" size="large" :icon="MagicStick" @click="$emit('open-wizard')" class="wizard-btn pulse-glow">一站式生成引擎</el-button>
        <el-button type="primary" size="large" :icon="FolderOpened" @click="$emit('import-json')">导入剧本</el-button>
        <el-button type="warning" size="large" :icon="Picture" @click="$emit('go-assets')">素材工作站</el-button>
        <el-button size="large" :icon="Edit" @click="$emit('go-editor')">节点编辑</el-button>
      </div>
    </div>

    <!-- Stats Dashboard -->
    <div class="stats-grid">
      <div 
        v-for="(stat, i) in statCards" :key="stat.label"
        class="stat-card"
        :style="{ animationDelay: `${i * 0.08}s` }"
      >
        <div class="stat-icon" :style="{ background: stat.gradient }">
          <el-icon :size="24"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-body">
          <p class="stat-label">{{ stat.label }}</p>
          <h3 class="stat-value">
            <span class="stat-number">{{ stat.value }}</span>
          </h3>
        </div>
      </div>
    </div>

    <!-- Chapter Timeline -->
    <section class="section-card">
      <div class="section-header">
        <h2><el-icon><Collection /></el-icon> 章节流程</h2>
        <div style="display: flex; gap: 8px;">
          <el-tag effect="dark" size="small" type="info">{{ chapterCount }} 章</el-tag>
          <el-button type="primary" size="small" @click="store.addChapter">新建章节</el-button>
        </div>
      </div>
      <div class="section-body">
        <ChapterFlow @select-chapter="jumpToEditor" />
      </div>
    </section>

    <!-- Asset Gallery -->
    <section class="section-card">
      <div class="section-header">
        <h2><el-icon><Picture /></el-icon> 资源库</h2>
        <el-button size="small" type="warning" @click="$emit('go-assets')">前往素材工作站 →</el-button>
      </div>
      <div class="section-body">
        <AssetsPanel />
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Collection, Picture, User, FolderOpened, MagicStick, Edit, ChatDotSquare } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useEditorStore } from '../stores/editor.js'
import AssetsPanel from './AssetsPanel.vue'

const store = useEditorStore()
const emit = defineEmits(['jump-to-editor', 'import-json', 'go-assets', 'go-editor', 'open-wizard'])

const chapterCount = computed(() => store.chapters.length)
const nodeCount = computed(() => store.chapters.reduce((sum, ch) => sum + (ch.nodes?.length || 0), 0))
const characterCount = computed(() => store.assets.characters?.length || 0)
const bgCount = computed(() => store.assets.backgrounds?.length || 0)
const bgmCount = computed(() => Object.keys(store.assets.bgm || {}).length)

const statCards = computed(() => [
  { label: '章节',       value: chapterCount.value,    icon: Collection,     gradient: 'linear-gradient(135deg, #6366f1, #a855f7)' },
  { label: '剧情节点',   value: nodeCount.value,       icon: ChatDotSquare,  gradient: 'linear-gradient(135deg, #f59e0b, #ef4444)' },
  { label: '角色',       value: characterCount.value,  icon: User,           gradient: 'linear-gradient(135deg, #10b981, #06b6d4)' },
  { label: '背景 / BGM', value: `${bgCount.value} / ${bgmCount.value}`, icon: Picture, gradient: 'linear-gradient(135deg, #ec4899, #8b5cf6)' },
])

function jumpToEditor(chapterId) {
  emit('jump-to-editor', chapterId)
}
</script>

<style scoped>
/* ============================================================
   Overview Page — Phase 33 Premium Polish
   ============================================================ */
.overview-scroll {
  padding: 28px 36px;
  overflow-y: auto;
  height: 100%;
}

/* ---- Hero Banner ---- */
.hero-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 36px 44px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(168, 85, 247, 0.08));
  border: 1px solid rgba(99, 102, 241, 0.15);
  border-radius: 18px;
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
}

/* Decorative glow orb */
.hero-banner::before {
  content: '';
  position: absolute;
  top: -60px;
  right: -40px;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.15), transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.hero-title {
  font-size: 30px;
  font-weight: 800;
  background: linear-gradient(135deg, #f0f0f0, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.hero-subtitle {
  color: var(--text-secondary, #8899aa);
  font-size: 14px;
  line-height: 1.5;
}

.quick-actions {
  display: flex;
  gap: 10px;
}

/* Wizard CTA glow */
.wizard-btn.pulse-glow {
  position: relative;
  overflow: visible;
}
.wizard-btn.pulse-glow::after {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: inherit;
  background: linear-gradient(135deg, #10b981, #06b6d4);
  opacity: 0;
  z-index: -1;
  animation: cta-glow 2.5s infinite;
}

@keyframes cta-glow {
  0%, 100% { opacity: 0; transform: scale(1); }
  50%      { opacity: 0.25; transform: scale(1.05); }
}

/* ---- Stats Grid ---- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 22px 24px;
  background: var(--bg-card, rgba(30,30,50,0.6));
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  cursor: default;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: stat-enter 0.5s ease both;
}

.stat-card:hover {
  border-color: rgba(255,255,255,0.12);
  transform: translateY(-3px) scale(1.01);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

@keyframes stat-enter {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  transition: transform 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1) rotate(-3deg);
}

.stat-label {
  font-size: 11px;
  color: var(--text-muted, #8899aa);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-weight: 600;
}

.stat-value {
  font-size: 26px;
  font-weight: 800;
  color: var(--text-primary, #fff);
  margin: 0;
  font-variant-numeric: tabular-nums;
}

/* ---- Section Cards ---- */
.section-card {
  background: var(--bg-card, rgba(30,30,50,0.6));
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  margin-bottom: 24px;
  overflow: hidden;
  transition: border-color 0.3s;
}

.section-card:hover {
  border-color: rgba(255,255,255,0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 28px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}

.section-header h2 {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary, #fff);
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.section-body {
  padding: 24px 28px;
}

/* ---- Responsive ---- */
@media (max-width: 1024px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .hero-banner { flex-direction: column; text-align: center; gap: 20px; }
  .quick-actions { flex-wrap: wrap; justify-content: center; }
}

@media (max-width: 640px) {
  .stats-grid { grid-template-columns: 1fr; }
  .overview-scroll { padding: 16px; }
}
</style>
