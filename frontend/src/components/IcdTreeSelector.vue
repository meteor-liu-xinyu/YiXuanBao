<template>
  <el-dialog :model-value="modelValue" width="820px" title="按层级选择疾病" @close="onClose">
    <div style="display:flex;gap:12px;align-items:center;margin-bottom:8px;">
      <el-input
        v-model="filter"
        placeholder="可输入关键字定位（回车展开到首个匹配节点）"
        clearable
        @keyup.enter="locateFirstMatch"
        style="flex:1;"
      />
      <el-button @click="collapseAll" plain>折叠全部</el-button>
    </div>

    <div style="max-height:520px; overflow:auto;">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        node-key="key"
        highlight-current
        :expand-on-click-node="false"
        :show-line="true"
        :show-checkbox="false"
        :expanded-keys="expandedKeys"
        :default-expanded-keys="defaultExpandedKeys"
        @node-click="onNodeClick"
      >
        <template #default="{ node, data }">
          <div style="padding:6px 8px; display:flex;align-items:center;gap:8px;">
            <span style="flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
              {{ data.label }}
            </span>
            <small v-if="data.code" style="color:#999">{{ data.code }}</small>
          </div>
        </template>
      </el-tree>
    </div>

    <template #footer>
      <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px;">
        <el-button @click="onClose">取消</el-button>
        <el-button type="primary" :disabled="!selectedNode" @click="confirm">确认选择</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { loadAndFlattenICD, getTreeForElTree } from '@/utils/icd-utils'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  targetKey: { type: [String, Number], default: null }
})
const emit = defineEmits(['update:modelValue', 'select'])

const treeData = ref([])
const treeRef = ref(null)
const treeProps = { children: 'children', label: 'label' }
const expandedKeys = ref([])
const defaultExpandedKeys = ref([])
const selectedNode = ref(null)
const filter = ref('')

// collect keys
function collectAllKeys(nodes, out = []) {
  for (const n of nodes || []) {
    if (n && typeof n.key !== 'undefined') out.push(n.key)
    if (n.children) collectAllKeys(n.children, out)
  }
  return out
}

// try instance expandAll for different element-plus versions
async function tryInstanceExpandAll() {
  try {
    if (!treeRef.value) return false
    if (typeof treeRef.value.expandAll === 'function') {
      treeRef.value.expandAll()
      return true
    }
    if (treeRef.value.store && typeof treeRef.value.store.expandAll === 'function') {
      treeRef.value.store.expandAll()
      return true
    }
  } catch (e) {}
  return false
}

// try per-node expand (fallback)
async function tryPerNodeExpand(keys) {
  try {
    if (!treeRef.value || typeof treeRef.value.getNode !== 'function') return false
    for (const k of keys) {
      const node = treeRef.value.getNode(k)
      if (!node) continue
      if (typeof node.expand === 'function') {
        node.expand(true)
        continue
      }
      if (typeof node.setExpanded === 'function') {
        node.setExpanded(true)
        continue
      }
      if (node.childNodes && node.childNodes.length) {
        node.childNodes.forEach(c => { try { if (typeof c.setExpanded === 'function') c.setExpanded(true) } catch (_) {} })
      }
    }
    return true
  } catch (e) {
    return false
  }
}

// try instance collapseAll for different versions
async function tryInstanceCollapseAll() {
  try {
    if (!treeRef.value) return false
    if (typeof treeRef.value.collapseAll === 'function') {
      treeRef.value.collapseAll()
      return true
    }
    if (treeRef.value.store && typeof treeRef.value.store.collapseAll === 'function') {
      treeRef.value.store.collapseAll()
      return true
    }
  } catch (e) {}
  return false
}

// try per-node collapse (fallback)
async function tryPerNodeCollapse(keys) {
  try {
    if (!treeRef.value || typeof treeRef.value.getNode !== 'function') return false
    for (const k of keys) {
      const node = treeRef.value.getNode(k)
      if (!node) continue
      if (typeof node.collapse === 'function') {
        node.collapse()
        continue
      }
      if (typeof node.setExpanded === 'function') {
        node.setExpanded(false)
        continue
      }
      if (node.childNodes && node.childNodes.length) {
        node.childNodes.forEach(c => { try { if (typeof c.setExpanded === 'function') c.setExpanded(false) } catch (_) {} })
      }
    }
    return true
  } catch (e) {
    return false
  }
}

// robust collapseAll: update expandedKeys and try instance/per-node methods
async function collapseAll() {
  expandedKeys.value = []
  defaultExpandedKeys.value = []
  await nextTick()
  const inst = await tryInstanceCollapseAll()
  if (!inst) {
    const keys = collectAllKeys(treeData.value)
    await tryPerNodeCollapse(keys)
  }
}

// node click handler
function onNodeClick(data, node) {
  selectedNode.value = data
  try { node.setCurrent() } catch (e) {}
}

function onClose() {
  selectedNode.value = null
  emit('update:modelValue', false)
}

function confirm() {
  if (!selectedNode.value) return
  emit('select', {
    code: selectedNode.value.code,
    name: selectedNode.value.name,
    label: selectedNode.value.label
  })
  emit('update:modelValue', false)
  selectedNode.value = null
}

// scroll/locate helper: set current key and try to scroll DOM into view
async function scrollToAndFocusKey(key) {
  if (!key) return
  try {
    // set current key if supported
    try { if (treeRef.value && treeRef.value.setCurrentKey) treeRef.value.setCurrentKey(key) } catch (e) {}

    await nextTick()
    // try to get node instance
    const node = treeRef.value && typeof treeRef.value.getNode === 'function' ? treeRef.value.getNode(key) : null

    // try known element properties
    let el = null
    if (node) {
      el = node.el || node.$el || (node?.$el && node.$el) || node.element
    }

    // fallback: try to find DOM by attribute inside tree root
    if (!el) {
      const rootEl = treeRef.value && (treeRef.value.$el || (treeRef.value.root && treeRef.value.root.$el) || treeRef.value)
      if (rootEl && rootEl.querySelector) {
        // element-plus doesn't always set data-key; try node-key attribute or text match
        el = rootEl.querySelector(`[node-key="${key}"]`) || rootEl.querySelector(`[data-key="${key}"]`)
      }
    }

    if (el && typeof el.scrollIntoView === 'function') {
      el.scrollIntoView({ block: 'center', behavior: 'auto' })
    }
  } catch (e) {
    // ignore best-effort
    // console.debug('scrollToAndFocusKey error', e)
  }
}

// locate first match and expand path, then scroll into view
function locateFirstMatch() {
  const q = String(filter.value || '').toLowerCase().trim()
  if (!q) return
  function dfs(node, parents) {
    const label = (node.label || '').toLowerCase()
    const code = (node.code || '').toLowerCase()
    const curParents = parents.slice()
    curParents.push(node.key)
    if ((label && label.includes(q)) || (code && code.includes(q))) return curParents
    if (node.children) {
      for (const c of node.children) {
        const p = dfs(c, curParents)
        if (p) return p
      }
    }
    return null
  }
  let foundPath = null
  for (const n of treeData.value) {
    const p = dfs(n, [])
    if (p) { foundPath = p; break }
  }
  if (foundPath) {
    expandedKeys.value = Array.from(new Set([...(expandedKeys.value || []), ...foundPath]))
    const key = foundPath[foundPath.length - 1]
    // set current and try to scroll
    try { if (treeRef.value && treeRef.value.setCurrentKey) treeRef.value.setCurrentKey(key) } catch (e) {}
    scrollToAndFocusKey(key)
  }
}

// load tree ensuring ICD cache is ready (so tree always has data when dialog opens)
async function loadTree() {
  // ensure the ICD flattened cache is loaded so getTreeForElTree can use it
  try {
    await loadAndFlattenICD()
  } catch (e) {
    // ignore; fallback below will try to fetch icd.json if util doesn't return data
  }

  let t = null
  try {
    t = getTreeForElTree()
  } catch (e) {
    t = null
  }

  if (!t || (Array.isArray(t) && t.length === 0)) {
    // fallback: try to fetch raw icd.json from assets
    try {
      const res = await fetch(new URL('../assets/icd.json', import.meta.url))
      if (!res.ok) throw new Error(`fetch icd.json failed: ${res.status}`)
      const raw = await res.json()
      function convertNode(node, uidCounter) {
        const key = node.code || node.id || `__icd_${uidCounter.next++}`
        const label = (node.code ? `${node.code}` : '') + (node.name ? ` ${node.name}` : '')
        const out = { key, code: node.code || null, label, name: node.name || '' }
        if (Array.isArray(node.children) && node.children.length) out.children = node.children.map(ch => convertNode(ch, uidCounter))
        return out
      }
      const uidCounter = { next: 1 }
      let roots = []
      if (Array.isArray(raw.categories)) roots = raw.categories.map(n => convertNode(n, uidCounter))
      else if (Array.isArray(raw)) roots = raw.map(n => convertNode(n, uidCounter))
      else if (raw && typeof raw === 'object') roots = [convertNode(raw, uidCounter)]
      t = roots
    } catch (e) {
      t = []
    }
  }

  treeData.value = t || []
}

// when dialog opens, load tree (do not auto-expand all to avoid UI freeze)
watch(
  () => props.modelValue,
  async (open) => {
    if (!open) {
      expandedKeys.value = []
      defaultExpandedKeys.value = []
      selectedNode.value = null
      filter.value = ''
      return
    }
    await loadTree()
    await nextTick()
    // keep collapsed by default to reduce cost
  }
)

// when targetKey provided, expand its path and scroll into view
watch(
  () => props.targetKey,
  async (key) => {
    if (!props.modelValue || !key) return
    await nextTick()
    function dfs(node, parents) {
      const cur = parents.slice()
      cur.push(node.key)
      if (node.key === key || String(node.code) === String(key)) return cur
      if (node.children) {
        for (const c of node.children) {
          const p = dfs(c, cur)
          if (p) return p
        }
      }
      return null
    }
    let path = null
    for (const n of treeData.value) {
      const p = dfs(n, [])
      if (p) { path = p; break }
    }
    if (path) {
      expandedKeys.value = Array.from(new Set([...(expandedKeys.value || []), ...path]))
      const k = path[path.length - 1]
      try { if (treeRef.value && treeRef.value.setCurrentKey) treeRef.value.setCurrentKey(k) } catch (e) {}
      scrollToAndFocusKey(k)
    }
  }
)
</script>

<style scoped>
.el-tree :where(.node__content) { cursor: pointer; }
</style>