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
      item-key="id"
      sort-by="dateCreated"
      sort-desc
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

          <v-switch v-model="selectable" class="mt-6 mr-5" label="Select" />

          <v-chip
            v-for="s in Object.keys(statuses)"
            :key="s"
            :close="status != null"
            :color="getStatusColor(s)"
            :to="`/jobs?status=${s}`"
            class="mr-4 no-link-under"
            @click:close="$router.push('/jobs')"
          >
            <span :title="s">{{ statuses[s] }}</span>
          </v-chip>

          <v-btn-toggle class="mr-2">
            <v-btn class="mr-3" title="Download jobs" @click="downloadJobs()">
              <v-icon v-if="downloading" class="mdi-spin"> mdi-rotate-right </v-icon>
              <v-icon v-else> mdi-file-excel </v-icon>
            </v-btn>
          </v-btn-toggle>

          <v-btn-toggle>
            <HeadersDialog
              v-if="feature('table-headers')"
              :available-headers="availableHeaders"
              :headers.sync="headers"
            />
            <DeleteDialog
              v-if="isAuthenticated"
              v-model="visibleDelete"
              :disabled="!selected.length"
              :items="selected"
              :visible="selectable"
              button-title="mdi-delete"
              object-type="jobs"
              title="Delete selected jobs"
              @click="deleteItems(selected)"
              @deleted="removeItems"
            />
            <v-menu offset-y>
              <template v-slot:activator="{ attrs, on }">
                <v-btn v-bind="attrs" v-on="on">
                  <v-icon> mdi-playlist-remove </v-icon>
                </v-btn>
              </template>
              <v-list>
                <v-list-item v-for="item in what2delete" :key="item.value" link @click="cleanJobs(item.value)">
                  <v-list-item-title v-text="item.title" />
                </v-list-item>
              </v-list>
            </v-menu>
          </v-btn-toggle>
        </v-toolbar>
      </template>

      <template #item.job_type="{ item }">
        <v-chip outlined small>
          {{ item.job_type }}
        </v-chip>
      </template>

      <template #item.result="{ item }">
        <div v-if="item.job_type === 'train'" class="wrap-300">
          <b-link
            v-if="item.model_id && item.params.model_name"
            :to="`/models/${encodeURIComponent(item.params.model_name)}`"
            class="wrap-300"
          >
            {{ item.params.model_name }}
          </b-link>
          <b-link v-else-if="item.model_id" :to="`/model/${item.model_id}`">
            {{ item.params.method }}
          </b-link>
        </div>
        <div v-else-if="item.job_type === 'predict'" class="wrap-300">
          <b-link v-if="item.rs_id" :to="`/resultsets/${item.rs_id}`"> Predictions </b-link>
        </div>
      </template>

      <template #item.dataset="{ item }">
        <div>
          <b-link :title="item.model" :to="`/datasets/${item.params.ds_id}`" class="wrap-300">
            {{ item.dataset }}
          </b-link>
        </div>
      </template>

      <template #item.method="{ item }">
        <b-link v-if="item.model_id" :to="`/model/${item.model_id}`">
          {{ item.method }}
        </b-link>
        <span v-else>{{ item.method }}</span>
      </template>

      <template #item.status="{ item }">
        <v-tooltip v-if="item.status === 'Failed'" bottom>
          <template v-slot:activator="{ on, attrs }">
            <v-chip
              :color="getStatusColor(item.status)"
              :to="`/jobs/${item._id.$oid}`"
              class="no-link-under"
              small
              v-bind="attrs"
              v-on="on"
            >
              {{ item.status }}
            </v-chip>
          </template>
          {{ item.error }}
        </v-tooltip>
        <v-chip v-else :color="getStatusColor(item.status)" :to="`/jobs/${item._id.$oid}`" class="no-link-under" small>
          {{ item.status }}
        </v-chip>
      </template>

      <template v-slot:item.execution_time="{ item }">
        {{ item.stats.execution_time ? roundup(item.stats.execution_time, 1) : '' }}
      </template>

      <template #item.owner="{ item }">
        {{ item.acl ? getUser(item.acl.owner) : '' }}
      </template>

      <template #item.dateCreated="{ item }">
        <span class="text-no-wrap">
          {{ dateTimeFormat.format(item.dateCreated) }}
        </span>
      </template>

      <template #item.actions="{ item }">
        <div class="justify-end mr-0">
          <v-icon v-if="canDelete(item)" title="Delete" @click="deleteItems([item])"> mdi-delete </v-icon>
        </div>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
import TableBase from '@/components/TableBase';

import HeadersDialog from '@/components/HeadersDialog';
import DeleteDialog from '@/components/DeleteDialog';
import { download, getDatedFilename } from '@/main';

export default {
  components: { DeleteDialog, HeadersDialog },

  mixins: [TableBase],

  data: () => ({
    statuses: [],
    allHeaders: [
      { text: 'Type', value: 'job_type' },
      { text: 'Status', value: 'status', align: 'center', fixed: true },
      { text: 'Server', value: 'server_name' },
      { text: 'Container', value: 'container_name' },
      { text: 'Result', value: 'result' },
      { text: 'Dataset', value: 'dataset' },
      { text: 'Method', value: 'method' },
      { text: 'Time, s', value: 'execution_time', align: 'end' },
      { text: 'Owner', value: 'owner', initial: false, authenticated: true },
      { text: 'Created', value: 'dateCreated', initial: false },
      { text: 'Actions', value: 'actions', sortable: false, align: 'end', groupable: false, fixed: true },
    ],
    what2delete: [
      { value: 'old-1', title: 'Older than 1 hour' },
      { value: 'old-12', title: 'Older than 12 hours' },
      { value: 'old-24', title: 'Older than 1 day' },
      { value: 'old-72', title: 'Older than 3 days' },
      { value: 'Failed', title: 'Failed' },
      { value: 'Done', title: 'Done' },
      { value: 'All', title: 'All' },
    ],
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'jobs';
    },
    QUERY() {
      return this.status ? `?status=${this.status}` : '';
    },
    status() {
      return this.$route.query.status;
    },
  },

  watch: {
    items() {
      this.statuses = this.items.reduce((acc, item) => {
        if (item.status in acc) acc[item.status]++;
        else acc[item.status] = 1;
        return acc;
      }, {});
    },
    status() {
      this.getData();
    },
  },

  methods: {
    getStatusColor(status) {
      switch (status) {
        case 'Created':
        case 'Rescheduled':
          return 'grey lighten-3';
        case 'Running':
          return 'green lighten-4';
        case 'Done':
          return 'green lighten-2';
        case 'Failed':
          return 'red lighten-2';
      }
    },
    postProcessData(s) {
      s.model = s.params.name;
      s.dataset = s.params.ds_name;
      s.method = s.params.method;
      s.name = `${s.model}/${s.method}`;
      if (s.params.rs_ids && s.params.rs_ids[0]) s.rs_id = s.params.rs_ids[0];
      s.id = s._id.$oid;
    },
    cleanJobs(what) {
      this.$axios.delete(`${this.OBJECTS_TYPE}?what=${what}`).then(() => this.getData());
    },
    downloadJobs() {
      this.downloading = true;
      this.$axios
        .post(
          `${this.OBJECTS_TYPE}/download`,
          {
            status: this.status,
            ids: [],
          },
          { responseType: 'blob' }
        )
        .then((response) => {
          this.downloading = false;
          let filename = getDatedFilename(this.OBJECTS_TYPE, 'xlsx');
          download(filename, response.data);
        })
        .catch(() => (this.downloading = false));
    },
  },
};
</script>
