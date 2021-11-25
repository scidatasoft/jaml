<template>
  <v-card>
    <v-toolbar>
      <v-btn v-if="Object.keys($route.params).length !== 0" title="Back" @click="$router.go(-1)">
        <v-icon>mdi-arrow-up</v-icon>
      </v-btn>

      <span class="ma-5">
        <b-link :to="`/models/${encodeURIComponent(item.name)}`" title="Go to models ensemble">{{ item.name }}</b-link>
        / {{ item.method_name }}
      </span>

      <v-spacer />

      <v-btn-toggle dense>
        <v-menu v-if="feature('navigate')" offset-y>
          <template v-slot:activator="{ attrs, on }">
            <v-btn title="Go to File" v-bind="attrs" v-on="on">
              <v-icon> mdi-file</v-icon>
            </v-btn>
          </template>
          <v-list>
            <v-list-item
              v-for="(file, i) in item.files"
              :key="file.$oid"
              link
              @click="$router.push(`/files/${file.$oid}`)"
            >
              <v-list-item-title v-text="`file-${i}`" />
            </v-list-item>
          </v-list>
        </v-menu>
        <v-btn
          v-if="feature('navigate')"
          class="mr-2"
          title="Go to Dataset"
          @click="$router.push(`/datasets/${item.dataset.$oid}`)"
        >
          <v-icon>mdi-table-large</v-icon>
        </v-btn>
      </v-btn-toggle>
      <v-btn-toggle dense>
        <ACLDialog
          v-if="canACL()"
          :item.sync="item"
          :type="OBJECTS_TYPE"
          button-title="mdi-account-key"
          title="Access Control"
        />
        <ImputeDialog
          v-if="item.method_name === 'DL' && feature('models-impute')"
          :cls="true"
          :models="item"
          :reg="false"
          button-title="mdi-restart"
          title="Re-train model"
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

    <v-tabs v-model="tab">
      <v-tabs-slider></v-tabs-slider>
      <v-tab> Metrics</v-tab>
      <v-tab v-if="item.test_indices && item.test_indices.length"> Split</v-tab>
    </v-tabs>

    <v-tabs-items v-model="tab">
      <v-tab-item>
        <v-card flat>
          <div class="ma-3">
            <v-row dense>
              <v-col>
                <v-text-field v-model="descriptors" class="ma-0" label="Descriptors" readonly />
              </v-col>
            </v-row>
            <v-row dense>
              <v-col v-for="m in Object.keys(metrics)" :key="`${m}`">
                <div>{{ metrics[m] }}</div>
                <v-chip
                  v-if="item.metrics[m]"
                  :color="getMetricColor(m, item.metrics[m])"
                  small
                  style="font-size: unset"
                >
                  {{ item.metrics[m] | number('0.00') }}
                </v-chip>
              </v-col>
            </v-row>
            <v-row v-if="item.test_set_size" dense>
              <v-col v-for="m in Object.keys(metrics_ext)" :key="`${m}`">
                <div>{{ metrics_ext[m] }}</div>
                <v-chip
                  v-if="item.metrics[m]"
                  :color="getMetricColor(m, item.metrics[m])"
                  small
                  style="font-size: unset"
                >
                  {{ item.metrics[m] | number('0.00') }}
                </v-chip>
              </v-col>
            </v-row>
            <div v-if="item.test_set_size" class="mt-2">* external test set {{ item.test_set_size }}%</div>
          </div>
        </v-card>
        <v-card v-if="item._id && item._id.$oid" class="pa-2" style="text-align: center" tile>
          <img :src="`${API_URL}models/${item._id.$oid}/image`" alt="" />
          <img v-if="item.test_set_size" :src="`${API_URL}models/${item._id.$oid}/image?set_type=test`" alt="" />
        </v-card>
      </v-tab-item>

      <v-tab-item>
        <v-toolbar>
          <v-text-field
            v-if="feature('table-search')"
            v-model="search"
            append-icon="mdi-magnify"
            hide-details
            label="Search in any field"
            single-line
            style="max-width: 300px"
          />

          <v-spacer />

          <v-btn-toggle v-model="train" class="mr-2" dense>
            <v-btn title="Train Set">
              <v-icon>mdi-train</v-icon>
            </v-btn>
            <v-btn title="Test Set">
              <v-icon>mdi-test-tube</v-icon>
            </v-btn>
          </v-btn-toggle>

          <v-btn-toggle dense>
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
        </v-toolbar>

        <v-data-table
          :footer-props="{ showFirstLastPage: true, itemsPerPageOptions: [10, 20, 50, -1] }"
          :headers="headers"
          :items="filteredItems"
          :search="search"
        >
          <template #item.image="{ item }">
            <img :id="`${item.id}`" :src="`${API_URL}render/${item.id}`" alt="" />
            <chem-popover :record="item" :target="`${item.id}`"></chem-popover>
          </template>
          <template #item.single-class-label="{ item }">
            <v-chip :color="getActivityColor(item['single-class-label'])" small />
          </template>
          <template #item.continuous-value="{ item }">
            {{ item['continuous-value'] | number('0.000') }}
          </template>
        </v-data-table>
      </v-tab-item>
    </v-tabs-items>
  </v-card>
</template>

<script>
import DeleteDialog from '@/components/DeleteDialog';
import ViewBase from '@/components/ViewBase';
import ModelBase from '@/components/ModelBase';
import ACLDialog from '@/components/auth/ACLDialog';
import ImputeDialog from '@/components/ImputeDialog';
import ChemPopover from '@/components/ChemPopover';
import { getActivityColor } from '@/main';

export default {
  components: { ACLDialog, DeleteDialog, ChemPopover, ImputeDialog },

  mixins: [ViewBase, ModelBase],

  data: () => ({
    tab: 'metrics',
    train: 0,
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'models';
    },
    headers() {
      return this.headersTypes;
    },
    descriptors() {
      return JSON.stringify(this.item.descriptors);
    },
    filteredItems() {
      if (this.train === 0) return this.items.filter((i) => this.item.train_indices.includes(i.ord));
      else return this.items.filter((i) => this.item.test_indices.includes(i.ord));
    },
  },

  methods: {
    getActivityColor(value) {
      return getActivityColor(value);
    },
  },
};
</script>
