<template>
  <v-card class="pa-5" v-html="CONFIG.home_text" />
</template>

<script>
import { mapGetters } from 'vuex';

export default {
  data: () => ({
    tab: null,
  }),
  computed: {
    ...mapGetters(['CONFIG']),
  },
  methods: {},
};
</script>
