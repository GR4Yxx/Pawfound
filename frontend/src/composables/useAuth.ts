import { storeToRefs } from "pinia";
import { useAuthStore } from "@/stores/auth";

/**
 * Thin composable wrapper around the auth Pinia store.
 * Returns reactive refs so components stay in sync.
 *
 * Usage:
 *   const { user, isLoggedIn, login, register, logout } = useAuth()
 */
export function useAuth() {
  const store = useAuthStore();
  const { user, isLoggedIn, checked } = storeToRefs(store);
  return {
    user,
    isLoggedIn,
    checked,
    login: store.login,
    register: store.register,
    logout: store.logout,
    fetchMe: store.fetchMe,
  };
}
