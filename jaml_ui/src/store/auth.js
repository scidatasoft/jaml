const state = {
  user: null,
  session: null,
  privileges: null,
  users: null,
};

const getters = {
  isAuthenticated: (state) => !!state.session,
  isAdmin: (state) => !!state.session && state.session.privileges.includes('admin'),
  canPredict: (state) =>
    !!state.session && (state.session.privileges.includes('admin') || state.session.privileges.includes('predict')),
  canTrain: (state) =>
    !!state.session && (state.session.privileges.includes('admin') || state.session.privileges.includes('train')),
  stateUser: (state) => state.user,
  USER: (state) => state.user,
  stateSession: (state) => state.session,
  PRIVILEGES: (state) => state.privileges,
  USERS: (state) => state.users,
};

const mutations = {
  setUser(state, username) {
    state.user = username;
  },
  setSession(state, session) {
    state.session = session;
  },
  logout(state) {
    state.user = null;
    state.session = null;
    state.privileges = null;
    state.users = null;
  },
  setPrivileges(state, privileges) {
    state.privileges = privileges;
  },
  setUsers(state, users) {
    state.users = users;
  },
};

const actions = {
  async logIn({ commit }, user) {
    try {
      let response = await this._vm.$axios.post('login', user);

      this._vm.$axios.defaults.headers.common['X-Auth'] = response.data.session._id.$oid;
      localStorage.xAuth = response.data.session._id.$oid;

      commit('setUser', response.data.user);
      commit('setSession', response.data.session);

      if (response.data.privileges) {
        let privileges = response.data.privileges.map((p) => ({
          value: p.name,
          text: p.description,
        }));
        commit('setPrivileges', privileges);
      }

      if (response.data.users) {
        let users = response.data.users.map((p) => ({
          value: p._id.$oid,
          text: `${p.full_name || p.username} <${p.email}>`,
        }));
        commit('setUsers', users);
      }

      // commit('resetAllHeaders');

      return null;
    } catch (error) {
      return error.response.data.detail;
    }
  },

  async logOut({ commit }) {
    try {
      await this._vm.$axios.delete('logout');
    } catch (error) {
      //
    }

    delete this._vm.$axios.defaults.headers.common['X-Auth'];
    localStorage.removeItem('xAuth');
    commit('logout');
    // commit('resetAllHeaders');
  },
};

export default {
  state,
  getters,
  actions,
  mutations
};
