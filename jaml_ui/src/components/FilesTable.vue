<template>
  <v-card>
    <v-data-table
      v-model="selected"
      :footer-props="{ showFirstLastPage: true, itemsPerPageOptions: [10, 20, 50, -1] }"
      :headers="headers"
      :hide-default-footer="items.length < 10"
      :items="items"
      :items-per-page="50"
      :search="search"
      :show-select="selectable"
      item-key="name"
    >
      <template #top>
        <v-toolbar class="mb-3">
          <v-text-field
            v-if="feature('table-search')"
            v-model="search"
            append-icon="mdi-magnify"
            hide-details
            label="Search in any field"
            single-line
          />

          <v-spacer />

          <v-switch v-if="isAuthenticated && isSelectable" v-model="selectable" class="mt-5 mr-4" label="Select" />

          <v-btn-toggle class="mr-2">
            <v-btn
              v-if="isAuthenticated && selectable && feature('download-multi')"
              :disabled="!selected.length"
              class="mr-3"
              title="Download selected files"
              @click="downloadFiles(selected)"
            >
              <v-icon v-if="downloading" class="mdi-spin"> mdi-rotate-right</v-icon>
              <v-icon v-else> mdi-download</v-icon>
            </v-btn>
          </v-btn-toggle>

          <v-btn-toggle>
            <FileDialog
              v-if="canCreate"
              v-model="visibleFile"
              :disabled="selectable"
              :item.sync="item"
              :on-button-activate="resetItem"
              :visible="!selectable"
              button-title="mdi-upload"
              item-type="files"
              @uploaded="onUploaded"
            />
            <HeadersDialog
              v-if="feature('table-headers')"
              :available-headers="availableHeaders"
              :headers.sync="headers"
            />
            <DatasetDialog
              v-if="canCreate && (!selectable || feature('create-batch') || feature('create-combine'))"
              v-model="visibleDataset"
              :disabled="!selected.length"
              :files="selected"
              :visible="selectable"
              button-title="mdi-table-large"
              title="Create dataset(s)"
              type="datasets"
              @click="createDataset(selected)"
            />
            <DatasetDialog
              v-if="canCreate && (!selectable || feature('create-batch') || feature('create-combine'))"
              v-model="visiblePredict"
              :disabled="!selected.length"
              :files="selected"
              :visible="selectable"
              button-title="mdi-timetable"
              title="Create resultset(s)"
              type="resultsets"
              @click="createPredictset(selected)"
            />
            <DeleteDialog
              v-if="isAuthenticated && (!selectable || feature('delete-multi'))"
              v-model="visibleDelete"
              :disabled="!selected.length"
              :items="selected"
              :visible="selectable"
              button-title="mdi-delete"
              object-type="files"
              title="Delete selected files"
              @click="deleteItems(selected)"
              @deleted="removeItems"
            />
          </v-btn-toggle>
        </v-toolbar>
      </template>

      <template #item.name="{ item }">
        <b-link :title="item.name" :to="`/${OBJECTS_TYPE}/${item._id.$oid}`" class="wrap-500">{{ item.name }}</b-link>
      </template>

      <template #item.project="{ item }">
        {{ item.metadata.project }}
      </template>
      <template #item.measurementType="{ item }">
        {{ item.metadata.measurementType }}
      </template>
      <template #item.target="{ item }">
        {{ item.metadata.target }}
      </template>
      <template #item.organism="{ item }">
        {{ item.metadata.organism }}
      </template>

      <template #item.metadata="{ item }">
        <div :id="item._id.$oid">
          <div v-for="n in metadata" :key="n">
            <div v-if="item.metadata[n]">
              <span>{{ item.metadata[n] }}</span>
            </div>
          </div>
          <MetadataPopover :item="item" :target="item._id.$oid"></MetadataPopover>
        </div>
      </template>

      <template #item.size="{ item }">
        <div style="white-space: nowrap">{{ item.size | bytes }}</div>
      </template>

      <template #item.records_number="{ item }">
        <v-chip>{{ item.records_number }}</v-chip>
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

      <template #item.fields="{ item }">
        <v-chip v-for="(field, i) in item.fields" :key="`f${i}`" class="ma-1" label outlined small>
          {{ field }}
        </v-chip>
      </template>

      <template v-if="!selectable" #item.actions="{ item }">
        <div class="justify-end mr-0">
          <v-icon v-if="canWrite(item) && feature('metadata-edit')" class="mr-1" title="Edit" @click="editItem(item)">
            mdi-pencil
          </v-icon>
          <v-icon v-if="canCreate && canRead(item)" class="mr-1" title="Create Dataset" @click="createDataset([item])">
            mdi-table-large
          </v-icon>
          <v-icon
            v-if="canCreate && canRead(item)"
            class="mr-1"
            title="Create Predictions"
            @click="createPredictset([item])"
          >
            mdi-timetable
          </v-icon>
          <v-icon v-if="canDelete(item)" title="Delete" @click="deleteItems([item])"> mdi-delete</v-icon>
        </div>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
import { download, getDatedFilename } from '@/main';
import DeleteDialog from '@/components/DeleteDialog';
import DatasetDialog from '@/components/DatasetDialog';
import MetadataPopover from '@/components/MetadataPopover';
import FileDialog from '@/components/FileDialog';
import TableBase from '@/components/TableBase';
import HeadersDialog from '@/components/HeadersDialog';

export default {
  components: { HeadersDialog, FileDialog, MetadataPopover, DatasetDialog, DeleteDialog },

  mixins: [TableBase],

  data: () => ({
    metadata: ['title', 'project', 'description', 'measurementType', 'target', 'organism'],
    allHeaders: [
      { text: 'Name', value: 'name' },
      { text: 'Information', value: 'metadata', sortable: false, initial: false },
      { text: 'Project', value: 'project', initial: false },
      { text: 'Measurement Type', value: 'measurementType', initial: false },
      { text: 'Target', value: 'target', initial: false },
      { text: 'Organism', value: 'organism', initial: false },
      { text: 'Size', value: 'size', align: 'end' },
      { text: 'Records', value: 'records_number', align: 'end' },
      { text: 'Fields', value: 'fields', sortable: false },
      { text: 'Access', value: 'access', initial: false, authenticated: true },
      { text: 'Owner', value: 'owner', initial: false, authenticated: true },
      { text: 'Rights', value: 'rights', sortable: false, initial: false, admin: true },
      { text: 'Created', value: 'dateCreated', initial: false },
      { text: 'Actions', value: 'actions', sortable: false, align: 'end', fixed: true, authenticated: true },
    ],
    visibleFile: false,
    visibleDataset: false,
    visiblePredict: false,
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'files';
    },
    isSelectable() {
      return (
        this.feature('download-multi') ||
        this.feature('create-batch') ||
        this.feature('create-combine') ||
        this.feature('delete-multi')
      );
    },
  },

  methods: {
    resetItem() {
      this.item = null;
    },
    onUploaded(files) {
      this.items.push(...files);
    },
    editItem(file) {
      this.item = file;
      this.visibleFile = true;
    },
    createDataset(files) {
      this.selected = files;
      this.visibleDataset = true;
    },
    createPredictset(items) {
      this.selected = items;
      this.visiblePredict = true;
    },
    downloadFiles(files) {
      this.downloading = true;
      this.$axios
        .post(`${this.OBJECTS_TYPE}/download`, { ids: files.map((f) => f._id.$oid) }, { responseType: 'blob' })
        .then((response) => {
          this.downloading = false;
          let filename = getDatedFilename(this.OBJECTS_TYPE, 'zip');
          download(filename, response.data);
        })
        .catch(() => (this.downloading = false));
    },
  },
};
</script>
