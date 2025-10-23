// 通用地区工具 —— 适用于 Vue 项目（ES Module）
export function getProvinces(areas) {
    return (areas || []).map(p => ({ code: p.code, name: p.name }));
  }
  
  export function getChildrenByCode(areas, code) {
    if (!areas) return [];
    const stack = [...areas];
    while (stack.length) {
      const node = stack.shift();
      if (node.code === code) return node.children || [];
      if (node.children) stack.push(...node.children);
    }
    return [];
  }
  
  export function findNodeByCode(areas, code) {
    if (!areas) return null;
    const stack = [...areas];
    while (stack.length) {
      const node = stack.shift();
      if (node.code === code) return node;
      if (node.children) stack.push(...node.children);
    }
    return null;
  }
  
  // 返回某个 code 的行政路径数组，例如 [{code,name}, {code,name}, ...]
  export function getNamePathByCode(areas, code) {
    const path = [];
    function dfs(list, target) {
      for (const n of list || []) {
        path.push({ code: n.code, name: n.name });
        if (n.code === target) return true;
        if (n.children && dfs(n.children, target)) return true;
        path.pop();
      }
      return false;
    }
    dfs(areas, code);
    return path;
  }
  
  // 扁平化为省/市/区三列数组（适合导出 CSV 或导入 DB）
  export function flattenAreas(areas) {
    const rows = [];
    for (const prov of areas || []) {
      const provCode = prov.code;
      const provName = prov.name;
      for (const city of prov.children || []) {
        const cityCode = city.code;
        const cityName = city.name;
        if (city.children && city.children.length) {
          for (const area of city.children) {
            rows.push({
              province_code: provCode,
              province_name: provName,
              city_code: cityCode,
              city_name: cityName,
              area_code: area.code,
              area_name: area.name
            });
          }
        } else {
          rows.push({
            province_code: provCode,
            province_name: provName,
            city_code: cityCode,
            city_name: cityName,
            area_code: '',
            area_name: ''
          });
        }
      }
    }
    return rows;
  }