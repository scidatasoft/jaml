<template>
  <v-app>
    <v-app-bar app color="primary">
      <div>
        <v-img v-if="CONFIG.logo" :src="CONFIG.logo" class="shrink mr-2" width="40" />
        <div class="title-logo">{{ CONFIG.title }}</div>
        <div class="title-version">version: {{ ENV.VUE_APP_VERSION }}, build: {{ ENV.VUE_APP_BUILD_DATE }}</div>
      </div>

      <v-spacer />

      <v-btn-toggle class="mr-4" rounded>
        <v-btn class="no-link-under" to="/files">
          <v-icon class="mr-2">mdi-file-document-multiple-outline</v-icon>
          Files
        </v-btn>
        <v-btn class="no-link-under" to="/datasets">
          <v-icon class="mr-2">mdi-table-large</v-icon>
          Datasets
        </v-btn>
        <v-btn class="no-link-under" to="/models">
          <v-icon class="mr-2">mdi-sitemap</v-icon>
          Models
        </v-btn>
        <v-btn class="no-link-under" to="/predict">
          <v-icon class="mr-2">mdi-calculator</v-icon>
          Predict
        </v-btn>
        <v-btn class="no-link-under" to="/resultsets">
          <v-icon class="mr-2">mdi-timetable</v-icon>
          Resultsets
        </v-btn>
      </v-btn-toggle>

      <LoginDialog
        v-if="!isAuthenticated"
        v-model="showLogin"
        button-title="mdi-account-arrow-left-outline"
        max-width="300"
        title="Log In"
      />
      <LoggedInStatus v-else />
    </v-app-bar>

    <v-main>
      <div>
        <router-view />
      </div>
    </v-main>

    <v-footer color="primary" light padless>
      <v-container class="pa-0" fluid>
        <v-card class="white--text text-center" color="primary" flat light padless tile>
          <v-card-text>
            <v-btn
              v-for="link in CONFIG.links"
              :key="link.icon"
              :href="link.url"
              :title="link.title"
              class="mx-4 white--text no-link-under"
              icon
              target="_blank"
            >
              <v-icon size="24px">
                {{ link.icon }}
              </v-icon>
            </v-btn>
          </v-card-text>

          <v-card-text class="white--text">
            <span v-html="CONFIG.copyright" />
          </v-card-text>
        </v-card>
      </v-container>
    </v-footer>
  </v-app>
</template>

<script>
import { mapGetters } from 'vuex';

import LoginDialog from '@/components/auth/LoginDialog';
import LoggedInStatus from '@/components/auth/LoggedInStatus';
import { ENV } from '@/main';

export default {
  components: { LoginDialog, LoggedInStatus },

  data: () => ({
    showLogin: false,
  }),

  beforeCreate() {
    this.$store.dispatch('initMetadata');
  },

  computed: {
    ...mapGetters(['isAuthenticated', 'isAdmin', 'canPredict', 'canTrain', 'feature', 'CONFIG']),
    ENV() {
      return ENV;
    },
  },

  methods: {
    async logout() {
      await this.$store.dispatch('logOut');
      this.$router.go();
    },
  },
};
</script>
<style lang="scss">
.no-link-under {
  &:hover {
    text-decoration: none;
  }
}

.title-logo {
  color: white;
  font-size: larger;
}

.title-version {
  color: darkgrey;
  font-size: smaller;
}

.show-on-hover {
  a.hidden {
    display: none;
  }

  &:hover {
    a {
      display: inline-block;
    }
  }
}

.wrap-300 {
  display: inline-block !important;
  width: 270px;
  overflow-wrap: break-word;
}

.wrap-400 {
  display: inline-block !important;
  width: 400px;
  overflow-wrap: break-word;
}

.wrap-500 {
  display: inline-block !important;
  width: 500px;
  overflow-wrap: break-word;
}

.wrap-600 {
  display: inline-block !important;
  width: 600px;
  overflow-wrap: break-word;
}

.kudos {
  font-size: x-small;
  position: absolute;
  bottom: 0;

  right: 0;
  padding-right: 5px;

  a:link,
  a:visited {
    color: white;
  }

  a:hover,
  a:active {
    color: pink;
  }
}
</style>
