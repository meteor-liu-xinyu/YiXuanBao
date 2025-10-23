<template>
  <div class="area-picker">
    <select v-model="province" @change="onProvinceChange">
      <option v-if="includeEmpty" value="">{{ emptyTextProvince }}</option>
      <option v-for="p in provinces" :key="p.code" :value="p.code">{{ p.name }}</option>
    </select>

    <select v-model="city" @change="onCityChange" :disabled="!province">
      <option v-if="includeEmpty" value="">{{ emptyTextCity }}</option>
      <option v-for="c in cities" :key="c.code" :value="c.code">{{ c.name }}</option>
    </select>

    <select v-model="area" @change="emitChange" :disabled="!city">
      <option v-if="includeEmpty" value="">{{ emptyTextArea }}</option>
      <option v-for="a in areasList" :key="a.code" :value="a.code">{{ a.name }}</option>
    </select>
  </div>
</template>

<script>
// 适配 Vue 2/3（选项式 API）
import areasData from '@/assets/areas.json';
export default {
  name: 'AreaPicker',
  props: {
    value: { type: Object, default: () => ({ provinceCode: '', cityCode: '', areaCode: '' }) },
    includeEmpty: { type: Boolean, default: true },
    emptyTextProvince: { type: String, default: '请选择省/直辖市' },
    emptyTextCity: { type: String, default: '请选择市/区' },
    emptyTextArea: { type: String, default: '请选择区/县' }
  },
  data() {
    return {
      areas: areasData,
      province: this.value.provinceCode || '',
      city: this.value.cityCode || '',
      area: this.value.areaCode || ''
    };
  },
  computed: {
    provinces() {
      return (this.areas || []).map(p => ({ code: p.code, name: p.name }));
    },
    cities() {
      const p = this.areas.find(x => x.code === this.province);
      return p ? (p.children || []) : [];
    },
    areasList() {
      const c = this.cities.find(x => x.code === this.city);
      return c ? (c.children || []) : [];
    }
  },
  watch: {
    value: {
      handler(v) {
        this.province = v.provinceCode || '';
        this.city = v.cityCode || '';
        this.area = v.areaCode || '';
      },
      deep: true
    }
  },
  methods: {
    onProvinceChange() {
      this.city = '';
      this.area = '';
      this.emitChange();
    },
    onCityChange() {
      this.area = '';
      this.emitChange();
    },
    emitChange() {
      const selected = {
        provinceCode: this.province,
        cityCode: this.city,
        areaCode: this.area
      };
      // v-model 支持
      this.$emit('input', selected);
      // 同时发出 change 事件
      this.$emit('change', {
        province: this.areas.find(p => p.code === this.province) || null,
        city: this.cities.find(c => c.code === this.city) || null,
        area: this.areasList.find(a => a.code === this.area) || null
      });
    }
  }
};
</script>

<style scoped>
.area-picker select { margin-right: 8px; padding: 4px 6px; }
</style>