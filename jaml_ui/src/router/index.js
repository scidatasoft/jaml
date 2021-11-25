import Vue from 'vue';
import VueRouter from 'vue-router';
import Home from '@/views/Home.vue';
import About from '@/views/About.vue';
import FileView from '@/components/FileView';
import DatasetView from '@/components/DatasetView';
import ModelView from '@/components/ModelView';
import FilesTable from '@/components/FilesTable';
import DatasetsTable from '@/components/DatasetsTable';
import ModelsTable from '@/components/ModelsTable';
import PredictionsTable from '@/components/PredictionsTable';
import PredictionsView from '@/components/PredictionsView';
import ValidationsView from '@/components/ValidationsView';
import ProtocolView from '@/components/ProtocolView';
import Register from '@/views/Register';
import Login from '@/views/Login';
import store from '../store';
import StructurePredict from '@/components/StructurePredict';
import FeaturesTable from '@/components/FeaturesTable';

Vue.use(VueRouter);

const routes = [
  {
    path: '/',
    component: Home,
  },
  {
    path: '/about',
    component: About,
  },
  {
    path: '/register',
    component: Register,
  },
  {
    path: '/login',
    component: Login,
  },
  {
    path: '/files',
    component: FilesTable,
  },
  {
    path: '/files/:id',
    name: 'file',
    component: FileView,
  },
  {
    path: '/datasets',
    component: DatasetsTable,
  },
  {
    path: '/datasets/:id',
    name: 'dataset',
    component: DatasetView,
  },
  {
    path: '/models',
    component: ModelsTable,
  },
  {
    path: '/models/:name',
    component: ModelsTable,
  },
  {
    path: '/model/:id',
    name: 'model',
    component: ModelView,
  },
  {
    path: '/predict',
    component: StructurePredict,
  },
  {
    path: '/resultsets',
    component: PredictionsTable,
  },
  {
    path: '/resultsets/:id',
    name: 'resultset',
    component: PredictionsView,
  },
  {
    path: '/resultsets/:id/validations',
    name: 'validations',
    component: ValidationsView,
  },
  {
    path: '/protocols/:id',
    name: 'protocol',
    component: ProtocolView,
  },
  {
    path: '/features',
    component: FeaturesTable,
  },
];

const router = new VueRouter({
  routes,
});

router.beforeEach((to, from, next) => {
  if (to.matched.some((record) => record.meta.admin)) {
    if (store.getters.isAuthenticated) {
      next();
      return;
    }
    next('/login');
  } else {
    next();
  }
});

export default router;
