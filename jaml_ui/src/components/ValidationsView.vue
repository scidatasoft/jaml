<template>
  <v-card>
    <v-toolbar>
      <v-btn v-if="Object.keys($route.params).length !== 0" class="mr-3" title="Back" @click="$router.go(-1)">
        <v-icon>mdi-arrow-up</v-icon>
      </v-btn>

      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        class="mr-3"
        hide-details
        label="Search in any field"
        single-line
      ></v-text-field>

      <v-spacer />
      <v-spacer />
      <v-spacer />
    </v-toolbar>

    <v-data-table
      :footer-props="{ showFirstLastPage: true, itemsPerPageOptions: [10, 20, 50, -1] }"
      :headers="headers"
      :hide-default-footer="items.length < 10"
      :items="items"
      :items-per-page="50"
      :search="search"
    >
      <template #item.img_id="{ item }">
        <img :src="`${API_URL}images/${item.img_id.$oid}`" alt="" height="100" width="100" />
      </template>

      <template #item.model="{ item }">
        <div class="wrap-400">
          <b-link :to="`/models/${encodeURIComponent(model_name(item))}`" title="Go to models ensemble"
            >{{ item.model }}
          </b-link>
        </div>
      </template>
      <template #item.acc="{ item }">
        <v-chip :color="getMetricColor('acc', item.acc)" small style="font-size: unset"
          >{{ roundup(item.acc, 2) }}
        </v-chip>
      </template>
      <template #item.auc="{ item }">
        <v-chip :color="getMetricColor('auc', item.auc)" small style="font-size: unset"
          >{{ roundup(item.auc, 2) }}
        </v-chip>
      </template>
      <template #item.cohens_kappa="{ item }">
        <v-chip :color="getMetricColor('cohens_kappa', item.cohens_kappa)" small style="font-size: unset"
          >{{ roundup(item.cohens_kappa, 2) }}
        </v-chip>
      </template>
      <template #item.f1score="{ item }">
        <v-chip :color="getMetricColor('f1score', item.f1score)" small style="font-size: unset"
          >{{ roundup(item.f1score, 2) }}
        </v-chip>
      </template>
      <template #item.mcc="{ item }">
        <v-chip :color="getMetricColor('mcc', item.mcc)" small style="font-size: unset"
          >{{ roundup(item.mcc, 2) }}
        </v-chip>
      </template>
      <template #item.precision="{ item }">
        <v-chip :color="getMetricColor('precision', item.precision)" small style="font-size: unset"
          >{{ roundup(item.precision, 2) }}
        </v-chip>
      </template>
      <template #item.recall="{ item }">
        <v-chip :color="getMetricColor('recall', item.recall)" small style="font-size: unset"
          >{{ roundup(item.recall, 2) }}
        </v-chip>
      </template>
      <template #item.specificity="{ item }">
        <v-chip :color="getMetricColor('specificity', item.specificity)" small style="font-size: unset"
          >{{ roundup(item.specificity, 2) }}
        </v-chip>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
import ModelBase from '@/components/ModelBase';
import { API_URL, roundup } from '@/main';

export default {
  mixins: [ModelBase],

  data: () => ({
    search: null,
    headers: [
      { text: 'Model', value: 'model' },
      { text: 'AUC', value: 'auc', filterable: false },
      { text: 'F1 Score', value: 'f1score', filterable: false },
      { text: 'Precision', value: 'precision', filterable: false },
      { text: 'Recall', value: 'recall', filterable: false },
      { text: 'Accuracy', value: 'acc', filterable: false },
      { text: 'Specificity', value: 'specificity', filterable: false },
      { text: "Cohen's Kappa", value: 'cohens_kappa', filterable: false },
      { text: 'MCC', value: 'mcc', filterable: false },
    ],
    items: [],
  }),

  computed: {
    API_URL() {
      return API_URL;
    },
    OBJECTS_TYPE() {
      return 'resultsets';
    },
  },

  methods: {
    roundup(value, digits) {
      return roundup(value, digits);
    },
    getData() {
      this.$axios.get(`${this.OBJECTS_TYPE}/${this.$route.params.id}/validations`).then((response) => {
        response.data.forEach((s) => Object.keys(s.metrics).forEach((k) => (s[k] = s.metrics[k])));
        this.items = response.data;
      });
    },
    model_name(item) {
      let i = item.model.indexOf('/');
      return i >= 0 ? item.model.substr(0, i) : item.model;
    },
    method_name(item) {
      let i = item.model.indexOf('/');
      return i >= 0 ? item.model.substr(i) : null;
    },
  },

  created() {
    this.getData();
  },
};
</script>
