<template>
  <v-card>
    <v-expansion-panels>
      <v-expansion-panel>
        <v-expansion-panel-header>
          {{ item.name }}
          <v-spacer />
          <span>
            <v-badge :content="statsText" color="blue lighten-2" overlap>
              <v-chip small>{{ item.records_number }}</v-chip>
            </v-badge>
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
            <v-row v-if="canWrite()">
              <v-spacer></v-spacer>
              <FileDialog
                v-if="canWrite() && feature('metadata-edit')"
                :allow-create="false"
                :item.sync="item"
                button-title="Edit"
                item-type="datasets"
              />
            </v-row>
          </v-container>
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>

    <v-toolbar>
      <v-btn v-if="Object.keys($route.params).length !== 0" class="mr-3" title="Back" @click="$router.go(-1)">
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

      <v-btn-toggle v-if="feature('view-tile')" v-model="view" class="mr-2" dense>
        <v-btn title="Table View">
          <v-icon>mdi-format-list-checkbox</v-icon>
        </v-btn>
        <v-btn title="Grid View">
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
            <v-btn title="Go to file" v-bind="attrs" v-on="on">
              <v-icon> mdi-file</v-icon>
            </v-btn>
          </template>
          <v-list>
            <v-list-item v-for="(file, i) in item.files" :key="file.$oid" @click="$router.push(`/files/${file.$oid}`)">
              <v-list-item-title v-text="`file-${i}`" />
            </v-list-item>
          </v-list>
        </v-menu>
        <v-btn
          v-if="feature('download-xlsx')"
          title="Export to Excel"
          @click="downloadItem(`${item.name}.xlsx`, 'xlsx')"
        >
          <v-icon v-if="downloading" class="mdi-spin"> mdi-rotate-right</v-icon>
          <v-icon v-else> mdi-file-excel</v-icon>
        </v-btn>
        <v-btn v-if="feature('download-sdf')" title="Download SDF" @click="downloadItem(`${item.name}.sdf`)">
          <v-icon v-if="downloading" class="mdi-spin"> mdi-rotate-right</v-icon>
          <v-icon v-else> mdi-download</v-icon>
        </v-btn>
      </v-btn-toggle>

      <v-btn-toggle dense>
        <ModelDialog
          v-if="canTrain && isReadyForModel"
          :datasets="[item]"
          button-title="mdi-sitemap"
          title="Train Models"
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
        <img :id="`${item.id}`" :src="`${API_URL}render/${item.id}`" alt="" />
        <chem-popover :record="item" :target="`${item.id}`" />
      </template>
      <template #item.single-class-label="{ item }">
        <v-chip :color="getActivityColor(item['single-class-label'])" small />
      </template>
      <template #item.continuous-value="{ item }">
        {{ item['continuous-value'] | number('0.000') }}
      </template>
    </v-data-table>

    <v-container v-else>
      <records-tile :recordset="item" />
    </v-container>
  </v-card>
</template>

<script>
import RecordsTile from '@/components/RecordsTile';
import ChemPopover from '@/components/ChemPopover';
import FileDialog from '@/components/FileDialog';
import ModelDialog from '@/components/ModelDialog';
import DeleteDialog from '@/components/DeleteDialog';
import ViewBase from '@/components/ViewBase';
import ACLDialog from '@/components/auth/ACLDialog';
import { getActivityColor } from '@/main';

export default {
  components: { ACLDialog, ChemPopover, RecordsTile, FileDialog, ModelDialog, DeleteDialog },

  mixins: [ViewBase],

  data: () => ({
    //
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'datasets';
    },
    headers() {
      return this.headersTypes;
    },
    isReadyForModel() {
      return this.item.fields_mapping.find((f) =>
        ['single-class-label', 'multi-class-label', 'continuous-value'].includes(f.type)
      );
    },
    statsText() {
      if (!this.item.stats) return '';
      if (this.item.stats.actives) return `${this.item.stats.actives}/${this.item.stats.inactives}`;
      if (this.item.stats.high_value)
        return `${this.roundup(this.item.stats.low_value, 2)}-${this.roundup(this.item.stats.high_value, 2)}`;
      return '';
    },
  },

  methods: {
    getActivityColor(value) {
      return getActivityColor(value);
    },
  },
};
</script>
