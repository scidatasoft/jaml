<template>
  <v-card>
    <v-expansion-panels>
      <v-expansion-panel>
        <v-expansion-panel-header>
          Protocol: {{ item.name }}
          <v-spacer />
          <span>
            <v-chip small>{{ item.records_number }}</v-chip>
          </span>
        </v-expansion-panel-header>
      </v-expansion-panel>
    </v-expansion-panels>

    <v-toolbar>
      <v-btn class="mr-3" title="Back" @click="$router.go(-1)">
        <v-icon>mdi-arrow-up</v-icon>
      </v-btn>

      <v-text-field
        v-if="feature('table-search')"
        v-model="search"
        append-icon="mdi-magnify"
        hide-details
        label="Search in any field"
        single-line
      />

      <v-spacer />

      <v-checkbox v-model="debug" class="mt-6" label="Show Debug" />

      <v-spacer />

      <v-btn-toggle dense>
        <v-btn
          v-if="feature('download-xlsx')"
          title="Download Excel"
          @click="downloadItem(`${item.name}.xlsx`, 'xlsx')"
        >
          <v-icon v-if="downloading" class="mdi-spin"> mdi-rotate-right </v-icon>
          <v-icon v-else> mdi-file-excel </v-icon>
        </v-btn>
        <v-btn v-if="feature('download-sdf')" title="Download SDF" @click="downloadItem(`${item.name}.sdf`, 'sdf')">
          <v-icon v-if="downloading" class="mdi-spin"> mdi-rotate-right </v-icon>
          <v-icon v-else> mdi-download </v-icon>
        </v-btn>
      </v-btn-toggle>
    </v-toolbar>

    <v-data-table
      v-if="view !== 1"
      :footer-props="{ showFirstLastPage: true, itemsPerPageOptions: [10, 20, 50, -1] }"
      :headers="headers"
      :items="item.records"
      :search="search"
    >
      <template v-slot:item.original="{ item }">
        <img :id="`org-${item.mol_org.$oid}`" :src="`${API_URL}render/${item.mol_org.$oid}`" alt="" />
        <chem-popover :delay="500" :record="item.mol_org.$oid" :size="400" :target="`org-${item.mol_org.$oid}`" />
      </template>

      <template v-slot:item.stdized="{ item }">
        <template v-if="item.mol_std">
          <img :id="`std-${item.mol_std.$oid}`" :src="`${API_URL}render/${item.mol_std.$oid}`" alt="" />
          <chem-popover :delay="500" :record="item.mol_std.$oid" :size="400" :target="`std-${item.mol_std.$oid}`" />
        </template>
      </template>

      <template v-slot:item.file_fields="{ item }">
        <div v-for="(v, n, i) in item.file_fields" :key="`${i}`" class="data-fields">
          <span>{{ n }}: </span>
          <span :title="v">{{ truncate(v, 15) }}</span>
        </div>
      </template>

      <template v-slot:item.ds_fields="{ item }">
        <div v-for="(v, n, i) in item.ds_fields" :key="`${i}`" class="data-fields">
          <span>{{ n }}: </span>
          <span :title="v">{{ truncate(v, 15) }}</span>
        </div>
      </template>

      <template v-slot:item.issues="{ item }">
        <div v-for="(issue, i) in filteredIssues(item.issues)" :key="`${i}`" class="wrap-300">
          <span style="font-style: italic">{{ issue.severity }}: </span>
          <span>{{ issue.message }}</span>
        </div>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
import ChemPopover from '@/components/ChemPopover';
import ViewBase from '@/components/ViewBase';

export default {
  components: { ChemPopover },

  mixins: [ViewBase],

  data: () => ({
    headers: [
      { text: 'Record', value: 'ord' },
      { text: 'Original', value: 'original', sortable: false, filterable: false },
      { text: 'File fields', value: 'file_fields', sortable: false },
      { text: 'Issues', value: 'issues', sortable: false },
      { text: 'Dataset fields', value: 'ds_fields', sortable: false },
      { text: 'Standardized', value: 'stdized', sortable: false, filterable: false },
    ],
    debug: false,
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'protocols';
    },
  },

  methods: {
    truncate(str, n, useWordBoundary) {
      if (str == null) return str;
      if (typeof str !== 'string') str = str.toString();
      if (str.length <= n) return str;

      const subString = str.substr(0, n - 1); // the original check
      return (useWordBoundary ? subString.substr(0, subString.lastIndexOf(' ')) : subString) + '...';
    },
    filteredIssues(issues) {
      return this.debug ? issues : issues.filter((i) => i.severity !== 'Debug');
    },
  },
};
</script>

<style lang="scss" scoped>
.data-fields {
  font-size: smaller;
  white-space: nowrap;
}
</style>
