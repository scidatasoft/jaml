const state = {
  files_headers: null,
  datasets_headers: null,
  models_headers: null,
  resultsets_headers: null,
  users_headers: null,
  jobs_headers: null,
  features_headers: null,
};

const getters = {
  get_files_headers: (state) => state.files_headers,
  get_datasets_headers: (state) => state.datasets_headers,
  get_models_headers: (state) => state.models_headers,
  get_resultsets_headers: (state) => state.resultsets_headers,
  get_users_headers: (state) => state.users_headers,
  get_jobs_headers: (state) => state.jobs_headers,
  get_features_headers: (state) => state.get_features_headers,
};

const mutations = {
  set_files_headers: (state, headers) => (state.files_headers = headers),
  set_datasets_headers: (state, headers) => (state.datasets_headers = headers),
  set_models_headers: (state, headers) => (state.models_headers = headers),
  set_resultsets_headers: (state, headers) => (state.resultsets_headers = headers),
  set_users_headers: (state, headers) => (state.users_headers = headers),
  set_jobs_headers: (state, headers) => (state.jobs_headers = headers),
  set_features_headers: (state, headers) => (state.features_headers = headers),

  resetAllHeaders(state) {
    state.files_headers = null;
    state.datasets_headers = null;
    state.models_headers = null;
    state.resultsets_headers = null;
    state.users_headers = null;
    state.jobs_headers = null;
    state.features_headers = null;
  },
};

const actions = {};

export default {
  state,
  getters,
  actions,
  mutations,
};
