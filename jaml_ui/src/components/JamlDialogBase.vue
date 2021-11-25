<script>
import DialogBase from '@/components/DialogBase';
import AuthBase from '@/components/auth/AuthBase';

export default {
  mixins: [DialogBase, AuthBase],

  data: () => ({
    lastOne: true,
    actionsDisabled: false,
    uploading: false,
    error: false,
    dismissCountDown: 0,
    alertVariant: null,
  }),

  computed: {
    successUrl() {
      return null;
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

  methods: {
    countDownChanged(dismissCountDown) {
      this.dismissCountDown = dismissCountDown;
    },
    close() {
      this.actionsDisabled = false;
      this.dialog = false;
    },
    closeAlert() {
      this.actionsDisabled = false;
      if (!this.error) {
        try {
          if (this.lastOne && this.successUrl) this.$router.push(this.successUrl);
        } catch {
          //
        }
        this.close();
      }
    },
    onOkSuccess() {
      this.uploading = false;
      this.message = 'Success!';
      this.alertVariant = 'success';
      this.dismissCountDown = 1;
      this.error = false;
    },
    onOkError(error) {
      this.uploading = false;
      this.message = error.response ? error.response.data.detail : 'Unknown error';
      this.alertVariant = 'danger';
      this.dismissCountDown = 3;
      this.error = true;
    },
  },
};
</script>
