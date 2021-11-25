<template>
  <v-dialog v-model="dialog" :max-width="maxWidth">
    <template v-slot:activator="{ on, attrs }">
      <template v-if="buttonTitle && buttonTitle.startsWith('mdi-')">
        <v-avatar v-b-tooltip :disabled="disabled" :title="title" color="white" v-bind="attrs" v-on="on">
          <v-icon>{{ buttonTitle }}</v-icon>
        </v-avatar>
      </template>
      <v-btn
        v-else
        v-b-tooltip
        :disabled="disabled"
        :style="{ display: visible ? 'flex' : 'none' }"
        :title="title"
        class="ml-4"
        v-bind="attrs"
        v-on="on"
      >
        {{ buttonTitle }}
      </v-btn>
    </template>

    <v-card>
      <v-card-title> Login</v-card-title>

      <v-card-text>
        <v-container>
          <v-row dense>
            <v-col>
              <v-text-field v-model="username" label="Username" />
              <v-text-field
                v-model="password"
                :append-icon="show ? 'mdi-eye' : 'mdi-eye-off'"
                :type="show ? 'text' : 'password'"
                label="Password"
                @click:append="show = !show"
              />
              <div v-if="message">{{ message }}</div>
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn @click="onLogin"> Log In</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import md5 from 'md5';
import DialogBase from '@/components/DialogBase';

export default {
  mixins: [DialogBase],

  data: () => ({
    username: null,
    password: null,
    show: false,
  }),

  methods: {
    async onLogin() {
      let res = await this.$store.dispatch('logIn', { username: this.username, password_hash: md5(this.password) });
      if (res) this.message = res;
      else {
        this.dialog = false;
        this.$router.go();
      }
    },
  },
};
</script>
