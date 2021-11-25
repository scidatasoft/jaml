<template>
  <b-popover :delay="delay" :target="target" :triggers="triggers" custom-class="chem-popover">
    <img :src="imageUrl" :width="size" alt="" />
  </b-popover>
</template>
<script>
import { API_URL } from '@/main';

export default {
  props: {
    record: {
      type: [Object, String],
      required: true,
    },
    target: {
      type: String,
      required: true,
    },
    triggers: {
      type: String,
      default: 'hover',
    },
    delay: {
      type: Number,
      default: 1000,
    },
    size: {
      type: Number,
      default: 400,
    },
  },

  computed: {
    imageUrl: function () {
      let id = typeof this.record === 'object' ? this.record.id : this.record;
      return `${API_URL}render/${id}?size=${this.size}`;
    },
  },
};
</script>

<style lang="scss">
.chem-popover {
  text-align: center;
  max-width: fit-content !important;
  max-height: fit-content !important;
}
</style>
