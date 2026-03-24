<template>
  <el-dialog 
    v-model="visible" 
    title="一站式生成引擎" 
    width="900px" 
    fullscreen
    custom-class="wizard-dialog dark-dialog"
    destroy-on-close
  >
    <div class="wizard-container">
      <el-steps :active="currentStep" finish-status="success" align-center class="wizard-steps">
        <el-step title="步骤 1" description="导入原始剧本"></el-step>
        <el-step title="步骤 2" description="AI 智能提取"></el-step>
        <el-step title="步骤 3" description="批量生成与导出"></el-step>
      </el-steps>

      <div class="step-content">
        <!-- Step 1: Script Import -->
        <div v-if="currentStep === 0" class="step step-1">
          <h3>粘贴您的剧本文本或 JSON</h3>
          <p class="desc-text">如果是纯文本，我们将尝试逐行解析。如果是合法的章节 JSON 列表，则直接导入。</p>
          <el-input 
            v-model="scriptInput" 
            type="textarea" 
            :rows="15" 
            placeholder="示例: [{'name': '第一章', 'nodes': [{'speaker': '主角', 'line': '你好世界', 'bg': '城市'}]}] 或者直接粘贴剧本..."
          />
          <div class="step-actions">
            <el-button type="primary" @click="handleExtract" :loading="extracting" size="large">
              交给 AI 提取分析 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- Step 2: AI Review -->
        <div v-if="currentStep === 1" class="step step-2">
          <h3>AI 提取结果确认</h3>
          <p class="desc-text">AI 已经分析了您的剧本并提取出以下需要生成的素材。</p>
          
          <div v-if="extractedAssets.length === 0" class="empty-state">
            没有发现可以提取的素材，请检查剧本格式。
          </div>
          
          <el-table :data="extractedAssets" height="400" v-else class="dark-table">
            <el-table-column prop="type" label="类型" width="100">
              <template #default="scope">
                <el-tag size="small" :type="scope.row.type === '人物立绘' ? 'warning' : 'info'">
                  {{ scope.row.type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="path" label="路径标识" width="180"></el-table-column>
            <el-table-column prop="description" label="画面描述"></el-table-column>
          </el-table>

          <div class="step-actions">
            <el-button @click="currentStep = 0" size="large">返回修改</el-button>
            <el-button type="success" @click="handleConfirmAssets" :loading="registering" size="large">
              确认无误，准备生成 <el-icon class="el-icon--right"><Check /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- Step 3: Generation & Export -->
        <div v-if="currentStep === 2" class="step step-3">
          <h3>准备就绪，开始生成</h3>
          <p class="desc-text">共计 {{ extractedAssets.length }} 个资产待生成。您可以随时前往右侧工作站预览结果。</p>
          
          <div class="gen-progress" v-if="generating">
            <el-progress :text-inside="true" :stroke-width="24" :percentage="genProgress" status="success" />
            <p class="status-msg">{{ genStatusText }}</p>
          </div>
          <div class="gen-progress" v-else-if="genProgress === 100">
            <el-result icon="success" title="生成完成" sub-title="所有资产已处理结束" />
          </div>
          
          <div class="step-actions">
            <el-button 
              type="primary" 
              size="large" 
              @click="handleStartGeneration" 
              :disabled="generating || genProgress === 100"
            >
              <el-icon class="el-icon--left"><MagicStick /></el-icon> 开始批量生成
            </el-button>
            <el-button 
              v-if="genProgress === 100"
              type="warning" 
              size="large" 
              @click="handleExportGodot"
            >
              <el-icon class="el-icon--left"><Download /></el-icon> 导出 Godot ZIP包
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ArrowRight, Check, MagicStick, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { API } from '../utils/api.config.js'
import { apiService } from '../services/api'
import { useEditorStore } from '../stores/editor'

const store = useEditorStore()

const visible = ref(false)
const currentStep = ref(0)
const scriptInput = ref('')

const extracting = ref(false)
const extractedAssets = ref([])
const registering = ref(false)

const generating = ref(false)
const genProgress = ref(0)
const genStatusText = ref('')

function open() {
  currentStep.value = 0
  
  // Try taking active script from the editor memory
  const memoryScript = store.exportJSON()
  if (memoryScript && memoryScript !== '[]' && memoryScript !== 'null') {
    scriptInput.value = memoryScript
  } else {
    scriptInput.value = ''
  }
  
  extractedAssets.value = []
  genProgress.value = 0
  genStatusText.value = ''
  visible.value = true
}

defineExpose({ open })

async function handleExtract() {
  if (!scriptInput.value.trim()) {
    ElMessage.warning('请输入剧本内容')
    return
  }
  
  extracting.value = true
  try {
    let chapters = []
    try {
      chapters = JSON.parse(scriptInput.value)
      if (!Array.isArray(chapters)) throw new Error('Not array')
    } catch {
      // Very basic fallback parsing to JSON structure if user pasted raw text
      chapters = [
        {
          name: "Imported Chapter",
          nodes: scriptInput.value.split('\n').filter(l => l.trim()).map((line, i) => ({
            id: `node_${i}`,
            line: line.trim(),
            speaker: line.includes('：') ? line.split('：')[0] : '佚名'
          }))
        }
      ]
    }
    
    // Call LLM Extraction API
    const data = await apiService.extractFromScript({
      chapters,
      use_llm: true
    })
    
    extractedAssets.value = data.candidates || []
    currentStep.value = 1
    ElMessage.success(`成功分析出 ${extractedAssets.value.length} 个资产需求`)
  } catch (err) {
    ElMessage.error('分析失败: ' + err.message)
  } finally {
    extracting.value = false
  }
}

async function handleConfirmAssets() {
  registering.value = true
  try {
    const data = await apiService.registerAssets("Wizard Batch Import")
    ElMessage.success(`注册完毕，共计 ${data.total_registered} 个资产纳入管理`)
    currentStep.value = 2
  } catch (err) {
    ElMessage.error('注册资产失败: ' + err.message)
  } finally {
    registering.value = false
  }
}

async function handleStartGeneration() {
  if (extractedAssets.value.length === 0) return
  
  generating.value = true
  genProgress.value = 0
  genStatusText.value = `准备生成 ${extractedAssets.value.length} 个资产...`
  
  for (let i = 0; i < extractedAssets.value.length; i++) {
    const asset = extractedAssets.value[i]
    genStatusText.value = `正在生成 (${i + 1}/${extractedAssets.value.length}): ${asset.path.split('/').pop()}`
    genProgress.value = Math.round(((i) / extractedAssets.value.length) * 100)
    
    try {
      await apiService.generateAsset({
        asset_path: asset.path,
        description: asset.description,
        asset_type: asset.type,
        provider: 'siliconflow',  // Default to primary provider
        seed: asset.seed !== undefined ? asset.seed : -1,
        negative_prompt: asset.negative_prompt || ""
      })
    } catch (err) {
    }
  }
  
  genProgress.value = 100
  genStatusText.value = `全部生成任务已提交`
  generating.value = false
  ElMessage.success('批量生成指令已发送')
}

async function handleExportGodot() {
  try {
    const scriptJson = store.exportJSON()
    const res = await fetch(API.EXPORT_GODOT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ script_json: scriptJson })
    })
    if (!res.ok) throw new Error(`Export failed: ${res.status}`)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'godot_assets.zip'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('Godot 资产包下载完成（含剧本数据）')
  } catch (err) {
    ElMessage.error('导出失败: ' + err.message)
  }
}
</script>

<style scoped>
.wizard-container {
  padding: 20px 40px;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.wizard-steps {
  margin-bottom: 40px;
}
.step-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow-y: auto;
}
.step {
  width: 100%;
  max-width: 800px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
h3 {
  margin-top: 0;
  font-size: 24px;
}
.desc-text {
  color: #a0aec0;
  margin-bottom: 20px;
  text-align: center;
}
.step-actions {
  margin-top: 40px;
  display: flex;
  gap: 20px;
}
.dark-table {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.empty-state {
  padding: 40px;
  color: #718096;
  font-size: 16px;
  background: rgba(0,0,0,0.1);
  border-radius: 8px;
  width: 100%;
  text-align: center;
}
.gen-progress {
  width: 100%;
  margin-top: 30px;
  text-align: center;
}
.status-msg {
  margin-top: 15px;
  color: #cbd5e0;
  font-family: monospace;
}
</style>
