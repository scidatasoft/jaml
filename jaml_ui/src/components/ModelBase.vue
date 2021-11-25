<script>
import { roundup } from '@/main';

export default {
  data: () => ({
    metrics_cls: {
      auc: 'AUC',
      f1score: 'F1',
      ba: 'BA',
      precision: 'Precision',
      acc: 'Accuracy',
      recall: 'Recall',
      specificity: 'Specificity',
      cohens_kappa: "Cohen's Kappa",
      mcc: 'MCC',
    },
    metrics_ext_cls: {
      auc_ext: 'AUC *',
      f1score_ext: 'F1 *',
      ba_ext: 'BA *',
      precision_ext: 'Precision *',
      acc_ext: 'Accuracy *',
      recall_ext: 'Recall *',
      specificity_ext: 'Specificity *',
      cohens_kappa_ext: "Cohen's Kappa *",
      mcc_ext: 'MCC *',
    },
    metrics_reg: {
      r2: 'R2',
      mae: 'MAE',
      rmse: 'RMSE',
      /*explained_variance: 'Explained Variance',
      d2_tweedie_score: 'D2 Tweedie Score',
      mpd: 'Mean Poisson Deviance',
      mgd: 'Mean Gamma Deviance',*/
    },
    metrics_ext_reg: {
      r2_ext: 'Q2 *',
      mae_ext: 'MAE *',
      rmse_ext: 'RMSE *',
      /*explained_variance_ext: 'Explained Variance *',
      d2_tweedie_score_ext: 'D2 Tweedie Score *',
      mpd_ext: 'Mean Poisson Deviance *',
      mgd_ext: 'Mean Gamma Deviance *',*/
    },
  }),

  computed: {
    OBJECTS_TYPE() {
      return 'models';
    },
    classModel() {
      return this.item ? !this.item.method_name.endsWith('r') : null;
    },
    allMetrics() {
      return Object.assign({}, this.metrics_cls, this.metrics_reg, this.metrics_ext_cls, this.metrics_ext_reg);
    },
    metrics() {
      return this.classModel ? this.metrics_cls : this.metrics_reg;
    },
    metrics_ext() {
      return this.classModel ? this.metrics_ext_cls : this.metrics_ext_reg;
    },
    clsHeaders() {
      return Object.keys(this.metrics_cls).map(k => ({ value: k, text: this.metrics_cls[k], align: 'center' }));
    },
    clsExtHeaders() {
      return Object.keys(this.metrics_ext_cls).map(k => ({
        value: k,
        text: this.metrics_ext_cls[k],
        align: 'center',
      }));
    },
    regHeaders() {
      return Object.keys(this.metrics_reg).map(k => ({ value: k, text: this.metrics_reg[k], align: 'center' }));
    },
    regExtHeaders() {
      return Object.keys(this.metrics_ext_reg).map(k => ({
        value: k,
        text: this.metrics_ext_reg[k],
        align: 'center',
      }));
    },
  },

  methods: {
    coloredMetric(h) {
      return (
        h in this.metrics_cls ||
        h in this.metrics_ext_cls ||
        h.startsWith('r2') ||
        h.startsWith('explained_variance') ||
        h.startsWith('d2_tweedie_score')
      );
    },
    roundup(value, digits) {
      return roundup(value, digits);
    },
    getMetricColor(metric, value) {
      if (value == null || isNaN(value) || !this.coloredMetric(metric)) return '';

      if (metric === 'cohens_kappa' || metric === 'cohens_kappa_ext') {
        if (value >= 0.81) return 'green';
        if (value >= 0.61) return 'light-green';
        if (value >= 0.41) return 'lime';
        if (value >= 0.21) return 'yellow';
        if (value > 0.0) return 'amber';
        return 'red';
      }

      if (metric === 'mcc' || metric === 'mcc_ext') {
        if (value >= 0.7) return 'green';
        if (value >= 0.4) return 'light-green';
        if (value >= 0.1) return 'lime';
        if (value >= -0.2) return 'yellow';
        if (value >= -0.5) return 'amber';
        if (value >= -0.8) return 'orange';
        return 'red';
      }

      if (value >= 0.9) return 'green';
      if (value >= 0.8) return 'light-green';
      if (value >= 0.7) return 'lime';
      if (value >= 0.6) return 'yellow';
      if (value >= 0.5) return 'amber';
      if (value >= 0.3) return 'orange';
      return 'red';
    },
  },
};
</script>
