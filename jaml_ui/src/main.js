import Vue from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import vuetify from './plugins/vuetify';
import './plugins/bootstrap-vue';
import Vue2Filters from 'vue2-filters';
import Axios from 'axios';

Vue.use(Vue2Filters);

Vue.config.productionTip = false;

console.log(process.env);

export const ENV = process.env;

export const API_URL = process.env.VUE_APP_API_URL ? process.env.VUE_APP_API_URL : '/api/';
export const SDE_API_URL = 'https://hazard.sciencedataexperts.com/api/';
export const RESOLVER_URL = `${SDE_API_URL}resolver/lookup`;
export const LOOKUP_URL = `${RESOLVER_URL}?query=`;
export const IMAGE_API_URL = `${SDE_API_URL}render/svg?query=`;

Vue.prototype.$axios = Axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

if (localStorage.xAuth) Vue.prototype.$axios.defaults.headers.common['X-Auth'] = localStorage.xAuth;

export const dateFromObjectId = function (objectId) {
  return new Date(parseInt(objectId.substring(0, 8), 16) * 1000);
};

export function download(filename, data) {
  let opt;
  const format = filename.substr(filename.lastIndexOf('.') + 1).toLowerCase();
  if (format === 'xlsx') opt = { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' };
  else if (format === 'csv') opt = { type: 'text/csv' };
  else if (format === 'sdf') opt = { type: 'chemical/x-mdl-sdfile' };
  else if (format === 'zip') opt = { type: 'application/zip' };
  else opt = { type: 'text/plain' };

  let blob = new Blob([data], opt); // pass a useful mime type here
  let url = URL.createObjectURL(blob);

  let element = document.createElement('a');
  element.setAttribute('href', url);
  element.setAttribute('download', filename);

  element.style.display = 'none';
  document.body.appendChild(element);

  element.click();

  document.body.removeChild(element);
}

export function getDatedFilename(prefix, ext) {
  const now = new Date();
  return prefix + '-' + now.toISOString().substr(0, 19) + '.' + ext;
}

export function getActivityColor(value) {
  switch (parseInt(value)) {
    case 0:
      return 'red lighten-3';
    case 1:
      return 'green';
  }
}

export function roundup(value, digits) {
  if (!isNaN(value)) {
    const round = Math.round(Math.pow(10, digits));
    return Math.round((parseFloat(value) + Number.EPSILON) * round) / round;
  }
}

export function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

new Vue({
  router,
  store,
  vuetify,
  render: (h) => h(App),
}).$mount('#app');
