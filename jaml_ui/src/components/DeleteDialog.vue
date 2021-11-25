<template>
  <v-dialog v-model="dialog" max-width="600px">
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
      <v-card-title class="headline">Are you sure you want to delete?</v-card-title>
      <v-card-text v-if="items">
        <div v-for="item in items" :key="item.name">
          {{ item.name }}
        </div>
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
        <v-btn :disabled="actionsDisabled" @click="close">Cancel</v-btn>
        <v-btn :disabled="actionsDisabled" @click="onOk">OK</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import JamlDialogBase from '@/components/JamlDialogBase';

export default {
  mixins: [JamlDialogBase],

  props: {
    items: {
      type: Array,
      default: () => [],
    },
    objectType: {
      type: String,
      required: true,
    },
  },

  methods: {
    onOk() {
      function deleteItem(item, last) {
        // _id.$oid for individual items and _id for groups (_id is a group's name)
        this.$axios
          .delete(`${this.objectType}/${item._id.$oid ? item._id.$oid : encodeURIComponent(item._id)}`)
          .then(() => {
            this.$emit('deleted', item);
            if (last) {
              this.message = 'Deleted';
              this.alertVariant = 'success';
              this.dismissCountDown = 1;
            }
          })
          .catch((error) => {
            this.message = error.response ? error.response.data.detail : 'Unknown error';
            this.alertVariant = 'danger';
            this.dismissCountDown = 2;
          });
      }

      for (let i = this.items.length - 1; i >= 0; i--) {
        deleteItem.call(this, this.items[i], i === 0);
        this.$router.push(`/${this.objectType}`);
      }
    },
  },
};
</script>
