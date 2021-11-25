<template>
  <v-dialog v-model="dialog" max-width="500">
    <template v-slot:activator="{ on, attrs }">
      <v-btn
        :disabled="disabled"
        :style="{ display: visible ? 'flex' : 'none' }"
        :title="title"
        v-bind="attrs"
        v-on="on"
      >
        <template>
          <v-icon> mdi-checkbox-multiple-marked-outline </v-icon>
        </template>
      </v-btn>
    </template>

    <v-card>
      <v-card-title> Choose Headers </v-card-title>

      <v-card-text>
        <v-container>
          <v-row dense>
            <v-col>
              <v-select
                v-model="selectedHeaders"
                :items="selectableHeaders"
                hint="Select which headers will show in the table"
                label="Headers"
                multiple
                persistent-hint
              />
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn @click="dialog = false"> Cancel </v-btn>
        <v-btn @click="onOk"> Set </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import DialogBase from '@/components/DialogBase';

export default {
  mixins: [DialogBase],

  props: {
    value: {
      type: Boolean,
      default: false,
    },
    availableHeaders: {
      type: Array,
      required: true,
    },
    headers: {
      type: Array,
      required: true,
    },
  },

  data: () => ({
    selectedHeaders: [],
  }),

  watch: {
    value(val) {
      this.dialog = val;
    },
    dialog(val) {
      this.$emit('input', val);
      if (val) this.selectedHeaders = [...this.headers];
    },
  },

  computed: {
    newHeaders() {
      return typeof this.selectedHeaders[0] === 'object'
        ? this.selectedHeaders
        : this.availableHeaders.filter((h) => this.selectedHeaders.includes(h.value));
    },
    selectableHeaders() {
      return this.availableHeaders.filter((h) => !h.fixed);
    },
  },

  methods: {
    onOk() {
      this.dialog = false;
      if (this.selectedHeaders.length) this.$emit('update:headers', this.newHeaders);
    },
  },
};
</script>
