import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { User } from "@/types";

const BASE = `${import.meta.env.VITE_API_BASE_URL ?? ""}/api`;

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const checked = ref(false);

  const isLoggedIn = computed(() => !!user.value);

  async function fetchMe(): Promise<void> {
    try {
      const res = await fetch(`${BASE}/auth/me`, { credentials: "include" });
      user.value = res.ok ? ((await res.json()) as User) : null;
    } catch {
      user.value = null;
    } finally {
      checked.value = true;
    }
  }

  async function register(email: string, name: string, password: string): Promise<User> {
    const res = await fetch(`${BASE}/auth/register`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, name, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error((data as { detail?: string }).detail ?? "Registration failed.");
    user.value = data as User;
    return user.value;
  }

  async function login(email: string, password: string): Promise<User> {
    const res = await fetch(`${BASE}/auth/login`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error((data as { detail?: string }).detail ?? "Login failed.");
    user.value = data as User;
    return user.value;
  }

  async function logout(): Promise<void> {
    await fetch(`${BASE}/auth/logout`, { method: "POST", credentials: "include" });
    user.value = null;
    // Import router lazily to avoid circular dependency
    const { default: router } = await import("@/router/index");
    router.push("/");
  }

  return { user, checked, isLoggedIn, fetchMe, register, login, logout };
});
