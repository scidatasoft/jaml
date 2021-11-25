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
        <v-col>
          {{ formTitle }}
        </v-col>
        <v-spacer />
        <v-col v-if="files && files.length > 1">
          <v-select v-if="modeItems.length" v-model="mode" :items="modeItems" label="Mode" />
        </v-col>
      </v-card-title>

      <v-card-text>
        <v-container>
          <v-row dense>
            <v-select
              v-model="filesNames"
              :items="filesNames"
              chips
              dense
              label="Files"
              multiple
              persistent-hint
              readonly
            />
          </v-row>
          <v-row dense>
            <v-col v-if="!mode || mode === 'combine'" cols="9">
              <v-text-field v-model="name" label="Name"></v-text-field>
            </v-col>
            <v-col v-if="mode === 'batch'" cols="4">
              <v-text-field v-model="prefix" label="Prefix"></v-text-field>
            </v-col>
            <v-col v-if="mode === 'batch'" cols="4">
              <v-text-field v-model="suffix" label="Suffix"></v-text-field>
            </v-col>
            <v-col cols="3">
              <v-select v-if="stdizers.length > 1" v-model="stdizer" :items="stdizers" label="Standardizer" />
            </v-col>
          </v-row>
          <template v-if="canPredict && type === 'resultsets'">
            <v-row dense>
              <v-select
                v-model="selectedModels"
                :item-text="modelItemText"
                :item-value="modelItemValue"
                :items="modelItems"
                chips
                deletable-chips
                dense
                hint="Select models to use for immediate prediction"
                label="Models"
                multiple
                persistent-hint
              />
            </v-row>
            <v-row dense>
              <v-col cols="4">
                <v-select
                  v-if="averagingModes.length > 1"
                  v-model="average_mode"
                  :items="averagingModes"
                  label="Averaging mode"
                  persistent-hint
                />
              </v-col>
              <v-col>
                <v-text-field v-if="average_mode === 'all'" v-model="average_name" label="Average model name" />
              </v-col>
            </v-row>
          </template>
          <v-row v-for="(m, i) in fieldsMap" :key="i" dense>
            <v-col cols="4">
              <label class="ma-5">{{ m.name }}</label>
            </v-col>
            <v-col cols="4">
              <v-select v-model="m.type" :items="fieldTypes" label="Field type" />
            </v-col>
            <template v-if="m.type === 'continuous-value'">
              <v-col cols="2">
                <v-select
                  v-model="m.op"
                  :items="[
                    { value: null, text: '' },
                    { value: 'log', text: 'Log' },
                  ]"
                  label="Op"
                />
              </v-col>
            </template>
            <template v-if="m.type === 'split-on-value'">
              <v-col>
                <v-select v-model="m.op" :items="ops" label="Op"></v-select>
              </v-col>
              <v-col>
                <v-text-field v-model="m.value" label="Threshold"></v-text-field>
              </v-col>
            </template>
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

        <v-progress-linear v-if="uploading" indeterminate />
      </v-card-text>

      <v-card-actions>
        <v-checkbox v-model="lastOne" label="Last" />
        <v-spacer></v-spacer>
        <v-btn :disabled="actionsDisabled" @click="close"> Cancel </v-btn>
        <v-btn :disabled="actionsDisabled" @click="onOk"> Create </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import JamlDialogBase from '@/components/JamlDialogBase';

export default {
  mixins: [JamlDialogBase],

  props: {
    files: {
      type: Array,
      required: true,
    },
    type: {
      type: String,
      required: true,
      validator: (value) => ['datasets', 'resultsets'].indexOf(value) !== -1,
    },
  },

  data: () => ({
    name: null,
    selectedModels: [],
    models: [],
    fieldsMap: [],
    dataset: {},
    stdizer: 'Simple',
    mode: null,
    average_mode: 'individual',
    average_name: null,
    prefix: null,
    suffix: null,
    successUrl_: null,
    ops: [
      { value: 'lt', text: '<' },
      { value: 'le', text: '<=' },
      { value: 'ge', text: '>=' },
      { value: 'gt', text: '>' },
    ],
  }),

  computed: {
    formTitle() {
      return `Create ${this.type}`;
    },
    successUrl() {
      return this.successUrl_;
    },
    filesNames() {
      return this.files.map((f) => f.name);
    },
    stdizers() {
      return this.feature('stdizers');
    },
    averagingModes() {
      return this.feature('ensemble-averaging-modes');
    },
    modelItems() {
      if (this.average_mode === 'individual') return this.models;
      else if (this.models) {
        return this.models.map((m) => m.name).filter((v, i, a) => a.indexOf(v) === i);
      } else return [];
    },
    fieldTypes() {
      return [{ value: null, text: '' }].concat(
        this.type === 'datasets'
          ? this.feature('field-types')
          : this.feature('field-types').filter((f) => f.value !== 'split-on-value')
      );
    },
    modeItems() {
      let res = [];
      if (this.feature('create-batch')) res.push('batch');
      if (this.feature('create-combine')) res.push('combine');
      return res;
    },
  },

  watch: {
    dialog(val) {
      if (val) {
        const file = this.files[0];

        this.name = file.name.substr(0, file.name.lastIndexOf('.'));

        this.$axios.get('models').then((response) => (this.models = response.data));

        if (file.fields_mapping != null && file.fields_mapping.length === file.fields.length) {
          this.fieldsMap = file.fields_mapping;
        } else if (file.fields) {
          this.fieldsMap = file.fields.map((f) => ({ name: f, type: null, op: null, value: null }));
        }
      }
    },
    average_mode() {
      this.selectedModels = [];
    },
  },

  methods: {
    modelItemText(mdl) {
      return `${mdl.name}/${mdl.method_name}`;
    },
    modelItemValue(mdl) {
      return mdl._id.$oid;
    },
    onOk() {
      this.uploading = true;
      this.actionsDisabled = true;
      this.$axios
        .post(`${this.type}`, {
          file_ids: this.files.map((f) => f._id.$oid),
          name: this.name,
          mode: this.mode,
          average_mode: this.average_mode,
          average_name: this.average_name,
          prefix: this.prefix,
          suffix: this.suffix,
          stdizer: this.stdizer,
          model_ids: this.selectedModels,
          fields_mapping: this.fieldsMap.filter((f) => f.type != null),
        })
        .then((response) => {
          this.onOkSuccess();
          if (response.data.length === 1) {
            this.dataset = response.data[0];
            this.successUrl_ = `/${this.type}/${this.dataset._id.$oid}`;
          } else if (response.data.length > 1) {
            this.dataset = response.data[0];
            this.successUrl_ = `/${this.type}`;
          }
        })
        .catch((error) => this.onOkError(error));
    },
  },
};
</script>
