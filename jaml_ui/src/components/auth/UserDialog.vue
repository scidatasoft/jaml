<template>
  <v-dialog v-model="dialog" max-width="500">
    <template v-slot:activator="{ on, attrs }">
      <v-btn
        v-if="buttonTitle"
        :disabled="disabled"
        :style="{ display: visible ? 'flex' : 'none' }"
        :title="title"
        v-bind="attrs"
        @click="onButtonActivate"
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
      <v-card-title>
        {{ formTitle }}
      </v-card-title>

      <v-card-text>
        <v-container>
          <v-row dense>
            <v-col>
              <v-text-field v-model="editedItem.username" label="Username" />
              <v-text-field
                v-model="editedItem.password"
                :append-icon="show ? 'mdi-eye' : 'mdi-eye-off'"
                :rules="passwordRules"
                :type="show ? 'text' : 'password'"
                counter
                hint="At least 8 characters"
                label="Password"
                @click:append="show = !show"
              />
              <v-text-field
                v-model="editedItem.password2"
                :append-icon="show ? 'mdi-eye' : 'mdi-eye-off'"
                :rules="password2Rules"
                :type="show ? 'text' : 'password'"
                counter
                hint="At least 8 characters"
                label="Repeat password"
                @click:append="show = !show"
              />
              <v-text-field v-model="editedItem.full_name" label="Full Name" />
              <v-text-field v-model="editedItem.email" :rules="[rules.required, rules.min]" label="Email" />
              <v-text-field v-model="editedItem.company" label="Company" />
              <v-checkbox v-model="editedItem.active" label="Active" />
              <v-select v-model="editedItem.privileges" :items="PRIVILEGES" label="Privileges" multiple />
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>

      <v-card-actions>
        <b-alert
          :show="dismissCountDown"
          :variant="alertVariant"
          @dismissed="close"
          @dismiss-count-down="countDownChanged"
        >
          {{ message }}
        </b-alert>
        <v-spacer></v-spacer>
        <v-btn :disabled="actionsDisabled" @click="close"> Cancel </v-btn>
        <v-btn :disabled="actionsDisabled" @click="onOk"> Save </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import JamlDialogBase from '@/components/JamlDialogBase';
import md5 from 'md5';
import { mapGetters } from 'vuex';

export default {
  mixins: [JamlDialogBase],

  props: {
    item: {
      type: [Object, null],
      default: null,
    },
    onButtonActivate: {
      type: Function,
      default: () => {},
    },
  },

  data: () => ({
    editedItem: {
      username: null,
      password: null,
      password2: null,
      email: null,
      company: null,
      active: true,
      privileges: [],
    },
    defaultItem: {
      username: null,
      password: null,
      password2: null,
      email: null,
      company: null,
      active: true,
      privileges: [],
    },
    show: false,
    rules: {
      required: (value) => !!value || 'Required',
      min: (v) => v != null && (v.length >= 6 || 'Min 6 characters'),
      passwordMatch() {
        return true;
        // let self = this;
        // return self.password === self.password2 ? true : `Passwords don't match`;
      },
    },
  }),

  computed: {
    ...mapGetters(['PRIVILEGES']),

    OBJECTS_TYPE() {
      return 'users';
    },
    formTitle() {
      return this.item ? 'Edit' : 'Create';
    },
    preparedUser() {
      return {
        username: this.editedItem.username,
        password_hash: this.editedItem.password ? md5(this.editedItem.password) : null,
        full_name: this.editedItem.full_name,
        email: this.editedItem.email,
        company: this.editedItem.company,
        active: this.editedItem.active,
        privileges: this.editedItem.privileges,
      };
    },
    passwordRules() {
      return this.item != null ? [] : [this.rules.required, this.rules.min];
    },
    password2Rules() {
      return this.item ? [this.rules.passwordMatch] : [this.rules.required, this.rules.min, this.rules.passwordMatch];
    },
  },

  watch: {
    dialog(val) {
      if (val) {
        if (this.item) this.editedItem = Object.assign({}, this.item);
        else this.editedItem = Object.assign({}, this.defaultItem);
      }
    },
  },

  methods: {
    onOk() {
      this.uploading = true;
      this.actionsDisabled = true;
      if (this.item) {
        this.$axios
          .put(`${this.OBJECTS_TYPE}/${this.item._id.$oid}`, this.preparedUser)
          .then((response) => {
            this.onOkSuccess();
            this.$emit('update:item', Object.assign({}, response.data));
          })
          .catch((error) => this.onOkError(error));
      } else {
        this.$axios
          .post(`${this.OBJECTS_TYPE}`, this.preparedUser)
          .then((response) => {
            this.onOkSuccess();
            this.$emit('created', response.data);
            this.message = 'Created new user';
          })
          .catch((error) => this.onOkError(error));
      }
    },
  },
};
</script>
