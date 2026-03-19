<template>
  <el-tabs v-model="activeTab" class="sidebar-tabs">
    <!-- ====== Chapters ====== -->
    <el-tab-pane label="章节" name="chapters">
      <div class="sidebar-scrollable">
        <div style="padding: 8px">
          <el-button type="primary" size="small" :icon="Plus" @click="store.addChapter()" style="width:100%">
            添加章节
          </el-button>
        </div>
        <el-collapse v-model="expandedChapters" accordion>
          <el-collapse-item
            v-for="ch in store.chapters"
            :key="ch.id"
            :name="ch.id"
          >
            <template #title>
              <span style="font-size:13px;font-weight:600;color:#e9c46a">{{ ch.title || ch.id }}</span>
              <el-tag size="small" style="margin-left:6px">{{ ch.nodes.length }} 节点</el-tag>
            </template>
            <div style="padding:8px;display:flex;flex-direction:column;gap:8px">
              <el-input v-model="ch.title" placeholder="章节名" size="small" />
              <el-input v-model="ch.description" placeholder="章节描述" size="small" type="textarea" :rows="2"/>
              <el-input v-model="ch.start_node_id" placeholder="起始 node_id" size="small" />
              <div style="display:flex;gap:6px;margin-top:4px">
                <el-button size="small" type="primary" :icon="View" @click="emit('select-chapter', ch.id)">
                  查看画布
                </el-button>
                <el-button size="small" type="danger" :icon="Delete" @click="confirmDelete(ch.id)">
                  删除
                </el-button>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-tab-pane>

    <!-- ====== Characters ====== -->
    <el-tab-pane label="角色" name="characters">
      <div class="sidebar-scrollable">
        <div style="padding:8px">
          <el-button type="primary" size="small" :icon="Plus" @click="addCharacter()" style="width:100%">
            添加角色
          </el-button>
        </div>
        <el-collapse accordion>
          <el-collapse-item v-for="(ch, idx) in store.assets.characters" :key="ch.id" :name="ch.id">
            <template #title>
              <span style="font-size:13px;color:#90e0ef">{{ ch.name || ch.id }}</span>
            </template>
            <div style="padding:8px;display:flex;flex-direction:column;gap:8px">
              <el-input v-model="ch.id" placeholder="角色 ID" size="small" />
              <el-input v-model="ch.name" placeholder="显示名称" size="small" />
              <el-input v-model="ch.description" placeholder="简介" size="small" type="textarea" :rows="2"/>
              <!-- Portraits -->
              <div>
                <div style="font-size:12px;color:#aaa;margin-bottom:4px">立绘 / 差分</div>
                <div v-for="(p, pi) in ch.portraits" :key="pi" style="display:flex;gap:4px;margin-bottom:4px">
                  <el-input v-model="p.path" placeholder="路径 (assets/portraits/...)" size="small" style="flex:1"/>
                  <el-input v-model="p.label" placeholder="标签 (正常)" size="small" style="width:80px"/>
                  <el-button size="small" :icon="Delete" @click="ch.portraits.splice(pi,1)" />
                </div>
                <el-button size="small" :icon="Plus" @click="ch.portraits.push({path:'',label:''})" style="width:100%">
                  添加立绘
                </el-button>
              </div>
              <el-button size="small" type="danger" :icon="Delete" @click="store.assets.characters.splice(idx,1)">
                删除角色
              </el-button>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-tab-pane>

    <!-- ====== Backgrounds ====== -->
    <el-tab-pane label="背景" name="backgrounds">
      <div class="sidebar-scrollable">
        <div style="padding:8px">
          <el-button type="primary" size="small" :icon="Plus" @click="store.assets.backgrounds.push({id:Date.now()+'',name:'',path:''})" style="width:100%">
            添加背景
          </el-button>
        </div>
        <div v-for="(bg,i) in store.assets.backgrounds" :key="bg.id" style="padding:6px 8px;border-bottom:1px solid #0f3460">
          <el-input v-model="bg.path" placeholder="路径 (assets/backgrounds/xxx.png)" size="small" style="margin-bottom:4px"/>
          <div style="display:flex;gap:4px">
            <el-input v-model="bg.name" placeholder="说明文字" size="small" style="flex:1"/>
            <el-button size="small" :icon="Delete" @click="store.assets.backgrounds.splice(i,1)" />
          </div>
        </div>
      </div>
    </el-tab-pane>

    <!-- ====== BGM ====== -->
    <el-tab-pane label="BGM" name="bgm">
      <div class="sidebar-scrollable">
        <div style="padding:8px">
          <el-button type="primary" size="small" :icon="Plus" @click="addBgm()" style="width:100%">
            添加 BGM
          </el-button>
        </div>
        <div v-for="(desc, key) in store.assets.bgm" :key="key" style="padding:6px 8px;border-bottom:1px solid #0f3460">
          <div style="display:flex;gap:4px">
            <el-input :model-value="key" placeholder="bgm key / 路径" size="small" style="flex:1"
              @update:model-value="renameBgm(key, $event)" />
            <el-button size="small" :icon="Delete" @click="deleteBgm(key)" />
          </div>
          <el-input :model-value="desc" placeholder="说明" size="small" style="margin-top:4px"
            @update:model-value="store.assets.bgm[key] = $event" />
        </div>
      </div>
    </el-tab-pane>
  </el-tabs>
</template>

<script setup>
import { ref } from 'vue'
import { Plus, Delete, View } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useEditorStore } from '../stores/editor.js'

const store = useEditorStore()
const emit = defineEmits(['select-chapter'])

const activeTab = ref('chapters')
const expandedChapters = ref([])

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
.sidebar-tabs {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.sidebar-scrollable {
  overflow-y: auto;
  flex: 1;
  max-height: calc(100vh - 52px - 40px);
}
</style>
