<template>
  <v-dialog v-model="dialog" max-width="500">
    <template v-slot:activator="{ on, attrs }">
      <v-btn
        v-if="buttonTitle"
        :disabled="disabled"
        :style="{ display: visible ? 'flex' : 'none' }"
        :title="title"
        v-bind="attrs"
        v-on="on"
      >
        <template v-if="buttonTitle.startsWith('mdi-')">
          <v-icon>
            {{ buttonTitle }}
          </v-icon>
        </template>
        <template v-else>
          {{ buttonTitle }}
        </template>
      </v-btn>
    </template>
    <v-card>
      <v-card-title> Edit Access Control </v-card-title>
      <v-card-text>
        <v-container>
          <v-row dense>
            <v-col cols="6">
              <v-select v-model="editedItem.access" :items="accessTypes" label="Access" />
            </v-col>
            <v-col cols="12">
              <v-select v-model="editedItem.owner" :items="USERS" :readonly="!isAdmin" label="Owner" />
            </v-col>
            <v-col cols="12">
              <v-select
                v-model="editedItem.read"
                :disabled="editedItem.access !== 'private'"
                :items="USERS"
                :readonly="!isAdmin"
                label="Read"
                multiple
              />
            </v-col>
            <v-col cols="12">
              <v-select
                v-model="editedItem.write"
                :disabled="editedItem.access !== 'private'"
                :items="USERS"
                :readonly="!isAdmin"
                label="Write"
                multiple
              />
            </v-col>
          </v-row>
          <v-row v-if="message" class="red lighten-4" dense>
            <v-col>
              {{ message }}
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn @click="dialog = false"> Cancel </v-btn>
        <v-btn @click="onOk"> Update </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import { mapGetters } from 'vuex';
import DialogBase from '@/components/DialogBase';
import AuthBase from '@/components/auth/AuthBase';

export default {
  mixins: [DialogBase, AuthBase],

  props: {
    item: {
      type: [Object, null],
      default: null,
    },
    type: {
      type: String,
      required: true,
      validator: (value) => ['files', 'datasets', 'models', 'resultsets'].includes(value),
    },
  },

  data: () => ({
    editedItem: {
      access: 'public',
      owner: null,
      read: [],
      write: [],
    },
    accessTypes: [
      { value: 'public', text: 'Public' },
      { value: 'authenticated', text: 'Authenticated' },
      { value: 'private', text: 'Private' },
    ],
  }),

  computed: {
    ...mapGetters(['USERS']),
  },

  watch: {
    dialog(val) {
      this.message = null;
      if (val) {
        if (this.item) this.editedItem = Object.assign({}, this.item.acl);
      }
    },
  },

  methods: {
    onOk() {
      this.$axios
        .put(`${this.type}/${this.item._id.$oid}/acl`, this.editedItem)
        .then(() => {
          this.item.acl = Object.assign({}, this.editedItem);
          this.$emit('update:item', this.item);
          this.dialog = false;
        })
        .catch((error) => (this.message = error.response ? error.response.data.detail : 'Unknown error'));
    },
  },
};
</script>
