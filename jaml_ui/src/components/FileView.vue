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
            <v-row dense>
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
                item-type="files"
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
        <v-btn>
          <v-icon>mdi-format-list-checkbox</v-icon>
        </v-btn>
        <v-btn>
          <v-icon>mdi-grid</v-icon>
        </v-btn>
      </v-btn-toggle>

      <v-btn-toggle class="mr-2" dense>
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
        <DatasetDialog
          v-if="canCreate"
          :files="[item]"
          button-title="mdi-table-large"
          title="Create Dataset"
          type="datasets"
        />
        <DatasetDialog
          v-if="canCreate"
          :files="[item]"
          button-title="mdi-timetable"
          title="Create Predictions"
          type="resultsets"
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
      <template v-slot:item.image="{ item }">
        <img :id="`${item.id}`" :src="`${API_URL}render/${item.id}`" alt="" />
        <chem-popover :record="item" :target="`${item.id}`"></chem-popover>
      </template>
    </v-data-table>

    <v-container v-else>
      <records-tile :recordset="item"></records-tile>
    </v-container>
  </v-card>
</template>

<script>
import DatasetDialog from '@/components/DatasetDialog';
import DeleteDialog from '@/components/DeleteDialog';
import RecordsTile from '@/components/RecordsTile';
import ChemPopover from '@/components/ChemPopover';
import FileDialog from '@/components/FileDialog';
import ViewBase from '@/components/ViewBase';
import ACLDialog from '@/components/auth/ACLDialog';

export default {
  components: { ACLDialog, FileDialog, ChemPopover, DatasetDialog, DeleteDialog, RecordsTile },

  mixins: [ViewBase],

  data: () => ({
    //
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'files';
    },
    headers() {
      return this.headersFields;
    },
  },
};
</script>
