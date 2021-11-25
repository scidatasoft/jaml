<template>
  <v-card>
    <v-expansion-panels>
      <v-expansion-panel>
        <v-expansion-panel-header>
          {{ item.name }}
          <v-spacer />
          <span>
            <v-chip small>{{ item.records_number }}</v-chip>
          </span>
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-container>
            <v-row>
              <v-col cols="6">
                <v-text-field v-model="item.metadata.project" class="ma-0" label="Project" readonly />
              </v-col>
              <v-col cols="2">
                <v-text-field v-model="item.metadata.measurementType" class="ma-0" label="Measurement Type" readonly />
              </v-col>
              <v-col cols="2">
                <v-text-field v-model="item.metadata.target" class="ma-0" label="Target" readonly />
              </v-col>
              <v-col cols="2">
                <v-text-field v-model="item.metadata.organism" class="ma-0" label="Organism" readonly />
              </v-col>
              <v-col cols="12">
                <v-textarea v-model="item.metadata.description" class="ma-0" label="Description" readonly />
              </v-col>
            </v-row>
            <v-row>
              <v-spacer />
              <FileDialog
                v-if="canWrite() && feature('metadata-edit')"
                :allow-create="false"
                :item.sync="item"
                button-title="Edit"
                item-type="resultsets"
              />
            </v-row>
          </v-container>
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>

    <v-toolbar>
      <v-btn v-if="Object.keys($route.params).length !== 0" class="mr-5" title="Back" @click="$router.go(-1)">
        <v-icon>mdi-arrow-up</v-icon>
      </v-btn>

      <v-text-field
        v-if="isFilterable && feature('table-search')"
        v-model="search"
        append-icon="mdi-magnify"
        class="mr-3"
        hide-details
        label="Search in any field"
        single-line
      ></v-text-field>

      <v-spacer></v-spacer>

      <v-switch v-if="view !== 1" v-model="average" class="mt-6 mr-4" label="Average" />

      <v-btn-toggle v-if="feature('view-tile')" v-model="view" class="mr-2" dense>
        <v-btn>
          <v-icon>mdi-format-list-checkbox</v-icon>
        </v-btn>
        <v-btn>
          <v-icon>mdi-grid</v-icon>
        </v-btn>
      </v-btn-toggle>

      <v-btn-toggle class="mr-2" dense>
        <v-btn
          v-if="item.protocol && item.protocol.$oid"
          title="Protocol"
          @click="$router.push(`/protocols/${item.protocol.$oid}`)"
        >
          <v-icon>mdi-book-open</v-icon>
        </v-btn>
        <v-menu v-if="feature('navigate')" offset-y>
          <template v-slot:activator="{ attrs, on }">
            <v-btn title="Go to files" v-bind="attrs" v-on="on">
              <v-icon> mdi-file </v-icon>
            </v-btn>
          </template>
          <v-list>
            <v-list-item v-for="(file, i) in item.files" :key="file.$oid" @click="$router.push(`/files/${file.$oid}`)">
              <v-list-item-title v-text="`file-${i}`" />
            </v-list-item>
          </v-list>
        </v-menu>
        <v-btn
          v-if="item.valid_stats && item.valid_stats.length && feature('resultset-validations-view')"
          title="Validations"
          @click="$router.push(`${$route.path}/validations`)"
        >
          <v-icon>mdi-chart-areaspline</v-icon>
        </v-btn>
        <v-btn
          v-if="feature('download-xlsx')"
          title="Export to Excel"
          @click="downloadItem(`${item.name}.xlsx`, 'xlsx')"
        >
          <v-icon v-if="downloading" class="mdi-spin"> mdi-rotate-right </v-icon>
          <v-icon v-else> mdi-file-excel </v-icon>
        </v-btn>
        <v-btn
          v-if="feature('download-xlsx')"
          title="Download SDF"
          @click="downloadItem(`${item.name}.sdf`, 'sdf')"
        >
          <v-icon v-if="downloading" class="mdi-spin"> mdi-rotate-right </v-icon>
          <v-icon v-else> mdi-download </v-icon>
        </v-btn>
      </v-btn-toggle>

      <v-btn-toggle dense>
        <PredictDialog
          v-if="canPredict"
          :dataset="item"
          button-title="mdi-timetable"
          title="Predict"
          @predicted="getData()"
        />
        <ACLDialog
          v-if="canACL()"
          :item.sync="item"
          :type="OBJECTS_TYPE"
          button-title="mdi-account-key"
          title="Access Control"
        />
        <DeleteDialog
          v-if="canDelete()"
          :items="[item]"
          :object-type="OBJECTS_TYPE"
          button-title="mdi-delete"
          title="Delete"
          @deleted="$router.push(`/${OBJECTS_TYPE}`)"
        />
      </v-btn-toggle>
    </v-toolbar>

    <v-data-table
      v-if="view !== 1"
      :footer-props="{ showFirstLastPage: true, itemsPerPageOptions: [10, 20, 50, -1] }"
      :headers="headers"
      :items="items"
      :search="search"
    >
      <template #item.image="{ item }">
        <img :id="`i${item.id}`" :src="`${API_URL}render/${item.id}`" alt="" />
        <chem-popover :record="item" :target="`i${item.id}`"></chem-popover>
      </template>

      <template #item="{ item }">
        <tr>
          <td>
            <img :id="`i${item.id}`" :src="`${API_URL}render/${item.id}`" alt="" />
            <chem-popover :record="item" :target="`i${item.id}`"></chem-popover>
          </td>
          <td v-for="(h, i) in dataHeaders" :key="`${h.value}-${i}`" align="center">
            <template v-if="isValueHeader(h)">
              <v-chip
                v-if="isBinaryHeader(item, h)"
                :color="getPredictionColor(item[h.value])"
                :small="isMappedValueHeader(h)"
                :x-small="isPredictedHeader(h)"
              />
              <span v-else>{{ roundup(item[h.value], 3) }}</span>
            </template>
            <span v-else>{{ item[h.value] }}</span>
          </td>
        </tr>
      </template>
    </v-data-table>

    <v-container v-else>
      <records-tile :recordset="item"></records-tile>
    </v-container>
  </v-card>
</template>

<script>
import RecordsTile from '@/components/RecordsTile';
import ChemPopover from '@/components/ChemPopover';
import PredictDialog from '@/components/PredictDialog';
import DeleteDialog from '@/components/DeleteDialog';
import FileDialog from '@/components/FileDialog';
import ViewBase from '@/components/ViewBase';
import ACLDialog from '@/components/auth/ACLDialog';

export default {
  components: { FileDialog, ACLDialog, ChemPopover, RecordsTile, PredictDialog, DeleteDialog },

  mixins: [ViewBase],

  data: () => ({
    average: true,
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'resultsets';
    },
    headers() {
      return [{ text: 'Structure', value: 'image', sortable: false, filterable: false }].concat(
        this.item.fields_mapping
          .filter((f) => f.type && (f.name.indexOf('/') === -1 || this.average === (f.name.indexOf('/avg') !== -1)))
          .map((f) => ({
            text: this.shortName(f.name),
            value: f.name,
            class: 'results-header',
            width: ['chem-id', 'chem-name'].includes(f.type) ? 100 : 50,
            align: 'center',
            filterable: ['chem-id', 'chem-name'].includes(f.type),
          }))
      );
    },
    dataHeaders() {
      return this.headers.filter((h) => h.value !== 'image');
    },
    isFilterable() {
      return this.dataHeaders.filter((h) => h.filterable).length;
    },
  },

  methods: {
    shortName(name) {
      if (name.indexOf('/') === -1) return name.substr(0, 10);
      else return name.substr(0, 7) + '...' + name.substr(name.indexOf('/'));
    },
    getPredictionColor(value) {
      return parseInt(value) ? 'green' : 'red lighten-3';
    },
    isBinaryHeader(item, h) {
      if (this.isMappedBinaryHeader(h)) return true;
      if (this.isMappedContinuousHeader(h)) return false;

      if (h.value.endsWith('-cls/avg')) return true;
      if (h.value.endsWith('-reg/avg')) return false;

      if (!h.value.endsWith('/avg')) return !h.value.endsWith('r');

      let base = h.value.split('/')[0];
      let hh = Object.keys(item).find((k) => k.startsWith(base + '/'));
      return !hh.endsWith('r');
    },
    isValueHeader(h) {
      return this.isMappedValueHeader(h) || this.isPredictedHeader(h);
    },
    isPredictedHeader(h) {
      return !!this.item.fields_mapping.find((f) => f.name === h.value && f.type === 'predicted-value');
    },
    isMappedValueHeader(h) {
      return this.isMappedBinaryHeader(h) || this.isMappedContinuousHeader(h);
    },
    isMappedBinaryHeader(h) {
      return !!this.item.fields_mapping.find((f) => f.name === h.value && f.type === 'single-class-label');
    },
    isMappedContinuousHeader(h) {
      return !!this.item.fields_mapping.find((f) => f.name === h.value && f.type === 'continuous-value');
    },
  },
};
</script>

<style lang="scss">
.results-header {
  span {
    width: 50px !important;

    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .rot {
    display: block;
    text-align: left;

    transform: rotate(-90deg);
    -ms-transform: rotate(-90deg);
    -webkit-transform: rotate(-90deg);
  }
}
</style>
