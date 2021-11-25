<template>
  <v-container>
    <v-row dense>
      <v-col v-for="(item, i) in items" :key="i">
        <v-card>
          <v-chip v-if="getActivity(item) != null" :color="getActivityColor(getActivity(item))" small />
          <v-chip v-if="getValue(item)" small>{{ roundup(getValue(item), 2) }}</v-chip>

          <div v-if="getId(item)" class="top-right">
            {{ getId(item) }}
          </div>

          <img :id="item.id" :src="`${API_URL}render/${item.id}`" alt="" />
          <chem-popover :delay="300" :record="item" :target="item.id"></chem-popover>

          <div class="bottom-right">
            <v-tooltip v-for="(act, i) in getActivities(item)" :key="i" bottom>
              <template v-slot:activator="{ on, attrs }">
                <v-chip
                  v-if="getActivity(item)"
                  :color="getActivityColor(act.activity)"
                  v-bind="attrs"
                  x-small
                  v-on="on"
                />
                <v-chip v-else v-bind="attrs" x-small v-on="on">{{ roundup(act.activity, 2) }}</v-chip>
              </template>
              <span>{{ act.name }}</span>
            </v-tooltip>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { API_URL, getActivityColor, roundup } from '@/main';
import ChemPopover from '@/components/ChemPopover';

export default {
  components: { ChemPopover },
  props: {
    recordset: {
      records: [],
    },
  },
  data: () => ({
    //
  }),

  computed: {
    API_URL: function () {
      return API_URL;
    },
    items: function () {
      return this.recordset
        ? this.recordset.records.map((r) => {
            r.fields.id = r.molecule.$oid;
            return r.fields;
          })
        : [];
    },
  },

  methods: {
    roundup(value, digits) {
      return roundup(value, digits);
    },
    getActivityColor(value) {
      return getActivityColor(value);
    },
    getId(item) {
      if (item['chem-id'] || item['chem-name']) return item['chem-id'] || item['chem-name'];

      const f = this.recordset.fields_mapping.find((f) => f.type === 'chem-id' || f.type === 'chem-name');
      if (f) return item[f.name];
    },
    getActivity: function (item) {
      if (item['single-class-label'] != null) return item['single-class-label'];

      const f = this.recordset.fields_mapping.find((f) => f.type === 'single-class-label');
      if (f) return item[f.name];
    },
    getValue: function (item) {
      if (item['continuous-value'] != null) return item['continuous-value'];

      const f = this.recordset.fields_mapping.find((f) => f.type === 'continuous-value');
      if (f) return item[f.name];
    },
    getActivities(item) {
      return Object.entries(item)
        .filter((kv) => kv[0].indexOf('/avg') !== -1)
        .map((kv) => ({ name: kv[0], activity: kv[1] }));
    },
  },
};
</script>

<style scoped>
.top-right {
  font-size: x-small;
  position: absolute;
  top: 0;
  right: 0;
  padding: 0 5px;
}

.bottom-right {
  font-size: x-small;
  position: absolute;
  bottom: 0;
  right: 0;
  padding: 1px;
}
</style>
