<script>
import { API_URL, download, roundup } from '@/main';
import AuthBase from '@/components/auth/AuthBase';
import { mapGetters } from 'vuex';

export default {
  mixins: [AuthBase],

  data: () => ({
    item: {
      name: null,
      metadata: {},
      fields: [],
      fields_mapping: [],
      records: [],
      method_name: '',
      descriptors: [],
    },
    search: null,
    downloading: false,
    view: 0,
  }),

  computed: {
    ...mapGetters(['feature']),
    API_URL() {
      return API_URL;
    },
    AUTO_REFRESH() {
      return null;
    },
    OBJECTS_TYPE() {
      return null;
    },
    headersFields() {
      return this.item
        ? [{ text: 'Structure', value: 'image', sortable: false }].concat(
            this.item.fields.map((f) => ({ text: f, value: f }))
          )
        : [];
    },
    headersNames() {
      return this.item
        ? [{ text: 'Structure', value: 'image', sortable: false }].concat(
            this.item.fields_mapping.filter((f) => f.type).map((f) => ({ text: f.name, value: f.name }))
          )
        : [];
    },
    headersTypes: function () {
      return this.item
        ? [{ text: 'Structure', value: 'image', sortable: false }].concat(
            this.item.fields_mapping.filter((f) => f.type).map((f) => ({ text: f.type, value: f.type }))
          )
        : [];
    },
    items() {
      return this.item
        ? this.item.records.map((r) => {
            if (r.molecule) r.fields.id = r.molecule.$oid;
            r.fields.ord = r.ord;
            return r.fields;
          })
        : [];
    },
  },

  methods: {
    roundup(value, digits) {
      return roundup(value, digits);
    },
    downloadItem(filename, format) {
      this.downloading = true;
      const fmt = format ? `?format=${format}` : '';
      this.$axios
        .get(`${this.OBJECTS_TYPE}/${this.item._id.$oid}/download${fmt}`, { responseType: 'blob' })
        .then((response) => {
          this.downloading = false;
          download(filename && typeof filename === 'string' ? filename : this.item.name, response.data);
        })
        .catch(() => (this.downloading = false));
    },
    postProcessData() {
      //
    },
    getData() {
      this.$axios.get(`${this.OBJECTS_TYPE}/${this.$route.params.id}`).then((response) => {
        this.postProcessData(response.data);
        this.item = response.data;
      });
    },
  },

  watch: {
    view(val) {
      if (val === 0 || val === 1) this.$router.push(`${this.$route.path}?view=${val}`);
    },
  },

  mounted() {
    if (!this.canRead()) this.$router.push('/');
    this.getData();
    if (this.AUTO_REFRESH) this.timer = setInterval(this.getData, this.AUTO_REFRESH);
  },

  beforeDestroy() {
    if (this.timer != null) clearInterval(this.timer);
  },
};
</script>
