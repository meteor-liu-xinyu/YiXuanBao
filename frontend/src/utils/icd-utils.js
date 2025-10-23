// frontend/src/utils/icd-utils.js
// 本地 ICD 工具：动态加载 ICD-10-cn.json，扁平化并提供本地搜索与树结构
let cachedFlatList = null
let cachedByCode = null
let rawTree = null

function _dfsCollect(node, list, parents = []) {
  const curPath = parents.slice()
  if (node.code || node.name) {
    curPath.push({ code: node.code || null, name: node.name || '' })
  }
  if (node.code) {
    list.push({
      code: node.code,
      name: node.name || '',
      id: node.id || null,
      label: node.code + (node.name ? ' ' + node.name : ''),
      path: curPath.slice()
    })
  }
  if (Array.isArray(node.children)) {
    for (const ch of node.children) _dfsCollect(ch, list, curPath)
  }
}

export async function loadAndFlattenICD() {
  if (cachedFlatList) return cachedFlatList
  // dynamic import to avoid bundling very large file
  const module = await import('@/assets/ICD-10-cn.json')
  const data = module.default || module
  rawTree = data
  const list = []
  if (Array.isArray(data.categories)) {
    for (const cat of data.categories) _dfsCollect(cat, list, [])
  } else if (Array.isArray(data)) {
    for (const it of data) _dfsCollect(it, list, [])
  } else {
    _dfsCollect(data, list, [])
  }
  // build map by code (last wins)
  const map = new Map()
  for (const it of list) map.set(it.code, it)
  cachedFlatList = Array.from(map.values())
  cachedByCode = map
  return cachedFlatList
}

/**
 * searchICD(list, q, opts)
 * local-only search
 */
export function searchICD(list, q, opts = {}) {
  if (!q || !q.trim()) return []
  const qn = q.trim().toLowerCase()
  const limit = opts.limit || 200

  const equals = []
  const starts = []
  const nameContains = []
  const labelContains = []

  for (const it of list) {
    const codeLower = String(it.code || '').toLowerCase()
    const nameLower = String(it.name || '').toLowerCase()
    const labelLower = String(it.label || '').toLowerCase()

    if (codeLower === qn) equals.push(it)
    else if (codeLower.startsWith(qn)) starts.push(it)
    else if (nameLower.includes(qn)) nameContains.push(it)
    else if (labelLower.includes(qn)) labelContains.push(it)
  }

  const merged = [...equals, ...starts, ...nameContains, ...labelContains]
  return merged.slice(0, limit)
}

/**
 * getTreeForElTree()
 * Convert rawTree into structure suitable for el-tree:
 * nodes: { key, code, label, name, children: [...] }
 */
export function getTreeForElTree() {
  if (!rawTree) return null
  const nodes = Array.isArray(rawTree.categories) ? rawTree.categories : (Array.isArray(rawTree) ? rawTree : [rawTree])
  let uid = 1
  function convert(node) {
    const key = node.code || `__icd_node_${uid++}`
    const label = (node.code ? node.code : '') + (node.name ? ` ${node.name}` : '')
    const out = {
      key,
      code: node.code || null,
      label,
      name: node.name || '',
      id: node.id || null
    }
    if (Array.isArray(node.children) && node.children.length) {
      out.children = node.children.map(convert)
    }
    return out
  }
  return nodes.map(convert)
}

/**
 * getByCode(code) -> item or null (requires loadAndFlattenICD initialized)
 */
export function getByCode(code) {
  if (!cachedByCode) return null
  return cachedByCode.get(code) || null
}

/**
 * getPathForCode(code) -> Promise<pathArray|null>
 * If data not loaded yet, will load and flatten first.
 * Returns array [{code,name}, ...] from root to the node, or null if not found.
 */
export async function getPathForCode(code) {
  if (!code) return null
  if (!cachedByCode) {
    // ensure flat list loaded
    await loadAndFlattenICD()
  }
  const it = cachedByCode.get(code)
  if (!it) return null
  return it.path && it.path.length ? it.path : null
}

export default {
  loadAndFlattenICD,
  searchICD,
  getTreeForElTree,
  getByCode,
  getPathForCode
}