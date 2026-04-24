<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { storeToRefs } from "pinia";
import { useAuthStore } from "@/stores/auth";
import { useInboxStore } from "@/stores/inbox";

const route = useRoute();
const authStore = useAuthStore();
const { user, isLoggedIn } = storeToRefs(authStore);
const inboxStore = useInboxStore();

const scrolled = ref(false);

function onScroll() {
  scrolled.value = window.scrollY > 12;
}

onMounted(() => {
  window.addEventListener("scroll", onScroll, { passive: true });
  if (isLoggedIn.value) inboxStore.startPolling();
});

onUnmounted(() => {
  window.removeEventListener("scroll", onScroll);
  inboxStore.stopPolling();
});

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + "/");
}
</script>

<template>
  <nav
    class="fixed top-0 w-full z-50 transition-all duration-300"
    :class="scrolled ? 'glass shadow-nav border-b border-outline-variant/20' : 'bg-transparent border-b border-transparent'"
  >
    <div class="flex justify-between items-center px-6 md:px-10 py-3.5 max-w-7xl mx-auto">

      <!-- Logo -->
      <RouterLink to="/" class="flex items-center gap-2.5 group shrink-0">
        <div class="w-8 h-8 editorial-gradient rounded-xl flex items-center justify-center shadow-btn group-hover:shadow-btn-hover transition-shadow">
          <span class="material-symbols-outlined text-on-primary text-base" style="font-variation-settings:'FILL' 1;">pets</span>
        </div>
        <span class="text-lg font-extrabold tracking-tight text-on-surface font-headline">Pawfound</span>
      </RouterLink>

      <!-- ── Logged-in nav ── -->
      <template v-if="isLoggedIn && user">
        <div class="hidden md:flex items-center gap-1">
          <RouterLink to="/browse" class="nav-link" :class="isActive('/browse') ? 'nav-link-active' : ''">Browse</RouterLink>
          <RouterLink to="/report" class="nav-link" :class="isActive('/report') ? 'nav-link-active' : ''">Report a Dog</RouterLink>
          <RouterLink to="/inbox" class="nav-link relative" :class="isActive('/inbox') ? 'nav-link-active' : ''">
            Inbox
            <span
              v-if="inboxStore.unreadCount > 0"
              class="absolute -top-0.5 -right-0.5 min-w-[17px] h-[17px] bg-error text-white text-[0.5rem] font-bold rounded-full leading-none flex items-center justify-center px-1"
            >{{ inboxStore.unreadCount }}</span>
          </RouterLink>
        </div>

        <div class="flex items-center gap-2">
          <RouterLink
            to="/profile"
            class="flex items-center gap-2.5 px-2.5 py-1.5 rounded-full hover:bg-surface-container transition-colors"
          >
            <img
              v-if="user.picture"
              :src="user.picture"
              :alt="user.name"
              class="w-7 h-7 rounded-full object-cover ring-2 ring-primary-container"
            />
            <div v-else class="w-7 h-7 rounded-full editorial-gradient flex items-center justify-center text-on-primary font-bold text-xs font-headline shrink-0">
              {{ user.name?.charAt(0)?.toUpperCase() ?? "?" }}
            </div>
            <span class="hidden md:block font-headline font-semibold text-sm text-on-surface max-w-[100px] truncate">{{ user.name }}</span>
          </RouterLink>
          <button @click="authStore.logout" class="nav-link text-on-surface-variant text-sm">Sign out</button>
        </div>
      </template>

      <!-- ── Guest nav ── -->
      <template v-else>
        <div class="flex items-center gap-1">
          <RouterLink to="/browse" class="nav-link hidden sm:block">Browse Dogs</RouterLink>
          <RouterLink
            to="/login"
            class="nav-link text-on-surface-variant"
          >Sign in</RouterLink>
          <RouterLink
            to="/report"
            class="btn btn-primary btn-sm ml-1"
          >
            <span class="material-symbols-outlined text-sm" style="font-variation-settings:'FILL' 1;">add</span>
            Report a Dog
          </RouterLink>
        </div>
      </template>

    </div>
  </nav>
</template>

<style scoped>
.nav-link {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 600;
  font-size: 0.875rem;
  color: #735722;
  padding: 0.5rem 0.75rem;
  border-radius: 9999px;
  transition: all 0.15s ease;
  position: relative;
  cursor: pointer;
  background: none;
  border: none;
}
.nav-link:hover {
  background: rgba(255,238,216,0.85);
  color: #402b00;
}
.nav-link-active {
  background: rgba(255,238,216,0.9);
  color: #402b00;
  font-weight: 700;
}
.editorial-gradient { background: linear-gradient(135deg, #815100 0%, #f8a010 100%); }
</style>
