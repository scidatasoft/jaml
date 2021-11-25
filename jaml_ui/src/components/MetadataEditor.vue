<script>
export default {
  props: {
    item: {
      type: [Object, null],
      default: null,
    },
    itemType: {
      type: String,
      required: true,
    },
  },

  data: () => ({
    editedItem: {
      name: null,
      project: null,
      description: null,
      measurementType: null,
      target: null,
      organism: null,
    },
    defaultItem: {
      name: null,
      project: null,
      description: null,
      measurementType: null,
      target: null,
      organism: null,
    },
  }),

  watch: {
    dialog(val) {
      if (val) {
        if (this.item) {
          this.editedItem = Object.assign({}, this.item.metadata);
          this.editedItem.name = this.item.name;
        } else {
          this.editedItem = Object.assign({}, this.defaultItem);
        }
      }
    },
  },

  methods: {
    updateMetadata() {
      this.$axios
        .put(`${this.itemType}/${this.item._id.$oid}`, this.editedItem)
        .then((response) => {
          this.onOkSuccess();
          this.item.name = response.data.name;
          Object.assign(this.item.metadata, response.data.metadata);
          this.$emit('update:item', this.item);
        })
        .catch((error) => this.onOkError(error));
    },
  },
};
</script>
