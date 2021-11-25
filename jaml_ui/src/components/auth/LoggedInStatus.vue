<template>
  <v-menu offset-y transition="scale-transition">
    <template v-slot:activator="{ attrs, on }">
      <v-avatar v-b-tooltip :title="USER.fullName" color="white" v-bind="attrs" v-on="on">
        <v-icon>mdi-account</v-icon>
      </v-avatar>
    </template>
    <v-list>
      <v-list-item v-if="feature('jobs-view') && (canPredict || canTrain)" @click="$router.push('/jobs')">
        <v-list-item-icon>
          <v-icon>mdi-file-multiple-outline</v-icon>
        </v-list-item-icon>
        <v-list-item-title>Jobs</v-list-item-title>
      </v-list-item>

      <v-divider />

      <v-list-item v-if="feature('users-view') && isAdmin" @click="$router.push('/users')">
        <v-list-item-icon>
          <v-icon>mdi-table-account</v-icon>
        </v-list-item-icon>
        <v-list-item-title>Users</v-list-item-title>
      </v-list-item>

      <v-list-item @click="onLogout">
        <v-list-item-icon>
          <v-icon>mdi-account-arrow-right-outline</v-icon>
        </v-list-item-icon>
        <v-list-item-title>Log Out</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script>
import AuthBase from '@/components/auth/AuthBase';
import { mapGetters } from 'vuex';

export default {
  mixins: [AuthBase],

  computed: {
    ...mapGetters(['isAdmin', 'canPredict', 'canTrain', 'feature', 'USER']),
  },

  methods: {
    async onLogout() {
      await this.$store.dispatch('logOut');
      this.$router.go();
    },
  },
};
</script>
