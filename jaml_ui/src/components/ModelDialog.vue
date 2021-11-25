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
        <v-container v-if="datasets.length">
          <v-row>
            <v-select
              v-model="datasetsNames"
              :items="datasetsNames"
              chips
              dense
              label="Dataset(s)"
              multiple
              persistent-hint
              readonly
            />
          </v-row>
          <v-row v-if="datasets.length === 1">
            <v-text-field v-model="modelName" :disabled="autoName" label="Model Name" />
            <v-checkbox v-if="feature('model-auto-name')" v-model="autoName" label="Auto" />
          </v-row>
          <v-row v-else>
            <v-col>
              <v-text-field v-model="prefix" label="Prefix" />
            </v-col>
            <v-col>
              <v-text-field v-model="suffix" label="Suffix" />
            </v-col>
            <v-col>
              <v-checkbox v-model="autoName" label="Add Descriptors" />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-select
                v-model="fields"
                :items="labelFields"
                :readonly="labelFields.length === 1"
                chips
                deletable-chips
                label="Label field type"
                multiple
              />
            </v-col>
            <v-col>
              <v-select
                v-model="selectedDescriptors"
                :disabled="descrNames.length < 2"
                :items="descrNames"
                chips
                deletable-chips
                label="Descriptors"
                multiple
                persistent-hint
              />
            </v-col>
          </v-row>
          <v-row v-if="selectedDescriptors.length">
            <template v-for="(descr, i) in selectedDescriptors">
              <v-col v-for="(param, j) in descrParams(descr)" :key="`${i}-${j}`">
                <v-select
                  v-if="descrParamType(descr, param) === 'multiple'"
                  v-model="params[descr][param]"
                  :items="descrParamValues(descr, param)"
                  :label="descr"
                  chips
                  deletable-chips
                  multiple
                  style="max-width: 250px"
                />
                <v-combobox
                  v-else
                  v-model="params[descr][param]"
                  :disabled="descrParamValues(descr, param).length < 2"
                  :items="descrParamValues(descr, param)"
                  :label="`${descr} ${param}`"
                />
              </v-col>
            </template>
          </v-row>
          <v-row>
            <v-col>
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
            </v-col>
          </v-row>
          <v-row v-if="hasDNN">
            <v-col>
              <v-text-field v-model="DL_hyper_params.dropout" label="Dropout rate (0 .. 1)" />
            </v-col>
            <v-col>
              <v-text-field v-model="DL_hyper_params.beta" label="L2 regularization factor" />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-checkbox v-model="force" label="Recalculate existing models" />
            </v-col>
            <v-col cols="3">
              <v-select
                v-if="feature('test-set-size')"
                v-model="test_set_size"
                :items="feature('test-set-size')"
                label="Test set %"
              />
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

        <v-progress-linear v-if="uploading" indeterminate />
      </v-card-text>

      <v-card-actions>
        <v-checkbox v-model="lastOne" class="ml-3" label="Last" />
        <v-spacer></v-spacer>
        <v-btn :disabled="actionsDisabled" @click="close"> Cancel</v-btn>
        <v-btn :disabled="actionsDisabled" @click="onOk"> Train</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import { mapGetters } from 'vuex';
import JamlDialogBase from '@/components/JamlDialogBase';
import _ from 'lodash';

export default {
  mixins: [JamlDialogBase],

  props: {
    datasets: {
      type: Array,
      required: true,
    },
  },

  data: () => ({
    autoName: true,
    modelName: null,
    prefix: null,
    suffix: null,
    selectedDescriptors: ['ECFP'],
    fields: [],
    params: {
      ECFP: { Radius: '3', Bits: '1024' },
      FCFP: { Radius: '3', Bits: '1024' },
      PaDEL: { Types: ['2D'] },
      Mordred: {},
      Toxprints: {},
      WebTEST: {},
    },
    methods: [],
    DL_hyper_params: {
      dropout: 0.5,
      beta: 0.01,
    },
    force: false,
    test_set_size: 0,
    result: [],
    _availableMethods: [],
  }),

  computed: {
    ...mapGetters(['CLS_METHODS', 'REG_METHODS']),
    availableMethods() {
      let result = [];
      if (this.fields.includes('single-class-label')) result.push(...this.CLS_METHODS);
      if (this.fields.includes('continuous-value')) result.push(...this.REG_METHODS);
      return result;
    },
    name: {
      get() {
        return this.autoName
          ? `${this.datasets[0].name}-${this.descrSuffix}${this.test_set_size ? '-' + this.test_set_size : ''}`
          : this.modelName;
      },
      set(name) {
        this.modelName = name;
      },
    },
    formTitle() {
      return 'Train Models';
    },
    labelFields() {
      let res = [];
      this.datasets.forEach(d => {
        d.fields_mapping
          .filter(f => ['single-class-label', 'multi-class-label', 'continuous-value'].includes(f.type))
          .map(f => f.type)
          .forEach(f => {
            if (!res.includes(f)) res.push(f);
          });
      });
      return res;
    },
    successUrl() {
      return '/models';
    },
    datasetsNames() {
      return this.datasets.map(d => d.name);
    },
    descrNames() {
      return this.feature('descriptors').map(d => d.name);
    },
    descriptors() {
      return this.selectedDescriptors.map(selDesc => ({
        provider: this.feature('descriptors').find(d => d.name === selDesc).provider,
        name: selDesc,
        params: this.params[selDesc],
      }));
    },
    descrSuffix() {
      return this.selectedDescriptors
        .map(selDesc => {
          if (['ECFP', 'FCFP'].includes(selDesc))
            return `${selDesc}${parseInt(this.params[selDesc].Radius) * 2}-${this.params[selDesc].Bits}`;
          else if (selDesc === 'PaDEL') return `${selDesc}-${this.params[selDesc].Types.join('-')}`;
          else return `${selDesc}`;
        })
        .join('-');
    },
    hasDNN() {
      return this.methods.map(m => (typeof m === 'string' ? m : m.value)).includes('DL');
    },
  },

  watch: {
    dialog(val) {
      if (val) {
        if (this.datasets.length === 1) this.name = this.datasets[0].name;
        else this.name = null;

        this.fields = this.labelFields;
        if (!_.isEqual(_.sortBy(this._availableMethods), _.sortBy(this.availableMethods))) {
          this.methods = [...this.availableMethods];
          this._availableMethods = [...this.availableMethods];
        }
      }
    },
  },

  methods: {
    descrParams(descr) {
      const params = this.feature('descriptors').find(d => d.name === descr).params;
      return params ? Object.keys(params) : [];
    },
    descrParamType(descr, param) {
      return this.feature('descriptors').find(d => d.name === descr).params[param].type;
    },
    descrParamValues(descr, param) {
      return this.feature('descriptors').find(d => d.name === descr).params[param].values;
    },
    onOk() {
      this.uploading = true;
      this.actionsDisabled = true;
      this.$axios
        .post('models', {
          ds_ids: this.datasets.map(d => d._id.$oid),
          name: this.name,
          prefix: this.prefix,
          suffix: this.suffix,
          auto_name: this.autoName,
          label_fields: this.fields,
          descriptors: this.descriptors,
          methods: this.methods.map(m => (typeof m === 'string' ? m : m.value)),
          hyper_params: {
            DL: this.DL_hyper_params,
          },
          force: this.force,
          test_set_size: this.test_set_size,
        })
        .then(response => {
          this.onOkSuccess();
          this.result = response.data;
          this.message = 'Models submitted for training';
        })
        .catch(error => this.onOkError(error));
    },
  },
};
</script>
