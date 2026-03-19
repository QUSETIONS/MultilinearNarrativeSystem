<template>
  <div class="assets-gallery">
    <!-- Character Gallery -->
    <div class="asset-category">
      <div class="category-header">
        <div class="category-title">
          <el-icon><User /></el-icon> 角色阵容
        </div>
        <el-button type="primary" size="small" plain @click="addCharacter">添加叙事主体</el-button>
      </div>

      <div class="category-content">
        <div v-if="!store.assets.characters.length" class="empty-hint">暂无角色数据</div>
        <div class="character-grid">
          <div v-for="(ch, ci) in store.assets.characters" :key="ch.id" class="character-card-premium">
            <div class="char-header">
              <el-input v-model="ch.name" placeholder="角色名" class="char-name-in" />
              <el-button link type="danger" :icon="Delete" @click="store.assets.characters.splice(ci,1)" />
            </div>
            
            <!-- Portrait Slider -->
            <div class="portrait-track">
              <div v-for="(p, pi) in ch.portraits" :key="pi" class="portrait-slot">
                <div class="slot-box" @click="pickPortrait(ch, pi)">
                  <img v-if="p._blobUrl" :src="p._blobUrl" />
                  <el-icon v-else :size="24"><Picture /></el-icon>
                </div>
                <el-input v-model="p.label" placeholder="标签" size="small" class="p-label" />
                <el-button link type="danger" :icon="Close" size="small" @click="ch.portraits.splice(pi,1)" />
                
                <input type="file" accept="image/*" style="display:none"
                  :ref="el => { if(el) portraitInputs[`${ch.id}-${pi}`] = el }"
                  @change="onPortraitFile($event, ch, pi)" />
              </div>
              <div class="portrait-slot add-slot" @click="ch.portraits.push({path:'',label:'默认',_blobUrl:null})">
                <div class="slot-box dashed">
                  <el-icon :size="20"><Plus /></el-icon>
                </div>
                <span style="font-size:10px">添加差分</span>
              </div>
            </div>

            <div class="char-meta">
              <el-input v-model="ch.id" placeholder="ID (例如: heroin_a)" size="small" prefix-icon="Key" />
              <el-input v-model="ch.description" type="textarea" :rows="2" placeholder="角色的性格特征与背景介绍..." size="small" style="margin-top:8px" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Backgrounds / BGM Row -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px;">
      
      <!-- Backgrounds -->
      <div class="asset-category">
        <div class="category-header">
          <div class="category-title"><el-icon><PictureRounded /></el-icon> 场景画廊</div>
          <el-button size="small" type="primary" plain @click="addBg">上传场景</el-button>
        </div>
        <div class="bg-scroll-grid">
           <div v-for="(bg, bi) in store.assets.backgrounds" :key="bg.id" class="bg-item-premium">
             <div class="bg-preview" @click="pickBg(bi)">
                <img v-if="bg._blobUrl" :src="bg._blobUrl" />
                <el-icon v-else :size="20"><Picture /></el-icon>
             </div>
             <div class="bg-info">
               <el-input v-model="bg.name" placeholder="背景名" size="small" />
               <el-input v-model="bg.path" placeholder="路径" size="small" style="margin-top:4px" />
             </div>
             <el-button link type="danger" :icon="Delete" @click="store.assets.backgrounds.splice(bi,1)" />
             
             <input type="file" accept="image/*" style="display:none"
                :ref="el => { if(el) bgInputs[bi] = el }"
                @change="onBgFile($event, bg)" />
           </div>
        </div>
      </div>

      <!-- BGM -->
      <div class="asset-category">
        <div class="category-header">
          <div class="category-title"><el-icon><Headset /></el-icon> 音乐轨道</div>
          <el-button size="small" type="primary" plain @click="addBgm">添加音轨</el-button>
        </div>
        <div class="bgm-scroll-list">
           <div v-for="(desc, key) in store.assets.bgm" :key="key" class="bgm-list-item">
             <el-icon style="color: var(--accent)"><Service /></el-icon>
             <div style="flex:1">
               <el-input :model-value="key" size="small" class="bgm-key-in" @update:model-value="renameBgm(key, $event)" />
               <el-input :model-value="desc" placeholder="说明" size="small" class="bgm-desc-in" @update:model-value="store.assets.bgm[key] = $event" />
             </div>
             <el-button link type="danger" :icon="Delete" @click="deleteBgm(key)" />
           </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { User, Picture, Delete, Plus, Close, PictureRounded, Headset, Key, Service } from '@element-plus/icons-vue'
import { useEditorStore } from '../stores/editor.js'

const store = useEditorStore()
const portraitInputs = ref({})
const bgInputs = ref({})

function addCharacter() {
  store.assets.characters.push({ id: `ch_${Date.now().toString(36)}`, name: '新角色', description: '', portraits: [] })
}

function addBg() {
  store.assets.backgrounds.push({ id: Date.now()+'', name: '新背景', path: '', _blobUrl: null })
}

function addBgm() {
  const k = `assets/bgm/music_${Date.now().toString(36)}.ogg`
  store.assets.bgm[k] = '新背景音乐'
}

function pickPortrait(ch, pi) {
  portraitInputs.value[`${ch.id}-${pi}`]?.click()
}
function onPortraitFile(e, ch, pi) {
  const file = e.target.files[0]; if (!file) return
  ch.portraits[pi]._blobUrl = URL.createObjectURL(file)
  ch.portraits[pi].path = `assets/portraits/${file.name}`
  e.target.value = ''
}

function pickBg(bi) {
  bgInputs.value[bi]?.click()
}
function onBgFile(e, bg) {
  const file = e.target.files[0]; if (!file) return
  bg._blobUrl = URL.createObjectURL(file)
  bg.path = `assets/backgrounds/${file.name}`
  bg.name = bg.name === '新背景' ? file.name.replace(/\.[^.]+$/, '') : bg.name
  e.target.value = ''
}

function deleteBgm(key) {
  const obj = { ...store.assets.bgm }; delete obj[key]
  store.assets.bgm = obj
}
function renameBgm(oldK, newK) {
  if (oldK === newK) return
  const obj = { ...store.assets.bgm }
  const val = obj[oldK]; delete obj[oldK]; obj[newK] = val
  store.assets.bgm = obj
}
</script>

<style scoped>
.category-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px;
}
.category-title {
  font-size: 16px; font-weight: 800; color: var(--text-primary);
  display: flex; align-items: center; gap: 8px;
}

.character-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.character-card-premium {
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.3s;
}
.character-card-premium:hover { border-color: var(--accent); background: rgba(255,255,255,0.04); }

.char-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.char-name-in :deep(.el-input__inner) { font-weight: 700; color: var(--gold); background: transparent !important; }

.portrait-track {
  display: flex; gap: 10px; overflow-x: auto; padding-bottom: 8px; margin-bottom: 12px;
}
.portrait-slot { display: flex; flex-direction: column; align-items: center; gap: 4px; flex-shrink: 0; }
.slot-box {
  width: 60px; height: 74px;
  background: rgba(0,0,0,0.3);
  border: 1px solid var(--border);
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; cursor: pointer; transition: all 0.2s;
}
.slot-box:hover { border-color: var(--accent); }
.slot-box img { width: 100%; height: 100%; object-fit: cover; }
.slot-box.dashed { border-style: dashed; color: var(--text-muted); }

.bg-scroll-grid {
  display: flex; flex-direction: column; gap: 10px;
  max-height: 400px; overflow-y: auto;
}
.bg-item-premium {
  display: flex; align-items: center; gap: 12px;
  padding: 8px; background: rgba(0,0,0,0.2); border-radius: 8px; border: 1px solid var(--border);
}
.bg-preview { width: 80px; height: 48px; border-radius: 4px; background: #000; flex-shrink: 0; overflow: hidden; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.bg-preview img { width: 100%; height: 100%; object-fit: cover; }

.bgm-scroll-list { display: flex; flex-direction: column; gap: 8px; max-height: 400px; overflow-y: auto; }
.bgm-list-item { display: flex; align-items: center; gap: 12px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; border: 1px solid var(--border); }

.bgm-key-in :deep(.el-input__inner) { font-family: monospace; font-size: 11px; color: var(--accent); }
.bgm-desc-in :deep(.el-input__inner) { font-size: 11px; color: var(--text-muted); border: none !important; padding: 0 !important; }

.empty-hint { padding: 40px; text-align: center; color: var(--text-muted); font-size: 13px; }
</style>
