<template>
  <div class="prop-panel premium-glass">
    <!-- Header -->
    <div class="prop-header">
      <div style="display: flex; align-items: center; gap: 8px;">
         <el-tag :type="tagType" size="small" effect="dark">{{ node.type }}</el-tag>
         <span class="prop-node-id"># {{ node.id }}</span>
      </div>
      <div style="display: flex; gap: 4px;">
        <el-button link :icon="Close" @click="$emit('close')" />
      </div>
    </div>

    <!-- Actions Bar -->
    <div class="prop-actions">
       <el-button type="danger" size="small" plain :icon="Delete" @click="$emit('delete')" style="width: 100%;">删除此节点</el-button>
    </div>

    <el-scrollbar class="prop-scroll">
      <el-form label-position="top" size="small" class="premium-form">

        <!-- Basic Section -->
        <div class="prop-section">
          <h4 class="section-title"><el-icon><EditPen /></el-icon> 基本内容</h4>
          
          <el-form-item label="说话人">
            <el-select v-model="node.speaker" clearable filterable placeholder="选择角色" style="width:100%">
              <el-option label="旁白 (narrator)" value="narrator" />
              <el-option v-for="c in store.assets.characters" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>

          <el-form-item label="对话文本">
            <el-input 
              v-model="node.text" 
              type="textarea" 
              :rows="6" 
              placeholder="输入剧情对白..." 
              class="premium-textarea"
            />
          </el-form-item>
        </div>

        <!-- Visual / Audio Section -->
        <div class="prop-section">
          <h4 class="section-title"><el-icon><MagicStick /></el-icon> 环境与效果</h4>
          
          <el-form-item label="背景场景">
            <el-select v-model="node.bg" clearable placeholder="切换背景..." style="width:100%">
              <el-option v-for="b in store.assets.backgrounds" :key="b.path" :label="b.name || b.path" :value="b.path" />
            </el-select>
          </el-form-item>

          <el-form-item label="背景音乐">
            <el-select v-model="node.music" clearable placeholder="点此切换音乐..." style="width:100%">
              <el-option v-for="(desc, key) in store.assets.bgm" :key="key" :label="desc" :value="key" />
            </el-select>
          </el-form-item>
        </div>

        <!-- Logic Section -->
        <div class="prop-section" v-if="!isChoiceType">
           <h4 class="section-title"><el-icon><Right /></el-icon> 跳转逻辑</h4>
           <el-form-item label="下一节点 ID">
             <el-input v-model="node.next" placeholder="拖动连线自动填充" />
           </el-form-item>
        </div>

        <!-- Choice Editor -->
        <div class="prop-section" v-if="node.type === 'choice'">
          <h4 class="section-title" style="color: var(--warning);"><el-icon><Opportunity /></el-icon> 玩家选项</h4>
          <div v-for="(c, i) in node.choices" :key="i" class="prop-choice-card">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
              <span class="choice-num">选项 {{ i+1 }}</span>
              <el-button link type="danger" :icon="Delete" @click="node.choices.splice(i,1)" />
            </div>
            <el-form-item label="显示文字">
              <el-input v-model="c.text" placeholder="按钮文字" />
            </el-form-item>
            <el-form-item label="跳转目标">
              <el-input v-model="c.next" placeholder="目标 Node ID" />
            </el-form-item>
          </div>
          <el-button :icon="Plus" size="small" dashed @click="node.choices.push({text:'',next:null})" style="width:100%">添加选项</el-button>
        </div>

        <!-- Condition Editor -->
        <div class="prop-section" v-if="node.type === 'branch'">
          <h4 class="section-title" style="color: var(--success);"><el-icon><Filter /></el-icon> 条件分支</h4>
          <div v-for="(c, i) in node.conditions" :key="i" class="prop-choice-card">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
              <span class="choice-num" style="color: var(--success);">规则 {{ i+1 }}</span>
              <el-button link type="danger" :icon="Delete" @click="node.conditions.splice(i,1)" />
            </div>
            <el-form-item label="判定变量">
              <el-input v-model="c.variable" placeholder="变量名" />
            </el-form-item>
            <el-form-item label="等于值">
              <el-input v-model="c.value" placeholder="匹配值" />
            </el-form-item>
            <el-form-item label="跳转目标">
              <el-input v-model="c.next" placeholder="目标 Node ID" />
            </el-form-item>
          </div>
          <el-form-item label="如果不满足任何条件 (Default)">
             <el-input v-model="node.default" placeholder="默认跳转目标" />
          </el-form-item>
          <el-button :icon="Plus" size="small" dashed @click="node.conditions.push({variable:'',value:'',next:null})" style="width:100%">添加分支条件</el-button>
        </div>

      </el-form>
      <div style="height: 40px;"></div>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Close, Delete, EditPen, MagicStick, Right, Opportunity, Plus, Filter } from '@element-plus/icons-vue'
import { useEditorStore } from '../stores/editor.js'

const props = defineProps({ node: Object })
const emit = defineEmits(['close', 'delete'])
const store = useEditorStore()

const isChoiceType = computed(() => props.node.type === 'choice' || props.node.type === 'branch')

const tagType = computed(() => {
  const t = props.node?.type
  if (t === 'choice') return 'warning'
  if (t === 'branch') return 'success'
  return 'primary'
})
</script>

<style scoped>
.prop-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.premium-glass {
  background: rgba(17, 24, 39, 0.8) !important;
  backdrop-filter: blur(12px);
}

.prop-header {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
}
.prop-node-id { font-size: 11px; font-weight: 700; color: var(--text-muted); opacity: 0.8; }

.prop-actions { padding: 8px 16px; border-bottom: 1px solid var(--border); }

.prop-section {
  padding: 16px;
  border-bottom: 1px solid var(--border);
  background: rgba(0,0,0,0.05);
}
.section-title {
  font-size: 12px; font-weight: 800; color: var(--accent);
  margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
  text-transform: uppercase; letter-spacing: 0.5px;
}

.prop-choice-card {
  background: rgba(0,0,0,0.2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}
.choice-num { font-size: 10px; font-weight: 800; color: var(--warning); text-transform: uppercase; }

:deep(.el-form-item__label) {
  font-size: 11px !important;
  font-weight: 600 !important;
  color: var(--text-secondary) !important;
  padding: 0 !important;
  margin-bottom: 4px !important;
}

:deep(.el-input__wrapper), :deep(.el-textarea__wrapper) {
  background: rgba(0,0,0,0.3) !important;
  box-shadow: none !important;
  border: 1px solid var(--border) !important;
}
:deep(.el-input__inner), :deep(.el-textarea__inner) {
  color: var(--text-primary) !important;
}
</style>
