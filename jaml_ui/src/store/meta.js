import Axios from 'axios';
import { API_URL } from '@/main';

const state = {
  config: {},
  methods: {},
  field_types: {},
  descriptors: {},
  stdizers: {},
  features: {},
};

const getters = {
  CONFIG: (state) => {
    return state.config;
  },
  VERSION: (state) => {
    return state.config.version;
  },
  METHODS: (state) => {
    return state.methods;
  },
  CLS_METHODS: (state) => {
    return Object.entries(state.methods)
      .filter((m) => !m[0].endsWith('r'))
      .map((m) => ({ value: m[0], text: m[1] }));
  },
  REG_METHODS: (state) => {
    return Object.entries(state.methods)
      .filter((m) => m[0].endsWith('r'))
      .map((m) => ({ value: m[0], text: m[1] }));
  },
  FEATURES: (state) => {
    return state.features;
  },
  feature: (state) => (feature) => {
    return !!state.features[feature] && (state.features[feature].value === undefined || state.features[feature].value);
  },
};

const mutations = {
  SET_CONFIG: (state, payload) => {
    state.config = payload;
  },
  SET_VERSION: (state, payload) => {
    state.config.version = payload;
  },
  SET_METHODS: (state, payload) => {
    state.methods = payload;
  },
  SET_FIELD_TYPES: (state, payload) => {
    state.field_types = payload;
  },
  SET_DESCRIPTORS: (state, payload) => {
    state.descriptors = payload;
  },
  SET_STDIZERS: (state, payload) => {
    state.stdizers = payload;
  },
  SET_FEATURES: (state, payload) => {
    state.features = payload;
  },
};

const actions = {
  initMetadata: (context) => {
    Axios.get(`${API_URL}metadata`)
      .then((response) => {
        context.commit('SET_CONFIG', response.data.config);
        context.commit('SET_METHODS', response.data.methods);
        context.commit('SET_FIELD_TYPES', response.data.field_types);
        context.commit('SET_DESCRIPTORS', response.data.descriptors);
        context.commit('SET_STDIZERS', response.data.stdizers);
        context.commit('SET_FEATURES', response.data.features);
      })
      .catch((error) => {
        console.log(error.response ? error.response.data.detail : 'Unknown error');
      });
  },
};

export default {
  state,
  getters,
  mutations,
  actions
};
