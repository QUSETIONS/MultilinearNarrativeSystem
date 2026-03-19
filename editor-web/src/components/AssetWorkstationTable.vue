<template>
  <el-table :data="tableData" style="width: 100%" stripe>
    <el-table-column prop="path" label="资源路径" width="300">
      <template #default="{ row }">
        <code>{{ row.path }}</code>
      </template>
    </el-table-column>
    <el-table-column prop="description" label="素材描述 (Prompt)" />
    <el-table-column label="状态" width="120">
      <template #default="{ row }">
        <el-tag :type="row.exists ? 'success' : 'danger'" size="small">
          {{ row.exists ? '已落实' : '缺失' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="150">
      <template #default="{ row }">
        <el-button 
          v-if="!row.exists" 
          type="primary" 
          size="small" 
          plain
          @click="$emit('generate', row)"
        >
          一键生成
        </el-button>
        <el-button v-else type="info" size="small" plain>预览</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

defineEmits(['generate'])

const tableData = computed(() => {
  return props.data.map(item => ({
    ...item,
    exists: item.status === 'FOUND'
  }))
})
</script>
