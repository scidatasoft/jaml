<script>
import { mapGetters } from 'vuex';

export default {
  computed: {
    ...mapGetters(['stateUser', 'stateSession', 'isAdmin', 'isAuthenticated']),
    canCreate() {
      return this.hasPrivilege('create');
    },
    canTrain() {
      return this.hasPrivilege('train');
    },
    canPredict() {
      return this.hasPrivilege('predict');
    },
  },
  methods: {
    canDelete(item) {
      return this.isAdmin || this.isOwner(item);
    },
    canACL(item) {
      return this.isAdmin || this.isOwner(item);
    },
    canRead(item) {
      let it = item || this.item;
      if (!it) return false;
      if (!it.acl) return true;
      return (
        this.isAdmin ||
        this.isOwner(it) ||
        it.acl.access === 'public' ||
        (this.isAuthenticated && it.acl.read.includes(this.stateUser._id.$oid))
      );
    },
    canWrite(item) {
      let it = item || this.item;
      if (!it || !it.acl) return false;
      return (
        this.isAdmin || this.isOwner(it) || (this.isAuthenticated && it.acl.write.includes(this.stateUser._id.$oid))
      );
    },
    isOwner(item) {
      let it = item || this.item;
      if (!it) return false;
      return this.isAuthenticated && (!it.acl || it.acl.owner === this.stateUser._id.$oid);
    },
    hasPrivilege(priv) {
      return this.isAuthenticated && (this.isAdmin || this.stateSession.privileges.includes(priv));
    },
  },
};
</script>
