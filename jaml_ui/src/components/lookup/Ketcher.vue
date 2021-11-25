<template>
  <div>
    <LookupBar v-if="feature('ketcher-chemical-lookup')" @searchcompleted="applyLookupResult"></LookupBar>

    <div>
      <div v-if="disabled" class="disabled"></div>
      <iframe ref="ketcherFrame" class="ketcher-frame" src="ketcher/ketcher.html" @load="loadFrame"></iframe>
    </div>

    <v-card v-if="record && (record.name || record.casrn || record.sid) && feature('ketcher-chemical-info')" tile>
      <v-card-text>
        <v-row>
          <v-col>
            {{ record.name }}
          </v-col>

          <v-col>
            {{ record.casrn }}
          </v-col>

          <v-col>
            <b-link
              v-if="record.sid"
              :href="`https://comptox.epa.gov/dashboard/dsstoxdb/results?search=${record.sid}`"
              target="_blank"
            >
              {{ record.sid }}
            </b-link>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import LookupBar from './LookupBar.vue';
import Axios from 'axios';
import { LOOKUP_URL } from '@/main';
import { mapGetters } from 'vuex';

export default {
  components: { LookupBar },

  props: {
    value: {
      type: String,
      default: null,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },

  data() {
    return {
      ketcherInstance: null,
      record: null,
    };
  },

  computed: {
    ...mapGetters(['feature']),
  },

  methods: {
    loadFrame() {
      this.ketcherInstance = this.$refs.ketcherFrame.contentWindow.ketcher;

      if (this.value) this.setMolecule(this.value);

      this.ketcherInstance.editor.on('change', this.onStructureChanged);
    },
    onStructureChanged() {
      let self = this;
      let smiles = self.ketcherInstance.getSmiles();

      this.$emit('input', smiles);

      Axios.get(LOOKUP_URL + encodeURIComponent(smiles) + '&idType=SMILES').then((response) => {
        if (response && response.data && response.data[0]) this.record = response.data[0];
      });
    },
    applyLookupResult(searchData) {
      if (searchData.length > 0) this.setMolecule(searchData[0].mol);
    },
    getMol() {
      return this.ketcherInstance.getMolfile();
    },
    getSmiles() {
      return this.ketcherInstance.getSmiles();
    },
    setMolecule(mol) {
      this.ketcherInstance.setMolecule(mol);
    },
  },
};
</script>

<style lang="scss" scoped>
.ketcher-frame {
  width: 100%;
  min-height: 450px;
  border: none;
  overflow: hidden;
}

.info {
  margin-top: 0.2em;
  margin-bottom: 1em;
}

.disabled {
  display: block;
  background: black;
  opacity: 0.05;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
</style>
