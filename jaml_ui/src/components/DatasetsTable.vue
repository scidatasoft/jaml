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

          <v-switch v-if="isAuthenticated && isSelectable" v-model="selectable" class="mt-4 mr-4" label="Select" />

          <v-btn-toggle>
            <HeadersDialog
              v-if="feature('table-headers')"
              :available-headers="availableHeaders"
              :headers.sync="headers"
            />
            <ModelDialog
              v-if="canTrain && (!selectable || feature('train-multi'))"
              v-model="visibleCreateModels"
              :datasets="selected"
              :disabled="!selected.length"
              :visible="selectable"
              button-title="mdi-sitemap"
              @click="createModels(selected)"
            />
            <DeleteDialog
              v-if="isAuthenticated && (!selectable || feature('delete-multi'))"
              v-model="visibleDelete"
              :disabled="!selected.length"
              :items="selected"
              :visible="selectable"
              button-title="mdi-delete"
              object-type="datasets"
              @click="deleteItems(selected)"
              @deleted="removeItems"
            />
          </v-btn-toggle>
        </v-toolbar>
      </template>

      <template #item.name="{ item }">
        <div>
          <b-link :title="item.name" :to="`/${OBJECTS_TYPE}/${item._id.$oid}`">{{ item.name }}</b-link>
        </div>
      </template>

      <template #item.file="{ item }">
        <div>
          <b-link :to="`/files/${item.files[0].$oid}`" class="no-link-under">
            <v-icon> mdi-file-document </v-icon>
          </b-link>
        </div>
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

      <template #item.records_number="{ item }">
        <v-badge :content="statsText(item)" color="blue lighten-2" overlap>
          <v-chip>{{ item.records_number }}</v-chip>
        </v-badge>
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

      <template #item.fields_mapping="{ item }">
        <v-chip
          v-for="(field, i) in item.fields_mapping.filter((f) => f.type)"
          :key="i"
          class="ma-1"
          label
          outlined
          small
        >
          {{ field.type }}
        </v-chip>
      </template>

      <template v-if="!selectable" #item.actions="{ item }">
        <div class="justify-end mr-0">
          <v-icon
            v-if="canTrain && canRead(item) && isReadyForModel(item)"
            :disabled="selectable"
            class="mr-2"
            title="Train Models"
            @click="createModels([item])"
          >
            mdi-sitemap
          </v-icon>
          <v-icon v-if="canDelete(item)" :disabled="selectable" title="Delete" @click="deleteItems([item])">
            mdi-delete
          </v-icon>
        </div>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
import DeleteDialog from '@/components/DeleteDialog';
import ModelDialog from '@/components/ModelDialog';
import MetadataPopover from '@/components/MetadataPopover';
import TableBase from '@/components/TableBase';
import HeadersDialog from '@/components/HeadersDialog';

export default {
  components: { MetadataPopover, DeleteDialog, ModelDialog, HeadersDialog },

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
      { text: 'Records', value: 'records_number', align: 'end' },
      { text: 'Fields', value: 'fields_mapping', sortable: false, align: 'end' },
      { text: 'Access', value: 'access', initial: false, authenticated: true },
      { text: 'Owner', value: 'owner', initial: false, authenticated: true },
      { text: 'Rights', value: 'rights', sortable: false, initial: false, admin: true },
      { text: 'Created', value: 'dateCreated', initial: false },
      { text: 'Actions', value: 'actions', sortable: false, align: 'end', fixed: true, authenticated: true },
    ],

    visibleCreateModels: false,
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'datasets';
    },
    isSelectable() {
      return this.feature('train-multi') || this.feature('delete-multi');
    },
  },

  methods: {
    statsText(item) {
      if (!item.stats) return '';
      if (item.stats.actives) return `${item.stats.actives}/${item.stats.inactives}`;
      if (item.stats.high_value)
        return `${this.roundup(item.stats.low_value, 2)}-${this.roundup(item.stats.high_value, 2)}`;
      return '';
    },
    isReadyForModel(dataset) {
      return dataset.fields_mapping.find((f) =>
        ['single-class-label', 'multi-class-label', 'continuous-value'].includes(f.type)
      );
    },
    createModels(items) {
      this.selected = items;
      this.visibleCreateModels = true;
    },
  },
};
</script>
