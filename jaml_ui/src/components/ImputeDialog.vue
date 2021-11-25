<template>
  <v-dialog v-model="dialog" width="600">
    <template v-slot:activator="{ on, attrs }">
      <v-btn
        v-if="buttonTitle"
        :disabled="disabled"
        :style="{ display: visible ? 'flex' : 'none' }"
        :title="title"
        v-bind="attrs"
        v-on="on"
      >
        <template v-if="buttonTitle.startsWith('mdi-')">
          <v-icon>
            {{ buttonTitle }}
          </v-icon>
        </template>
        <template v-else>
          {{ buttonTitle }}
        </template>
      </v-btn>
    </template>
    <v-card>
      <v-card-title>
        {{ formTitle }}
      </v-card-title>

      <v-card-text>
        <v-container>
          <v-row v-if="typeof models !== 'object'">
            <v-select
              v-model="methods"
              :items="availableMethods"
              chips
              deletable-chips
              item-text="text"
              item-value="value"
              label="Methods"
              multiple
            />
          </v-row>
          <v-row v-if="hasDNN">
            <v-col>
              <v-text-field v-model="DL_hyper_params.dropout" label="Dropout rate (0 .. 1)" />
            </v-col>
            <v-col>
              <v-text-field v-model="DL_hyper_params.beta" label="L2 regularization factor" />
            </v-col>
          </v-row>
          <v-row v-if="typeof models !== 'object'">
            <v-col>
              <v-checkbox v-model="force" label="Recalculate existing models" />
            </v-col>
          </v-row>
        </v-container>

        <b-alert
          :show="dismissCountDown"
          :variant="alertVariant"
          @dismissed="closeAlert()"
          @dismiss-count-down="countDownChanged"
        >
          {{ message }}
        </b-alert>

        <v-row v-for="(r, i) in result" :key="i">
          {{ r.error }}
        </v-row>

        <v-progress-linear v-if="uploading" indeterminate></v-progress-linear>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn :disabled="actionsDisabled" @click="close"> Cancel </v-btn>
        <v-btn :disabled="actionsDisabled || !methods.length" @click="onOk"> Impute </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import { mapGetters } from 'vuex';
import JamlDialogBase from '@/components/JamlDialogBase';

export default {
  mixins: [JamlDialogBase],

  props: {
    models: {
      type: [Array, String, Object],
      required: true,
    },
    cls: {
      type: Boolean,
      default: true,
    },
    reg: {
      type: Boolean,
      default: true,
    },
  },

  data: () => ({
    selectedDescriptors: ['ECFP'],
    params: {
      ECFP: { Radius: '3', Bits: '1024' },
      FCFP: { Radius: '3', Bits: '1024' },
    },
    methods: [],
    DL_hyper_params: {
      dropout: 0.5,
      beta: 0.01,
    },
    force: false,
    test_set_size: 0,
    result: [],
  }),

  computed: {
    ...mapGetters(['CLS_METHODS', 'REG_METHODS']),
    formTitle() {
      return typeof this.models === 'object' || this.force ? 'Re/calculate models' : 'Impute missing models';
    },
    successUrl() {
      return typeof this.models === 'object'
        ? `/models/${encodeURIComponent(this.models.name)}`
        : typeof this.models === 'string'
        ? `/models/${this.models}`
        : '/models';
    },
    descrNames() {
      return Array.isArray(this.feature('descriptors')) ? this.feature('descriptors').map((d) => d.name) : [];
    },
    model_ids() {
      if (this.models && typeof this.models === 'object') return [this.models._id.$oid];
      if (!this.models || !this.models.length) return null;
      if (typeof this.models === 'string') return [this.models];
      if (typeof this.models[0] === 'string') return this.models;
      return this.models.map((m) => m._id);
    },
    availableMethods() {
      return [...(this.cls ? this.CLS_METHODS : []), ...(this.reg ? this.REG_METHODS : [])];
    },
    hasDNN() {
      return this.methods.map((m) => (typeof m === 'string' ? m : m.value)).includes('DL');
    },
  },

  watch: {
    dialog(val) {
      if (val) {
        if (this.methods.length === 0) this.methods = [...this.availableMethods];
      }
    },
  },

  methods: {
    descrParams(descr) {
      return Array.isArray(this.feature('descriptors'))
        ? Object.keys(this.feature('descriptors').find((d) => d.name === descr).params)
        : [];
    },
    descrParamValues(descr, param) {
      return Array.isArray(this.feature('descriptors'))
        ? this.feature('descriptors').find((d) => d.name === descr).params[param]
        : [];
    },
    onOk() {
      this.uploading = true;
      this.actionsDisabled = true;
      this.$axios
        .post('models/impute', {
          model_ids: this.model_ids,
          descriptors: this.selectedDescriptors.map((selDesc) => ({
            provider: this.feature('descriptors').find((d) => d.name === selDesc).provider,
            name: selDesc,
            params: this.params[selDesc],
          })),
          methods: this.methods.map((m) => (typeof m === 'string' ? m : m.value)),
          hyper_params: {
            DL: this.DL_hyper_params,
          },
          force: this.force,
          test_set_size: this.test_set_size,
        })
        .then((response) => {
          this.onOkSuccess();
          this.result = response.data;
          this.message = 'Models submitted for training';
        })
        .catch((error) => this.onOkError(error));
    },
  },
};
</script>
