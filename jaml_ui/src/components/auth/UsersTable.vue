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
            v-model="search"
            append-icon="mdi-magnify"
            hide-details
            label="Search in any field"
            single-line
          ></v-text-field>

          <v-spacer />

          <v-switch v-model="selectable" class="mt-5 mr-4" label="Select" />

          <v-btn-toggle>
            <HeadersDialog :available-headers="availableHeaders" :headers.sync="headers" />
            <UserDialog
              v-model="visibleUser"
              :disabled="selectable"
              :item.sync="item"
              :on-button-activate="resetItem"
              :visible="!selectable"
              button-title="mdi-account-plus"
              @created="onCreated"
            />
            <DeleteDialog
              v-model="visibleDelete"
              :disabled="!selected.length"
              :items="selected"
              :visible="selectable"
              button-title="mdi-delete"
              object-type="users"
              title="Delete selected users"
              @click="deleteItems(selected)"
              @deleted="removeItems"
            />
          </v-btn-toggle>
        </v-toolbar>
      </template>

      <template #item.username="{ item }">
        {{ item.username }}
      </template>

      <template #item.dateCreated="{ item }">
        {{ dateTimeFormat.format(item.dateCreated) }}
      </template>

      <template #item.privileges="{ item }">
        <v-chip v-for="(privilege, i) in item.privileges" :key="i" class="mr-1" label outlined small>
          {{ privilege }}
        </v-chip>
      </template>

      <template #item.roles="{ item }">
        <v-chip v-for="(role, i) in item.roles" :key="i" label outlined small>
          {{ role }}
        </v-chip>
      </template>

      <template #item.actions="{ item }">
        <div class="justify-end mr-0">
          <v-icon :disabled="selectable" class="mr-1" small title="Edit" @click="editItem(item)">
            mdi-account-edit
          </v-icon>
          <v-icon :disabled="selectable" small title="Delete" @click="deleteItems([item])"> mdi-delete </v-icon>
        </div>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
import DeleteDialog from '@/components/DeleteDialog';
import TableBase from '@/components/TableBase';
import UserDialog from '@/components/auth/UserDialog';
import HeadersDialog from '@/components/HeadersDialog';

export default {
  components: { HeadersDialog, UserDialog, DeleteDialog },

  mixins: [TableBase],

  data: () => ({
    allHeaders: [
      { text: 'Username', value: 'username' },
      { text: 'Full Name', value: 'full_name' },
      { text: 'Email', value: 'email' },
      { text: 'Company', value: 'company' },
      { text: 'Privileges', value: 'privileges', sortable: false },
      { text: 'Active', value: 'active' },
      { text: 'Created', value: 'dateCreated', initial: false },
      { text: 'Actions', value: 'actions', sortable: false, align: 'end', fixed: true },
    ],
    editMode: false,
    visibleUser: false,
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'users';
    },
  },

  methods: {
    resetItem() {
      this.item = null;
    },
    onCreated(user) {
      this.items.push(user);
    },
    editItem(user) {
      this.item = user;
      this.visibleUser = true;
    },
    postProcessData(s) {
      if (!s.name && s.username) s.name = s.username;
    },
  },
};
</script>
