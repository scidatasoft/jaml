<script>
import { mapGetters } from 'vuex';

export default {
  props: {
    value: {
      type: Boolean,
      default: false,
    },
    buttonTitle: {
      type: String,
      default: null,
    },
    onButtonActivate: {
      type: Function,
      default: () => {},
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    visible: {
      type: Boolean,
      default: true,
    },
    title: {
      type: String,
      default: null,
    },
    maxWidth: {
      type: [String, Number],
      default: '500',
    },
    small: {
      type: Boolean,
      default: false,
    },
  },

  data: () => ({
    dialog: false,
    message: null,
    uploading: false,
  }),

  computed: {
    ...mapGetters(['feature']),
    formTitle() {
      return 'Create';
    },
  },

  watch: {
    value(val) {
      this.dialog = val;
    },
    dialog(val) {
      this.$emit('input', val);
    },
  },
};
</script>
