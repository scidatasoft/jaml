<template>
  <v-card>
    <v-data-table
      :footer-props="{ showFirstLastPage: true, itemsPerPageOptions: [10, 20, 50, -1] }"
      :headers="allHeaders"
      :hide-default-footer="items.length < 50"
      :items="items"
      :items-per-page="-1"
      :search="search"
      show-group-by
    >
      <template #top>
        <v-toolbar class="mb-3">
          <v-col cols="6">
            <v-text-field
              v-model="search"
              append-icon="mdi-magnify"
              hide-details
              label="Search in any field"
              single-line
            />
          </v-col>
          <v-spacer />
          <v-col v-if="isAdmin && USER.username === 'admin'" cols="2">
            <v-select v-model="version" :items="['basic', 'standard', 'enterprise']" />
          </v-col>
        </v-toolbar>
      </template>

      <template #item.feature="{ item }">
        <span v-if="item.link" :title="item.description">
          <a :href="item.link" target="feature">{{ item.feature }}</a>
        </span>
        <span v-else :title="item.description">
          {{ item.feature }}
        </span>
      </template>

      <template v-for="col in ['basic', 'standard', 'enterprise']" v-slot:[`item.${col}`]="{ item }">
        <span v-if="typeof item[col] !== 'object'" :key="col">
          <span v-if="typeof item[col] === 'boolean'">
            <v-icon v-if="item[col]" small color="green">mdi-checkbox-marked-circle-outline</v-icon>
          </span>
          <span v-else-if="item[col] === -1"> Unlimited </span>
          <span v-else-if="item.type === 'number'">
            {{ item[col] | number('0,0') }}
          </span>
          <span v-else-if="item.type === 'size'">
            {{ item[col] | bytes }}
          </span>
          <span v-else>
            {{ item[col] }}
          </span>
        </span>
        <span v-else-if="Array.isArray(item[col])" :key="col">
          <v-chip
            v-for="(v, i) in item[col]"
            :key="`${col}-${i}`"
            :title="v.description"
            outlined
            small
            style="margin-right: 2px; margin-bottom: 2px"
          >
            <span v-if="v.text">
              {{ v.text }}
            </span>
            <span v-else-if="v.name">
              <span v-if="v.link">
                <a :href="v.link" target="feature">{{ v.name }}</a>
              </span>
              <span v-else>
                {{ v.name }}
              </span>
            </span>
            <span v-else>
              {{ v }}
            </span>
          </v-chip>
        </span>
        <span v-else :key="col">
          <v-chip outlined>{{ item[col] }}</v-chip>
        </span>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
import TableBase from '@/components/TableBase';
import { mapGetters } from 'vuex';
import { delay } from '@/main';

export default {
  mixins: [TableBase],

  data: () => ({
    allHeaders: [
      { text: 'Feature', value: 'feature', groupable: false },
      { text: 'Category', value: 'category' },
      { text: 'Basic', value: 'basic', sortable: false, groupable: false },
      { text: 'Standard', value: 'standard', sortable: false, groupable: false },
      { text: 'Enterprise', value: 'enterprise', sortable: false, groupable: false },
      { text: 'Description', value: 'description', sortable: false, groupable: false },
    ],
  }),

  computed: {
    ...mapGetters(['VERSION', 'USER']),
    OBJECTS_TYPE() {
      return 'features';
    },
    AUTO_REFRESH() {
      return null;
    },
    version: {
      get() {
        return this.VERSION;
      },
      set(version) {
        this.$axios
          .put('version', { version: version })
          .then(() => {
            this.$store.commit('SET_VERSION', version);
          })
          .catch(() => {
            console.log('error updating version');
          });

        delay(1000).then(() => {
          alert('Wait for a few seconds while the server restarts');
          this.$router.go();
        });
      },
    },
  },
};
</script>
