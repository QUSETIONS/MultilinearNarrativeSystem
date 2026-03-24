<template>
  <div class="sidebar-container">
    <!-- Tab Navigation -->
    <nav class="sidebar-nav">
      <div 
        v-for="tab in tabs" :key="tab.key"
        class="sidebar-nav-item" 
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        <span class="nav-icon">{{ tab.icon }}</span>
        <span class="nav-label">{{ tab.label }}</span>
        <el-badge v-if="tab.count > 0" :value="tab.count" type="info" class="nav-badge" />
      </div>
    </nav>

    <!-- Tab Content -->
    <div class="sidebar-body">
      <transition name="tab-fade" mode="out-in">

        <!-- ====== Chapters ====== -->
        <div v-if="activeTab === 'chapters'" key="chapters" class="sidebar-scrollable">
          <div class="sidebar-action-bar">
            <el-button type="primary" size="small" :icon="Plus" @click="store.addChapter()" class="full-width-btn">
              添加章节
            </el-button>
          </div>
          <transition-group name="list-stagger" tag="div" class="card-list">
            <div
              v-for="ch in store.chapters"
              :key="ch.id"
              class="sidebar-card chapter-card"
              :class="{ expanded: expandedItem === ch.id }"
              @click="expandedItem = expandedItem === ch.id ? null : ch.id"
            >
              <div class="card-header">
                <span class="card-title">{{ ch.title || ch.id }}</span>
                <el-tag size="small" effect="plain" round>{{ ch.nodes.length }} 节点</el-tag>
              </div>
              <transition name="expand">
                <div v-if="expandedItem === ch.id" class="card-body" @click.stop>
                  <el-input v-model="ch.title" placeholder="章节名" size="small" />
                  <el-input v-model="ch.description" placeholder="章节描述" size="small" type="textarea" :rows="2"/>
                  <el-input v-model="ch.start_node_id" placeholder="起始 node_id" size="small" />
                  <div class="card-actions">
                    <el-button size="small" type="primary" :icon="View" @click="emit('select-chapter', ch.id)">
                      查看画布
                    </el-button>
                    <el-button size="small" type="danger" :icon="Delete" @click="confirmDelete(ch.id)">
                      删除
                    </el-button>
                  </div>
                </div>
              </transition>
            </div>
          </transition-group>
        </div>

        <!-- ====== Characters ====== -->
        <div v-else-if="activeTab === 'characters'" key="characters" class="sidebar-scrollable">
          <div class="sidebar-action-bar">
            <el-button type="primary" size="small" :icon="Plus" @click="addCharacter()" class="full-width-btn">
              添加角色
            </el-button>
          </div>
          <transition-group name="list-stagger" tag="div" class="card-list">
            <div
              v-for="(ch, idx) in store.assets.characters"
              :key="ch.id"
              class="sidebar-card character-card"
              :class="{ expanded: expandedItem === 'char-' + ch.id }"
              @click="expandedItem = expandedItem === 'char-' + ch.id ? null : 'char-' + ch.id"
            >
              <div class="card-header">
                <span class="card-title char-name">{{ ch.name || ch.id }}</span>
                <el-tag v-if="ch.portraits.length" size="small" effect="plain" round>{{ ch.portraits.length }} 立绘</el-tag>
              </div>
              <transition name="expand">
                <div v-if="expandedItem === 'char-' + ch.id" class="card-body" @click.stop>
                  <el-input v-model="ch.id" placeholder="角色 ID" size="small" />
                  <el-input v-model="ch.name" placeholder="显示名称" size="small" />
                  <el-input v-model="ch.description" placeholder="简介" size="small" type="textarea" :rows="2"/>
                  <!-- Portraits -->
                  <div class="portrait-section">
                    <div class="section-label">立绘 / 差分</div>
                    <div v-for="(p, pi) in ch.portraits" :key="pi" class="portrait-row">
                      <el-input v-model="p.path" placeholder="路径" size="small" style="flex:1"/>
                      <el-input v-model="p.label" placeholder="标签" size="small" style="width:70px"/>
                      <el-button size="small" :icon="Delete" @click="ch.portraits.splice(pi,1)" circle />
                    </div>
                    <el-button size="small" :icon="Plus" @click="ch.portraits.push({path:'',label:''})" class="full-width-btn">
                      添加立绘
                    </el-button>
                  </div>
                  <el-button size="small" type="danger" :icon="Delete" @click="store.assets.characters.splice(idx,1)">
                    删除角色
                  </el-button>
                </div>
              </transition>
            </div>
          </transition-group>
        </div>

        <!-- ====== Backgrounds ====== -->
        <div v-else-if="activeTab === 'backgrounds'" key="backgrounds" class="sidebar-scrollable">
          <div class="sidebar-action-bar">
            <el-button type="primary" size="small" :icon="Plus" @click="store.assets.backgrounds.push({id:Date.now()+'',name:'',path:''})" class="full-width-btn">
              添加背景
            </el-button>
          </div>
          <transition-group name="list-stagger" tag="div" class="card-list">
            <div v-for="(bg,i) in store.assets.backgrounds" :key="bg.id" class="sidebar-card bg-card">
              <el-input v-model="bg.path" placeholder="路径 (assets/backgrounds/xxx.png)" size="small" />
              <div style="display:flex;gap:4px;margin-top:4px">
                <el-input v-model="bg.name" placeholder="说明文字" size="small" style="flex:1"/>
                <el-button size="small" :icon="Delete" @click="store.assets.backgrounds.splice(i,1)" circle />
              </div>
            </div>
          </transition-group>
        </div>

        <!-- ====== BGM ====== -->
        <div v-else-if="activeTab === 'bgm'" key="bgm" class="sidebar-scrollable">
          <div class="sidebar-action-bar">
            <el-button type="primary" size="small" :icon="Plus" @click="addBgm()" class="full-width-btn">
              添加 BGM
            </el-button>
          </div>
          <transition-group name="list-stagger" tag="div" class="card-list">
            <div v-for="(desc, key) in store.assets.bgm" :key="key" class="sidebar-card bgm-card">
              <div style="display:flex;gap:4px">
                <el-input :model-value="key" placeholder="bgm key / 路径" size="small" style="flex:1"
                  @update:model-value="renameBgm(key, $event)" />
                <el-button size="small" :icon="Delete" @click="deleteBgm(key)" circle />
              </div>
              <el-input :model-value="desc" placeholder="说明" size="small" style="margin-top:4px"
                @update:model-value="store.assets.bgm[key] = $event" />
            </div>
          </transition-group>
        </div>

      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Plus, Delete, View } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useEditorStore } from '../stores/editor.js'

const store = useEditorStore()
const emit = defineEmits(['select-chapter'])

const activeTab = ref('chapters')
const expandedItem = ref(null)

const tabs = computed(() => [
  { key: 'chapters',    label: '章节', icon: '📑', count: store.chapters.length },
  { key: 'characters',  label: '角色', icon: '👤', count: store.assets.characters.length },
  { key: 'backgrounds', label: '背景', icon: '🏞️', count: store.assets.backgrounds.length },
  { key: 'bgm',         label: 'BGM', icon: '🎵', count: Object.keys(store.assets.bgm).length },
])

function addCharacter() {
  store.assets.characters.push({ id: `char_${Date.now()}`, name: '新角色', description: '', portraits: [] })
}

function addBgm() {
  const key = `assets/bgm/new_${Date.now()}.ogg`
  store.assets.bgm[key] = '新音乐'
}

function deleteBgm(key) {
  const obj = { ...store.assets.bgm }
  delete obj[key]
  store.assets.bgm = obj
}

function renameBgm(oldKey, newKey) {
  if (oldKey === newKey) return
  const desc = store.assets.bgm[oldKey]
  const obj = { ...store.assets.bgm }
  delete obj[oldKey]
  obj[newKey] = desc
  store.assets.bgm = obj
}

async function confirmDelete(chapterId) {
  try {
    await ElMessageBox.confirm('确认删除该章节及其所有节点？', '警告', { type: 'warning' })
    store.deleteChapter(chapterId)
  } catch { /* cancelled */ }
}
</script>

<style scoped>
/* ============================================================
   Premium Sidebar — Phase 33 P2
   ============================================================ */

.sidebar-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  border-right: 1px solid rgba(255,255,255,0.06);
}

/* ---- Nav Tabs ---- */
.sidebar-nav {
  display: flex;
  gap: 0;
  padding: 6px 6px 0;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
}

.sidebar-nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 4px 6px;
  font-size: 11px;
  color: rgba(255,255,255,0.45);
  cursor: pointer;
  border-radius: 8px 8px 0 0;
  transition: all 0.25s ease;
  position: relative;
  user-select: none;
}

.sidebar-nav-item:hover {
  color: rgba(255,255,255,0.75);
  background: rgba(255,255,255,0.04);
}

.sidebar-nav-item:active {
  transform: scale(0.95);
}

.sidebar-nav-item.active {
  color: #a78bfa;
  background: rgba(167, 139, 250, 0.08);
  font-weight: 600;
}

.sidebar-nav-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 20%;
  width: 60%;
  height: 2px;
  background: linear-gradient(90deg, #818cf8, #a78bfa);
  border-radius: 2px;
}

.nav-icon { font-size: 16px; }
.nav-label { font-size: 10px; letter-spacing: 0.5px; }
.nav-badge { margin-left: 2px; }

/* ---- Body ---- */
.sidebar-body {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.sidebar-scrollable {
  overflow-y: auto;
  height: 100%;
  padding-bottom: 20px;
}

.sidebar-scrollable::-webkit-scrollbar {
  width: 4px;
}
.sidebar-scrollable::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.1);
  border-radius: 4px;
}

/* ---- Action Bar ---- */
.sidebar-action-bar {
  padding: 10px 10px 6px;
  position: sticky;
  top: 0;
  z-index: 5;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(8px);
}

.full-width-btn { width: 100%; }

/* ---- Card List ---- */
.card-list {
  padding: 4px 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ---- Sidebar Card ---- */
.sidebar-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-card:hover {
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,255,255,0.1);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.sidebar-card:active {
  transform: translateY(0) scale(0.98);
}

.sidebar-card.expanded {
  background: rgba(99, 102, 241, 0.06);
  border-color: rgba(99, 102, 241, 0.2);
}

/* ---- Card Header ---- */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 13px;
  font-weight: 600;
  color: #e9c46a;
}

.char-name {
  color: #90e0ef;
}

/* ---- Card Body ---- */
.card-body {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-actions {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

/* ---- Portraits ---- */
.portrait-section {
  margin-top: 4px;
}

.section-label {
  font-size: 11px;
  color: rgba(255,255,255,0.4);
  margin-bottom: 6px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.portrait-row {
  display: flex;
  gap: 4px;
  margin-bottom: 4px;
}

/* ============================================================
   Transitions
   ============================================================ */

/* Tab content fade */
.tab-fade-enter-active,
.tab-fade-leave-active {
  transition: all 0.2s ease;
}
.tab-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.tab-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Card list stagger */
.list-stagger-enter-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.list-stagger-leave-active {
  transition: all 0.25s ease;
}
.list-stagger-enter-from {
  opacity: 0;
  transform: translateX(-12px);
}
.list-stagger-leave-to {
  opacity: 0;
  transform: translateX(12px) scale(0.95);
}
.list-stagger-move {
  transition: transform 0.3s ease;
}

/* Card expand/collapse */
.expand-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
.expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.expand-enter-from {
  opacity: 0;
  max-height: 0;
  transform: translateY(-8px);
}
.expand-enter-to {
  max-height: 500px;
}
.expand-leave-from {
  max-height: 500px;
}
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-8px);
}
</style>
