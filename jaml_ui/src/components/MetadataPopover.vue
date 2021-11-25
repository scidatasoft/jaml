<template>
  <b-popover :delay="delay" :target="target" :triggers="triggers" custom-class="metadata-popover">
    <b-table-lite :fields="headers" :items="items" borderless small stacked></b-table-lite>
  </b-popover>
</template>
<script>
export default {
  props: {
    item: {
      type: Object,
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
      default: 500,
    },
  },

  data() {
    return {
      headers: [
        { key: 'title' },
        { key: 'project' },
        { key: 'description' },
        { key: 'measurementType' },
        { key: 'target' },
        { key: 'organism' },
      ],
    };
  },

  computed: {
    items: function () {
      return this.item && this.item.metadata ? [this.item.metadata] : [];
    },
  },
};
</script>

<style lang="scss">
.metadata-popover {
  max-width: 600px !important;
  min-width: 300px;
  width: max-content !important;
}
</style>
