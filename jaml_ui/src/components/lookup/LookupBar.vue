<template>
  <div class="row">
    <autocomplete
      :debounce-time="300"
      :get-result-value="getResultValue"
      :search="lookup"
      class="col"
      placeholder="Search by Name, CAS, SMILES, DTXSID, DTXCID, InChI or InChIKey"
      @submit="submit"
    >
      <template #result="{ result, props }">
        <li class="container" v-bind="props">
          <div class="row item">
            <img :src="`${IMAGE_API_URL}${result.cid}`" alt="" class="col-1 item-img" />
            <div class="col item-body">
              {{ getResultValue(result) }}
            </div>
          </div>
        </li>
      </template>
    </autocomplete>

    <b-checkbox v-model="fuzzy" class="col-1 options">Fuzzy</b-checkbox>
  </div>
</template>

<script>
import { IMAGE_API_URL, LOOKUP_URL } from '@/main';
import Axios from 'axios';
import Autocomplete from '@trevoreyre/autocomplete-vue';
import '@trevoreyre/autocomplete-vue/dist/style.css';

export default {
  components: {
    autocomplete: Autocomplete,
  },

  data: () => ({
    fuzzy: false,
  }),

  computed: {
    IMAGE_API_URL() {
      return IMAGE_API_URL;
    },
  },

  methods: {
    getResultValue(result) {
      return result.name || result.cas || result.sid;
    },

    async lookup(query) {
      if (!query || query.trim().length < 3) return [];

      let { data } = await Axios.get(
        LOOKUP_URL + encodeURIComponent(query) + (this.fuzzy ? '&fuzzy=Anywhere' : '&fuzzy=Start')
      );
      return data;
    },

    submit(input) {
      if (!input || (typeof input === 'string' && !input.trim())) return;

      const query = typeof input === 'string' ? input : input.id;
      Axios.get(LOOKUP_URL + encodeURIComponent(query) + '&mol=true').then((response) => {
        if (response.data && response.data[0].mol) this.$emit('searchcompleted', response.data);
      });
    },
  },
};
</script>

<style scoped>
.item-img {
  margin-left: 40px;
}

.options {
  vertical-align: middle;
}

.item-body {
  vertical-align: middle;

  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
