import Vue from 'vue';
import Vuex from 'vuex';
import auth from './auth';
import meta from './meta';
import settings from './settings';
import createPersistedState from 'vuex-persistedstate';

Vue.use(Vuex);

export default new Vuex.Store({
  state: {},
  mutations: {},
  actions: {},
  modules: {
    meta,
    auth,
    settings,
  },
  plugins: [createPersistedState()],
});
