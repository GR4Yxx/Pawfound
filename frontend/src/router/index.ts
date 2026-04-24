import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";
import HomeView from "@/views/HomeView.vue";
import ReportView from "@/views/ReportView.vue";
import ReportSuccessView from "@/views/ReportSuccessView.vue";
import BrowseView from "@/views/BrowseView.vue";
import DogDetailView from "@/views/DogDetailView.vue";
import ProfileView from "@/views/ProfileView.vue";
import LoginView from "@/views/LoginView.vue";
import InboxView from "@/views/InboxView.vue";
import { useAuthStore } from "@/stores/auth";

const routes: RouteRecordRaw[] = [
  { path: "/", component: HomeView },
  { path: "/login", component: LoginView },
  { path: "/report", component: ReportView, meta: { requiresAuth: true } },
  { path: "/report/success", component: ReportSuccessView, meta: { requiresAuth: true } },
  { path: "/browse", component: BrowseView },
  { path: "/browse/:id", component: DogDetailView },
  // Legacy redirects so old links / bookmarks still work
  { path: "/matches", redirect: "/browse" },
  { path: "/matches/:id", redirect: to => `/browse/${to.params.id}` },
  { path: "/profile", component: ProfileView, meta: { requiresAuth: true } },
  { path: "/inbox", component: InboxView, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();

  // Wait for the initial auth check to complete
  if (!auth.checked) {
    await auth.fetchMe();
  }

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { path: "/login", query: { tab: "login", redirect: to.fullPath } };
  }

  if (to.path === "/login" && auth.isLoggedIn) {
    return { path: "/" };
  }
});

export default router;
