<script>
import { API_URL, dateFromObjectId, roundup } from '@/main';
import AuthBase from '@/components/auth/AuthBase';
import { mapGetters } from 'vuex';

export default {
  mixins: [AuthBase],

  data: () => ({
    dateTimeFormat: new Intl.DateTimeFormat('en-US', { dateStyle: 'short', timeStyle: 'short' }),
    search: null,
    selected: [],
    selectable: false,
    downloading: false,
    items: [],
    item: null,
    visibleDelete: false,
    timer: null,
  }),

  computed: {
    ...mapGetters(['USERS', 'feature']),
    API_URL() {
      return API_URL;
    },
    AUTO_REFRESH() {
      return 30000;
    },
    QUERY() {
      return '';
    },
    availableHeaders() {
      return this.allHeaders.filter(
        (h) =>
          (!('authenticated' in h) || (h.authenticated && this.isAuthenticated)) &&
          (!('admin' in h) || (h.admin && this.isAdmin))
      );
    },
    headers: {
      get() {
        let headers = this.$store.getters[`get_${this.OBJECTS_TYPE}_headers`];
        if (!headers) headers = this.availableHeaders.filter((h) => !('initial' in h) || h.initial);
        return headers;
      },
      set(hs) {
        this.$store.commit(`set_${this.OBJECTS_TYPE}_headers`, hs);
      },
    },
  },

  methods: {
    getUser(user_id) {
      if (!this.USERS) return null;
      const user = this.USERS.find((u) => u.value === user_id);
      return user ? user.text : null;
    },
    roundup(value, digits) {
      return roundup(value, digits);
    },
    deleteItems(items) {
      this.selected = items;
      this.visibleDelete = true;
    },
    removeItems(items) {
      if (!Array.isArray(items)) this.items.splice(this.items.indexOf(items), 1);
      else items.forEach((item) => this.items.splice(this.items.indexOf(item), 1));
    },
    postProcessData(s) {
      if (s._id && s._id.$oid) s.dateCreated = dateFromObjectId(s._id.$oid);
    },
    getData() {
      this.$axios.get(`${this.OBJECTS_TYPE}${this.QUERY}`).then((response) => {
        // to catch a bug: if (typeof response.data === 'string') response.data = JSON.parse(response.data);
        response.data.forEach((s) => this.postProcessData(s));
        this.items = response.data;
      });
    },
  },

  mounted() {
    this.getData();
    if (this.AUTO_REFRESH) this.timer = setInterval(this.getData, this.AUTO_REFRESH);
  },

  beforeDestroy() {
    if (this.timer != null) clearInterval(this.timer);
  },
};
</script>
