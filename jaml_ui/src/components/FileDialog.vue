<template>
  <v-dialog v-model="dialog" max-width="600">
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
            <v-col v-if="item != null" cols="12">
              <v-text-field v-model="editedItem.name" label="Name" />
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="editedItem.project" label="Project" />
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="editedItem.description" label="Description" />
            </v-col>
            <v-col cols="6">
              <v-text-field v-model="editedItem.measurementType" label="Measurement Type (e.g. IC50/EC50/AC50/GI50)" />
            </v-col>
            <v-col cols="6">
              <v-text-field v-model="editedItem.target" label="Target" />
            </v-col>
            <v-col cols="6">
              <v-text-field v-model="editedItem.organism" label="Organism" />
            </v-col>
            <v-col v-if="item == null" cols="6">
              <v-select v-model="access" :items="accessTypes" label="Access" />
            </v-col>
            <v-col cols="6">
              <v-select
                v-if="hasCsv"
                v-model="fieldName"
                :disabled="!fieldTypes.length"
                :items="fieldTypes"
                :rules="[(value) => !!value || 'Required']"
                label="Structure field"
              ></v-select>
            </v-col>
            <v-col v-if="item == null" cols="12">
              <v-file-input
                v-model="files"
                :label="`${feature('upload-formats')} file(s)`"
                :multiple="feature('upload-max-files') < 0 || feature('upload-max-files') > 1"
                show-size
              />
            </v-col>
          </v-row>
        </v-container>
        <v-progress-linear v-if="uploading" indeterminate />
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
import MetadataEditor from '@/components/MetadataEditor';

export default {
  mixins: [JamlDialogBase, MetadataEditor],

  props: {
    onButtonActivate: {
      type: Function,
      default: () => {},
    },
  },

  data: () => ({
    fieldName: null,
    fieldTypes: [],
    files: [],
    access: 'public',
    accessTypes: [
      { value: 'public', text: 'Public' },
      { value: 'authenticated', text: 'Authenticated' },
      { value: 'private', text: 'Private' },
    ],
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'files';
    },
    formTitle() {
      return this.item ? 'Edit' : 'Upload';
    },
    hasCsv() {
      return this.files.find((f) => f.name.toLowerCase().endsWith('.csv') || f.name.toLowerCase().endsWith('.xlsx'));
    },
  },

  watch: {
    files() {
      if (this.hasCsv) {
        let formData = new FormData();

        let i = 0;
        this.files.forEach((f) => {
          if (f.name.toLowerCase().endsWith('.csv') || f.name.toLowerCase().endsWith('.xlsx')) {
            formData.append('file' + i, f, f.name);
            i++;
          }
        });

        formData.append('files_number', i);

        this.$axios
          .post('preload', formData)
          .then((response) => {
            this.fieldTypes = response.data;
            this.fieldName = this.fieldTypes.find((f) => f.match(/smiles/i));
          })
          .catch((error) => this.onOkError(error));
      }
    },
  },

  methods: {
    onOk() {
      this.uploading = true;
      this.actionsDisabled = true;
      if (this.item) this.updateMetadata();
      else if (this.files && this.files.length) {
        let formData = new FormData();

        for (let i = 0; i < this.files.length; i++) {
          formData.append('file' + i, this.files[i], this.files[i].name);
        }

        formData.append('files_number', this.files.length);
        formData.append('metadata', JSON.stringify(this.editedItem));
        formData.append('field_name', this.fieldName);
        formData.append('access', this.access);

        this.$axios
          .post(`${this.OBJECTS_TYPE}`, formData)
          .then((response) => {
            this.onOkSuccess();
            this.$emit('uploaded', response.data);
            this.message = 'Created ' + response.data.length + ' SDFs';
          })
          .catch((error) => this.onOkError(error));
      }
    },
  },
};
</script>
