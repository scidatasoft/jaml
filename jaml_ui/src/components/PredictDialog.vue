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
          <v-row v-if="dataset">
            <v-text-field v-model="dataset.name" label="Resultset Name" readonly />
          </v-row>
          <v-row>
            <v-select
              v-model="selectedModels"
              :item-text="modelItemText"
              :item-value="modelItemValue"
              :items="modelItems"
              chips
              deletable-chips
              dense
              hint="Select models to use for prediction"
              label="Models"
              multiple
              persistent-hint
            />
          </v-row>
          <v-row>
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
        </v-container>

        <b-alert
          :show="dismissCountDown"
          :variant="alertVariant"
          @dismissed="closeAlert()"
          @dismiss-count-down="countDownChanged"
        >
          {{ message }}
        </b-alert>

        <v-progress-linear v-if="uploading" indeterminate></v-progress-linear>
      </v-card-text>

      <v-card-actions>
        <v-checkbox v-model="lastOne" class="ml-3" label="Last" />
        <v-spacer></v-spacer>
        <v-btn :disabled="actionsDisabled" @click="close"> Cancel </v-btn>
        <v-btn :disabled="actionsDisabled" @click="onOk"> Predict </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import { dateFromObjectId } from '@/main';
import { mapGetters } from 'vuex';
import JamlDialogBase from '@/components/JamlDialogBase';

export default {
  mixins: [JamlDialogBase],

  props: {
    dataset: {
      type: [Object, null],
      default: null,
    },
  },

  data: () => ({
    selectedModels: [],
    models: [],
    result: {},
    average_mode: 'individual',
    average_name: null,
  }),

  computed: {
    ...mapGetters(['METHODS']),
    formTitle() {
      return 'Predict';
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
  },

  watch: {
    dialog(val) {
      if (val) {
        this.$axios.get('models').then((response) => {
          response.data.forEach((m) => (m.dateCreated = dateFromObjectId(m._id.$oid)));
          this.models = response.data;
        });
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
        .post('resultsets/predict', {
          rs_ids: [this.dataset._id.$oid],
          model_ids: this.selectedModels,
          average_mode: this.average_mode,
          average_name: this.average_name,
        })
        .then((response) => {
          this.onOkSuccess();
          this.result = response.data;
          this.$emit('predicted', response.data);
        })
        .catch((error) => this.onOkError(error));
    },
  },
};
</script>
