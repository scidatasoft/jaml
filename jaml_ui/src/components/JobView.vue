<template>
  <v-card>
    <v-toolbar>
      <v-btn v-if="Object.keys($route.params).length !== 0" class="mr-3" title="Back" @click="$router.go(-1)">
        <v-icon>mdi-arrow-up</v-icon>
      </v-btn>

      {{ item.error }}

      <v-spacer />

      <v-chip :color="getStatusColor(item.status)" class="mr-4" small>{{ item.status }}</v-chip>

      <v-btn-toggle dense>
        <v-btn title="Go to Dataset" @click="$router.push(`/datasets/${item.params.ds_id}`)">
          <v-icon>mdi-table-large</v-icon>
        </v-btn>
        <v-btn v-if="item.model_id" title="Go to Model" @click="$router.push(`/model/${item.model_id}`)">
          <v-icon>mdi-sitemap</v-icon>
        </v-btn>
        <v-btn
          v-if="item.status === 'Failed' || item.status === 'Done'"
          title="Re-run"
          @click="changeStatus('Rescheduled')"
        >
          <v-icon>mdi-reload</v-icon>
        </v-btn>
      </v-btn-toggle>
    </v-toolbar>

    <v-container v-if="item && item.params" class="mt-6">
      <v-row>
        <v-col cols="5">
          <v-text-field v-model="item.params.name" class="ma-0" label="Model" readonly />
        </v-col>
        <v-col cols="5">
          <v-text-field v-model="item.params.ds_name" class="ma-0" label="Dataset" readonly />
        </v-col>
        <v-col cols="2">
          <v-text-field v-model="item.params.method" class="ma-0" label="Method" readonly />
        </v-col>
        <v-col>
          <v-text-field v-model="descriptors" class="ma-0" label="Descriptors" readonly />
        </v-col>
        <v-col cols="3">
          <v-text-field v-model="item.server_name" class="ma-0" label="Server" readonly />
        </v-col>
        <v-col cols="3">
          <v-text-field v-model="item.container_name" class="ma-0" label="Container" readonly />
        </v-col>
      </v-row>
    </v-container>

    <v-expansion-panels>
      <v-expansion-panel v-if="item.stdout">
        <v-expansion-panel-header> Job output</v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-textarea v-model="item.stdout" auto-grow class="small-text" dense label="Job output" readonly />
        </v-expansion-panel-content>
      </v-expansion-panel>

      <v-expansion-panel v-if="item.stderr">
        <v-expansion-panel-header> Error output</v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-textarea v-model="item.stderr" auto-grow class="small-text" dense label="Error output" readonly />
        </v-expansion-panel-content>
      </v-expansion-panel>

      <v-expansion-panel v-if="item.stack_trace">
        <v-expansion-panel-header> Stack Trace</v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-textarea v-model="item.stack_trace" auto-grow class="small-text" dense label="Stack Trace" readonly />
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-card>
</template>

<script>
import ViewBase from '@/components/ViewBase';

export default {
  mixins: [ViewBase],

  data: () => ({
    //
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'jobs';
    },
    AUTO_REFRESH() {
      return 5000;
    },
    descriptors() {
      return JSON.stringify(this.item.params.descriptors);
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
    changeStatus(status) {
      this.$axios.put(`${this.OBJECTS_TYPE}/${this.item._id.$oid}`, { status: status }).then(() => {
        this.$router.go();
      });
    },
  },
};
</script>
<style lang="scss" scoped>
.small-text {
  font-size: small;
}
</style>
