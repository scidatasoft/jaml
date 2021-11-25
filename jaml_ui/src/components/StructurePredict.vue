<template>
  <div>
    <v-card>
      <v-card-text>
        <Ketcher v-model="smiles" />

        <v-row>
          <v-col cols="11">
            <v-select
              v-if="availableModels"
              v-model="models"
              :item-text="modelItemText"
              :item-value="modelItemValue"
              :items="availableModels"
              chips
              class="mt-5"
              deletable-chips
              dense
              hint="Select models to use for prediction"
              label="Models"
              multiple
              persistent-hint
            />
          </v-col>
          <v-col class="mt-7" cols="1">
            <b-checkbox v-model="individualModels">Individual</b-checkbox>
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-actions>
        <b-alert :show="!!message" variant="danger">
          {{ message }}
        </b-alert>

        <v-spacer />

        <v-btn :disabled="!smiles || running || !models || !models.length" @click="onPredict">
          Predict
          <v-icon v-if="running" class="mdi-spin"> mdi-rotate-right</v-icon>
        </v-btn>
      </v-card-actions>
    </v-card>
    <v-data-table
      v-if="result"
      :footer-props="{ showFirstLastPage: true, itemsPerPageOptions: [20, 50, 100, -1] }"
      :headers="headers"
      :hide-default-footer="result.length < 10"
      :items="result[0].predictions"
      :items-per-page="20"
    >
      <template v-slot:item.value="{ item }">
        <v-chip v-if="isBinaryValue(item)" :color="getPredictionColor(item.value)" x-small />
        <span v-else>{{ item.value | number('0.00') }}</span>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import Ketcher from '@/components/lookup/Ketcher';
import { roundup } from '@/main';

export default {
  components: { Ketcher },

  data: () => ({
    individualModels: false,
    smiles: null,
    result: null,
    message: null,
    running: false,
    allModels: null,
    models: null,
    headers: [
      { text: 'Model', value: 'model' },
      { text: 'Method', value: 'method' },
      { text: 'Predicted value', value: 'value' },
    ],
  }),

  computed: {
    availableModels() {
      return !this.allModels
        ? []
        : this.individualModels
        ? this.allModels
        : this.allModels.map(m => m.name).filter((v, i, a) => a.indexOf(v) === i);
    },
  },

  methods: {
    roundup(value, digits) {
      return roundup(value, digits);
    },
    isBinaryValue(item) {
      console.log(item);
      if (item.method !== 'avg') return !item.method.endsWith('r');

      let hh = this.result[0].predictions.find(r => r.model === item.model && r.method !== 'avg');
      return !hh.method.endsWith('r');
    },
    getPredictionColor(value) {
      return parseInt(value) ? 'green' : 'red lighten-3';
    },
    modelItemText(mdl) {
      return `${mdl.name}/${mdl.method_name}`;
    },
    modelItemValue(mdl) {
      return mdl._id.$oid;
    },
    onPredict() {
      this.running = true;
      this.message = null;
      this.$axios
        .post('predict', {
          structures: [this.smiles],
          models: this.models,
        })
        .then(response => {
          this.running = false;
          this.message = null;
          this.result = response.data;
        })
        .catch(error => {
          this.running = false;
          this.message = error.response ? error.response.data.detail : 'Unknown error';
        });
    },
  },

  mounted() {
    this.$axios.get('models').then(response => {
      this.allModels = response.data;
    });
  },
};
</script>
