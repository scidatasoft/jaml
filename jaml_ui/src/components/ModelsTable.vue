<template>
  <div>
    <v-data-table
      v-model="selected"
      :footer-props="{ showFirstLastPage: true, itemsPerPageOptions: [10, 20, 50, -1] }"
      :headers="modelsHeaders"
      :hide-default-footer="items.length < 10"
      :item-key="tableKey"
      :items="items"
      :items-per-page="50"
      :search="search"
      :show-group-by="!ensembleMode"
      :show-select="selectable"
      :sort-by.sync="sortBy"
      :sort-desc.sync="sortDesc"
    >
      <template #top>
        <v-toolbar class="mb-3">
          <v-btn v-if="Object.keys($route.params).length !== 0" class="mr-3" title="Back" @click="$router.go(-1)">
            <v-icon>mdi-arrow-up</v-icon>
          </v-btn>

          <v-text-field
            v-if="!modelName && feature('table-search')"
            v-model="search"
            append-icon="mdi-magnify"
            class="mr-3"
            hide-details
            label="Search in any field"
            single-line
          />

          <template v-if="modelName">
            <v-col cols="6">
              {{ modelName }}
            </v-col>
            <v-col cols="2">
              <v-select v-model="metricsType" :items="metricsTypes" class="mt-6" dense label="Headers" />
            </v-col>
          </template>
          <template v-else>
            <v-col v-if="ensembleModeItems.length" cols="2">
              <v-select v-model="ensembleMode" :items="ensembleModeItems" class="mt-6" dense label="Ensemble score" />
            </v-col>
            <v-col cols="2">
              <v-select
                v-model="metricsGroups"
                :items="availableMetricsGroups"
                class="mt-3"
                deletable-chips
                dense
                label="Headers"
                multiple
              />
            </v-col>
          </template>

          <v-spacer />

          <v-switch v-if="isAuthenticated && isSelectable" v-model="selectable" class="mt-4 mr-4" label="Select" />

          <v-btn-toggle class="mr-2" dense>
            <v-btn v-if="feature('download-xlsx')" title="Export to Excel" @click="downloadModels">
              <v-icon v-if="downloading" class="mdi-spin"> mdi-rotate-right</v-icon>
              <v-icon v-else> mdi-file-excel</v-icon>
            </v-btn>
          </v-btn-toggle>

          <v-btn-toggle dense>
            <HeadersDialog
              v-if="!modelName && !ensembleMode && feature('table-headers')"
              :available-headers="availableHeaders"
              :headers.sync="headers"
            />
            <ImputeDialog
              v-if="ensembleMode && (!modelName || !selectable) && feature('models-impute')"
              :cls="!modelName || hasClsModel"
              :models="modelName || selected"
              :reg="!modelName || hasRegModel"
              button-title="mdi-basket-fill"
              title="Impute missing model"
            />
            <DeleteDialog
              v-if="canDelete() && (!selectable || feature('delete-multi'))"
              v-model="visibleDelete"
              :disabled="!selectable || !selected.length"
              :items="selected"
              :visible="selectable"
              button-title="mdi-delete"
              object-type="models"
              @click="deleteItems(selected)"
              @deleted="items.splice(items.indexOf(selected[0]), 1)"
            />
          </v-btn-toggle>
        </v-toolbar>
      </template>

      <template #item.name="{ item }">
        <b-link :title="item.name" :to="`/models/${item.name}`" class="wrap-300">
          {{ item.name }}
        </b-link>
      </template>

      <template #item._id="{ item }">
        <b-link :title="item._id" :to="`/models/${encodeURIComponent(item._id)}`" class="wrap-300">
          {{ item._id }}
        </b-link>
      </template>

      <template #item.method_name="{ item }">
        <b-link :to="`/model/${item._id.$oid}`">{{ item.method_name }}</b-link>
      </template>

      <template v-slot:item.metrics="{ item }">
        <div v-for="(v, m, i) in item.metrics" :key="`${i}`" style="white-space: nowrap">
          <span>{{ allMetrics[m] }} </span>
          <v-chip :color="getMetricColor(m, v)" small style="font-size: unset">{{ v | number('0.00') }}</v-chip>
        </div>
      </template>

      <template v-for="col in Object.keys(allMetrics)" v-slot:[`item.${col}`]="{ item }">
        <span v-if="item[col]" :key="col">
          <v-chip v-if="coloredMetric(col)" :color="getMetricColor(col, item[col])" small style="font-size: unset">
            {{ item[col] | number('0.00') }}
          </v-chip>
          <v-chip v-else small style="font-size: unset">
            {{ item[col] | number('0.00') }}
          </v-chip>
        </span>
      </template>

      <template #item.access="{ item }">
        {{ item.acl.access }}
      </template>
      <template #item.owner="{ item }">
        {{ getUser(item.acl.owner) }}
      </template>
      <template #item.rights="{ item }">
        <div v-if="item.acl.read.length">
          <div>Read:</div>
          <div v-for="(uid, i) in item.acl.read" :key="i">
            {{ getUser(uid) }}
          </div>
        </div>
        <div v-if="item.acl.write.length">
          <div>Write:</div>
          <div v-for="(uid, i) in item.acl.write" :key="i">
            {{ getUser(uid) }}
          </div>
        </div>
      </template>

      <template #item.dateCreated="{ item }">
        {{ dateTimeFormat.format(item.dateCreated) }}
      </template>

      <template v-slot:item.execution_time="{ item }">
        {{ item.execution_time | number('0.0') }}
      </template>

      <template #item.actions="{ item }">
        <div class="justify-end mr-0">
          <v-icon v-if="canDelete(item)" title="Delete" @click="deleteItems([item])"> mdi-delete</v-icon>
        </div>
      </template>
    </v-data-table>

    <div v-if="modelName" class="pa-2" style="text-align: center">
      <v-row>
        <v-col v-for="(m, i) in sortedItems" :key="i" style="max-width: 260px">
          <v-card v-if="!metricsType || metricsType === 'int'" class="mb-1">
            <v-card-title class="pa-1 pl-2" style="font-size: smaller">
              {{ m.method_name }}
            </v-card-title>
            <v-card-text v-if="m._id.$oid" class="pa-1" style="text-align: left">
              <template v-if="m.method_name && m.method_name.endsWith('r')">
                <v-chip
                  v-for="(_m, i) in ['r2', 'mae', 'rmse']"
                  :key="i"
                  :color="getMetricColor(_m, m[_m])"
                  small
                  style="padding: 5px; margin: 2px"
                >
                  {{ getMetricTitle(_m) }}={{ m[_m] | number('0.00') }}
                </v-chip>
              </template>
              <template v-else>
                <v-chip
                  v-for="(_m, i) in ['auc', 'f1score', 'ba']"
                  :key="i"
                  :color="getMetricColor(_m, m[_m])"
                  small
                  style="padding: 5px; margin: 2px"
                >
                  {{ getMetricTitle(_m) }}={{ m[_m] | number('0.00') }}
                </v-chip>
              </template>
              <v-img :src="`${API_URL}models/${m._id.$oid}/image`" />
            </v-card-text>
          </v-card>

          <v-card v-if="!metricsType || metricsType === 'ext'">
            <v-card-title class="pa-1 pl-2" style="font-size: smaller"> {{ m.method_name }} *</v-card-title>
            <v-card-text v-if="m._id.$oid" class="pa-1" style="text-align: left">
              <template v-if="m.method_name && m.method_name.endsWith('r')">
                <v-chip
                  v-for="(_m, i) in ['r2_ext', 'mae_ext', 'rmse_ext']"
                  :key="i"
                  :color="getMetricColor(_m, m[_m])"
                  small
                  style="padding: 5px; margin: 2px"
                >
                  {{ getMetricTitle(_m) }}={{ m[_m] | number('0.00') }}
                </v-chip>
              </template>
              <template v-else>
                <v-chip
                  v-for="(_m, i) in ['auc_ext', 'f1score_ext', 'ba_ext']"
                  :key="i"
                  :color="getMetricColor(_m, m[_m])"
                  small
                  style="padding: 5px; margin: 2px"
                >
                  {{ getMetricTitle(_m) }}={{ m[_m] | number('0.00') }}
                </v-chip>
              </template>
              <v-img :src="`${API_URL}models/${m._id.$oid}/image?set_type=test`" />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>
  </div>
</template>

<script>
import DeleteDialog from '@/components/DeleteDialog';
import TableBase from '@/components/TableBase';
import ModelBase from '@/components/ModelBase';
import ImputeDialog from '@/components/ImputeDialog';
import HeadersDialog from '@/components/HeadersDialog';
import { download } from '@/main';

export default {
  components: { HeadersDialog, ImputeDialog, DeleteDialog },

  mixins: [TableBase, ModelBase],

  data: () => ({
    mode: 'avg',
    metricsType: 'int',
    metricsTypes: [
      { value: null, text: 'Both' },
      { value: 'int', text: 'Internal' },
      { value: 'ext', text: 'External *' },
    ],
    metricsGroups: ['cls'],
    visibleCreateModels: false,
    allHeaders: [
      { text: 'Model', value: 'name' },
      { text: 'Method', value: 'method_name' },
      { text: 'Metrics', value: 'metrics', sortable: false, groupable: false },
      { text: 'Training Time, s', value: 'execution_time', align: 'end', groupable: false },
      { text: 'Access', value: 'access', initial: false, authenticated: true },
      { text: 'Owner', value: 'owner', initial: false, authenticated: true },
      { text: 'Rights', value: 'rights', sortable: false, groupable: false, initial: false, admin: true },
      { text: 'Created', value: 'dateCreated', initial: false },
      { text: 'Actions', value: 'actions', sortable: false, align: 'end', groupable: false, fixed: true },
    ],
    sortBy: null,
    sortDesc: null,
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'models';
    },
    QUERY() {
      return this.modelName ? `?name=${this.modelName}` : this.ensembleMode ? `?aggr=${this.ensembleMode}` : '';
    },
    isSelectable() {
      return this.feature('delete-multi') || this.feature('download-xlsx');
    },
    modelName() {
      return this.$route.params.name;
    },
    hasClsModel() {
      let rs = this.items.filter((m) => m.method_name && !m.method_name.endsWith('r'));
      return !!(rs && rs.length);
    },
    hasRegModel() {
      let rs = this.items.filter((m) => m.method_name && m.method_name.endsWith('r'));
      return !!(rs && rs.length);
    },
    ensembleMode: {
      get() {
        return this.ensembleModeItems.length === 0 ? null : this.mode;
      },
      set(mode) {
        this.mode = mode;
      },
    },
    ensembleModeItems() {
      return Array.isArray(this.feature('models-ensemble-score'))
        ? [{ value: null, text: '' }, ...this.feature('models-ensemble-score')]
        : [];
    },
    availableMetricsGroups() {
      return this.feature('models-metrics-groups');
    },
    modelMetricsHeaders() {
      const zip = (a, b) => {
        let res = [];
        Array(Math.max(b.length, a.length))
          .fill()
          .forEach((_, i) => {
            res.push(a[i]);
            res.push(b[i]);
          });
        return res;
      };

      let res = [];
      if (this.hasClsModel) {
        if (this.metricsType == null) res = zip(this.clsHeaders, this.clsExtHeaders);
        else if (this.metricsType === 'int') res = this.clsHeaders;
        else if (this.metricsType === 'ext') res = this.clsExtHeaders;
      }
      if (this.hasRegModel) {
        if (this.metricsType == null) res = zip(this.regHeaders, this.regExtHeaders);
        else if (this.metricsType === 'int') res = res.concat(this.regHeaders);
        else if (this.metricsType === 'ext') res = res.concat(this.regExtHeaders);
      }
      return res;
    },
    modelsMetricsHeaders() {
      let res = [];
      if (this.ensembleMode) {
        if (this.metricsGroups.includes('cls')) res = res.concat(this.clsHeaders);
        if (this.metricsGroups.includes('cls_ext')) res = res.concat(this.clsExtHeaders);
        if (this.metricsGroups.includes('reg')) res = res.concat(this.regHeaders);
        if (this.metricsGroups.includes('reg_ext')) res = res.concat(this.regExtHeaders);
      }
      return res;
    },
    modelsHeaders() {
      if (this.modelName) {
        return [
          { text: 'Method', value: 'method_name' },
          ...this.modelMetricsHeaders,
          { text: 'Actions', value: 'actions', sortable: false, align: 'end', groupable: false },
        ];
      } else if (this.ensembleMode) {
        return [
          { text: 'Model', value: '_id' },
          { text: 'N', value: 'n' },
          ...this.modelsMetricsHeaders,
          { text: 'Actions', value: 'actions', align: 'end', sortable: false },
        ];
      } else {
        return this.headers;
      }
    },
    tableKey() {
      if (this.modelName) return 'method_name';
      else if (this.ensembleMode) return '_id';
      else return '_id.$oid';
    },
    sortedItems() {
      const sortBy = this.sortBy == null ? null : Array.isArray(this.sortBy) ? this.sortBy[0] : this.sortBy;
      const sortDesc = this.sortDesc == null ? null : Array.isArray(this.sortDesc) ? this.sortDesc[0] : this.sortDesc;
      if (!this.sortBy) return this.items;
      else {
        const res = sortDesc == null ? 1 : sortDesc ? -1 : 1;
        let items = [...this.items];
        return items.sort((a, b) => (a[sortBy] > b[sortBy] ? res : -res));
      }
    },
  },

  watch: {
    modelName() {
      this.getData();
      if (this.modelName) this.selected = [this.modelName];
      else this.selected = [];
    },
    ensembleMode() {
      this.getData();
    },
  },

  methods: {
    getMetricTitle(m) {
      if (m === 'r2_ext') m = 'q2_ext';
      if (m.endsWith('_ext')) m = m.substr(0, m.length - 4);
      if (m === 'f1score') m = 'f1';
      return m.toUpperCase();
    },
    downloadModels(filename) {
      this.downloading = true;
      this.$axios
        .post(
          `${this.OBJECTS_TYPE}/download`,
          {
            ids:
              this.modelName && !this.selected.length
                ? [this.modelName]
                : this.selected.map((m) => (typeof m === 'string' ? m : m._id)),
          },
          { responseType: 'blob' }
        )
        .then((response) => {
          this.downloading = false;
          download(filename && typeof filename === 'string' ? filename : `${this.OBJECTS_TYPE}.xlsx`, response.data);
        })
        .catch(() => (this.downloading = false));
    },
  },
};
</script>
