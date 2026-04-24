<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter, useRoute, RouterLink } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

onMounted(() => {
  if (route.query.tab === "register") activeTab.value = "register";
});

function redirectAfterAuth() {
  const dest = route.query.redirect as string | undefined;
  router.push(dest && dest.startsWith("/") ? dest : "/");
}

const activeTab = ref<"login" | "register">("login");

const loginEmail = ref("");
const loginPassword = ref("");
const loginError = ref("");
const loginLoading = ref(false);

const regEmail = ref("");
const regName = ref("");
const regPassword = ref("");
const regConfirm = ref("");
const regError = ref("");
const regLoading = ref(false);

async function submitLogin() {
  loginError.value = "";
  if (!loginEmail.value || !loginPassword.value) {
    loginError.value = "Please fill in all fields.";
    return;
  }
  loginLoading.value = true;
  try {
    await authStore.login(loginEmail.value, loginPassword.value);
    redirectAfterAuth();
  } catch (e: unknown) {
    loginError.value = e instanceof Error ? e.message : "Login failed.";
  } finally {
    loginLoading.value = false;
  }
}

async function submitRegister() {
  regError.value = "";
  if (!regEmail.value || !regName.value || !regPassword.value) {
    regError.value = "Please fill in all fields.";
    return;
  }
  if (regPassword.value.length < 8) {
    regError.value = "Password must be at least 8 characters.";
    return;
  }
  if (regPassword.value !== regConfirm.value) {
    regError.value = "Passwords do not match.";
    return;
  }
  regLoading.value = true;
  try {
    await authStore.register(regEmail.value, regName.value, regPassword.value);
    redirectAfterAuth();
  } catch (e: unknown) {
    regError.value = e instanceof Error ? e.message : "Registration failed.";
  } finally {
    regLoading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen bg-surface font-body flex flex-col">

    <!-- Minimal header -->
    <header class="px-6 md:px-10 py-4 flex items-center justify-between max-w-7xl mx-auto w-full">
      <RouterLink to="/" class="flex items-center gap-2.5 group">
        <div class="w-8 h-8 editorial-gradient rounded-xl flex items-center justify-center shadow-btn">
          <span class="material-symbols-outlined text-on-primary text-base" style="font-variation-settings:'FILL' 1;">pets</span>
        </div>
        <span class="text-lg font-extrabold tracking-tight text-on-surface font-headline">Pawfound</span>
      </RouterLink>
      <RouterLink to="/" class="text-sm font-headline font-semibold text-on-surface-variant hover:text-primary transition-colors flex items-center gap-1.5">
        <span class="material-symbols-outlined text-sm">arrow_back</span>
        Back to home
      </RouterLink>
    </header>

    <!-- Auth card -->
    <main class="flex-1 flex items-center justify-center px-4 py-12">
      <div class="w-full max-w-md animate-fade-up">

        <!-- Brand accent -->
        <div class="editorial-gradient h-1.5 rounded-t-2xl"></div>

        <div class="bg-white rounded-b-2xl shadow-card-raised px-8 pt-8 pb-10">

          <!-- Heading -->
          <div class="text-center mb-8">
            <h1 class="font-headline text-2xl font-extrabold text-on-surface mb-1.5">
              {{ activeTab === 'login' ? 'Welcome back' : 'Create your account' }}
            </h1>
            <p class="font-body text-sm text-on-surface-variant leading-relaxed">
              {{ activeTab === 'login'
                ? 'Sign in to report dogs and track your submissions.'
                : 'Join the community helping reunite dogs with their families.' }}
            </p>
          </div>

          <!-- Tab switcher -->
          <div class="flex bg-surface-container rounded-full p-1 mb-8">
            <button
              @click="activeTab = 'login'"
              class="flex-1 py-2.5 rounded-full text-sm font-headline font-semibold transition-all duration-200"
              :class="activeTab === 'login'
                ? 'bg-white shadow text-on-surface'
                : 'text-on-surface-variant hover:text-on-surface'"
            >Sign in</button>
            <button
              @click="activeTab = 'register'"
              class="flex-1 py-2.5 rounded-full text-sm font-headline font-semibold transition-all duration-200"
              :class="activeTab === 'register'
                ? 'bg-white shadow text-on-surface'
                : 'text-on-surface-variant hover:text-on-surface'"
            >Create account</button>
          </div>

          <!-- LOGIN -->
          <form v-if="activeTab === 'login'" @submit.prevent="submitLogin" class="space-y-5">
            <div class="space-y-1.5">
              <label class="font-label text-xs font-semibold text-on-surface-variant uppercase tracking-widest ml-1">Email</label>
              <input
                v-model="loginEmail"
                type="email"
                autocomplete="email"
                placeholder="you@example.com"
                class="w-full bg-surface-container-high border-none rounded-xl px-4 py-3.5 text-sm focus:bg-surface-container-highest transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20 placeholder:text-on-surface-variant/40"
              />
            </div>
            <div class="space-y-1.5">
              <label class="font-label text-xs font-semibold text-on-surface-variant uppercase tracking-widest ml-1">Password</label>
              <input
                v-model="loginPassword"
                type="password"
                autocomplete="current-password"
                placeholder="••••••••"
                class="w-full bg-surface-container-high border-none rounded-xl px-4 py-3.5 text-sm focus:bg-surface-container-highest transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20 placeholder:text-on-surface-variant/40"
              />
            </div>

            <p v-if="loginError" class="text-xs text-error font-medium flex items-center gap-1.5">
              <span class="material-symbols-outlined text-sm">error_outline</span>
              {{ loginError }}
            </p>

            <button
              type="submit"
              :disabled="loginLoading"
              class="btn btn-primary w-full"
            >
              <span v-if="loginLoading" class="material-symbols-outlined text-lg animate-spin-slow">autorenew</span>
              {{ loginLoading ? "Signing in…" : "Sign in" }}
            </button>

            <p class="text-center text-xs text-on-surface-variant">
              Don't have an account?
              <button type="button" @click="activeTab = 'register'" class="text-primary font-semibold hover:underline ml-1">Create one</button>
            </p>
          </form>

          <!-- REGISTER -->
          <form v-else @submit.prevent="submitRegister" class="space-y-5">
            <div class="space-y-1.5">
              <label class="font-label text-xs font-semibold text-on-surface-variant uppercase tracking-widest ml-1">Full Name</label>
              <input
                v-model="regName"
                type="text"
                autocomplete="name"
                placeholder="Jane Doe"
                class="w-full bg-surface-container-high border-none rounded-xl px-4 py-3.5 text-sm focus:bg-surface-container-highest transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20 placeholder:text-on-surface-variant/40"
              />
            </div>
            <div class="space-y-1.5">
              <label class="font-label text-xs font-semibold text-on-surface-variant uppercase tracking-widest ml-1">Email</label>
              <input
                v-model="regEmail"
                type="email"
                autocomplete="email"
                placeholder="you@example.com"
                class="w-full bg-surface-container-high border-none rounded-xl px-4 py-3.5 text-sm focus:bg-surface-container-highest transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20 placeholder:text-on-surface-variant/40"
              />
            </div>
            <div class="space-y-1.5">
              <label class="font-label text-xs font-semibold text-on-surface-variant uppercase tracking-widest ml-1">Password</label>
              <input
                v-model="regPassword"
                type="password"
                autocomplete="new-password"
                placeholder="Min. 8 characters"
                class="w-full bg-surface-container-high border-none rounded-xl px-4 py-3.5 text-sm focus:bg-surface-container-highest transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20 placeholder:text-on-surface-variant/40"
              />
            </div>
            <div class="space-y-1.5">
              <label class="font-label text-xs font-semibold text-on-surface-variant uppercase tracking-widest ml-1">Confirm Password</label>
              <input
                v-model="regConfirm"
                type="password"
                autocomplete="new-password"
                placeholder="••••••••"
                class="w-full bg-surface-container-high border-none rounded-xl px-4 py-3.5 text-sm focus:bg-surface-container-highest transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20 placeholder:text-on-surface-variant/40"
              />
            </div>

            <p v-if="regError" class="text-xs text-error font-medium flex items-center gap-1.5">
              <span class="material-symbols-outlined text-sm">error_outline</span>
              {{ regError }}
            </p>

            <button
              type="submit"
              :disabled="regLoading"
              class="btn btn-primary w-full"
            >
              <span v-if="regLoading" class="material-symbols-outlined text-lg animate-spin-slow">autorenew</span>
              {{ regLoading ? "Creating account…" : "Create account" }}
            </button>

            <p class="text-center text-xs text-on-surface-variant">
              Already have an account?
              <button type="button" @click="activeTab = 'login'" class="text-primary font-semibold hover:underline ml-1">Sign in</button>
            </p>
          </form>

        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
.editorial-gradient { background: linear-gradient(135deg, #815100 0%, #f8a010 100%); }
</style>
