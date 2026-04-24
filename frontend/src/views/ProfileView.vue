<script setup lang="ts">
import { ref, onMounted } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { storeToRefs } from "pinia";
import { useAuthStore } from "@/stores/auth";
import { usePendingMatch } from "@/stores/matchQueue";
import { useInboxStore } from "@/stores/inbox";
import { updateDogStatus } from "@/api";
import NavBar from "@/components/NavBar.vue";
import AppFooter from "@/components/AppFooter.vue";

const router = useRouter();
const authStore = useAuthStore();
const { user } = storeToRefs(authStore);
const { set: setPendingMatch } = usePendingMatch();
const inboxStore = useInboxStore();

const BASE = `${import.meta.env.VITE_API_BASE_URL ?? ""}/api`;

interface DogEntry {
  dog_id: string;
  metadata: {
    dog_name: string;
    breed: string;
    color: string;
    age: string;
    distinctive_markings: string;
    location: string;
    contact_email: string;
    lost_or_found: "lost" | "found";
  };
  image: string | null;
  created_at: string | null;
  status?: "active" | "reunited";
}

const dogs = ref<DogEntry[]>([]);
const loading = ref(true);
const error = ref("");

onMounted(async () => {
  try {
    const res = await fetch(`${BASE}/users/me/dogs`, { credentials: "include" });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    dogs.value = data.dogs;
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to load your dogs.";
  } finally {
    loading.value = false;
  }
});

function formatDate(iso: string | null) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function findMatches(dog: DogEntry) {
  if (!dog.image) return;
  setPendingMatch(dog.image, `${dog.metadata.dog_name}.jpg`, dog.dog_id, dog.metadata.lost_or_found);
  router.push("/browse");
}

async function toggleReunited(dog: DogEntry) {
  const newStatus = dog.status === "reunited" ? "active" : "reunited";
  dog.status = newStatus;
  try {
    await updateDogStatus(dog.dog_id, newStatus);
  } catch {
    dog.status = newStatus === "reunited" ? "active" : "reunited";
  }
}
</script>

<template>
  <div class="bg-surface text-on-surface font-body min-h-screen flex flex-col">
    <NavBar />

    <main class="flex-1 pt-24 pb-20 max-w-5xl mx-auto w-full px-6 md:px-8">

      <!-- Profile header card -->
      <div class="card overflow-hidden mb-8 animate-fade-up">
        <div class="h-24 bg-gradient-brand"></div>
        <div class="px-6 pb-6 -mt-10">
          <div class="flex flex-col md:flex-row items-start md:items-end gap-4">
            <!-- Avatar -->
            <div class="w-20 h-20 rounded-full border-4 border-white shadow-card overflow-hidden shrink-0 bg-primary flex items-center justify-center">
              <img v-if="user?.picture" :src="user.picture" :alt="user?.name" class="w-full h-full object-cover" />
              <span v-else class="text-2xl font-extrabold text-on-primary font-headline">
                {{ user?.name?.charAt(0)?.toUpperCase() ?? "?" }}
              </span>
            </div>
            <div class="flex-1 pb-1">
              <h1 class="font-headline text-2xl font-extrabold text-on-surface">{{ user?.name }}</h1>
              <p class="font-body text-sm text-on-surface-variant">{{ user?.email }}</p>
            </div>
            <button
              @click="authStore.logout"
              class="btn btn-ghost btn-sm text-on-surface-variant"
            >
              <span class="material-symbols-outlined text-sm">logout</span>
              Sign out
            </button>
          </div>
        </div>
      </div>

      <!-- Stats row -->
      <div class="grid grid-cols-3 gap-4 mb-8 animate-fade-up" style="animation-delay:0.05s;">
        <div class="card p-5 text-center">
          <p class="font-headline text-3xl font-extrabold text-on-surface">{{ dogs.length }}</p>
          <p class="text-xs font-label text-on-surface-variant mt-1">Reports</p>
        </div>
        <div class="card p-5 text-center">
          <p class="font-headline text-3xl font-extrabold text-on-surface">{{ dogs.filter(d => d.status === 'reunited').length }}</p>
          <p class="text-xs font-label text-on-surface-variant mt-1">Reunited</p>
        </div>
        <RouterLink to="/inbox" class="card p-5 text-center card-hover group">
          <div class="relative inline-block">
            <p class="font-headline text-3xl font-extrabold text-on-surface">{{ inboxStore.unreadCount }}</p>
            <span v-if="inboxStore.unreadCount > 0" class="absolute -top-1 -right-3 w-4 h-4 bg-error text-white text-[0.5rem] font-bold rounded-full flex items-center justify-center">
              {{ inboxStore.unreadCount }}
            </span>
          </div>
          <p class="text-xs font-label text-on-surface-variant mt-1">Messages</p>
        </RouterLink>
      </div>

      <!-- Inbox shortcut -->
      <RouterLink to="/inbox" class="card card-hover flex items-center justify-between p-5 mb-10 animate-fade-up group" style="animation-delay:0.08s;">
        <div class="flex items-center gap-4">
          <div class="w-11 h-11 editorial-gradient rounded-xl flex items-center justify-center shadow-btn">
            <span class="material-symbols-outlined text-on-primary text-xl" style="font-variation-settings:'FILL' 1;">mark_unread_chat_alt</span>
          </div>
          <div>
            <h3 class="font-headline font-bold text-base text-on-surface">Messages</h3>
            <p class="font-body text-xs text-on-surface-variant">People contacting you about your reports</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span v-if="inboxStore.unreadCount > 0" class="bg-error text-white text-xs font-bold px-2.5 py-0.5 rounded-full">
            {{ inboxStore.unreadCount }} new
          </span>
          <span class="material-symbols-outlined text-on-surface-variant group-hover:text-primary transition-colors">chevron_right</span>
        </div>
      </RouterLink>

      <!-- My reports section -->
      <div class="animate-fade-up" style="animation-delay:0.12s;">
        <div class="flex items-end justify-between mb-6">
          <div>
            <span class="font-label text-xs uppercase tracking-widest text-primary font-semibold mb-1 block">Your Reports</span>
            <h2 class="font-headline text-2xl font-bold text-on-surface">My Reported Dogs</h2>
          </div>
          <RouterLink to="/report" class="btn btn-primary btn-sm">
            <span class="material-symbols-outlined text-sm" style="font-variation-settings:'FILL' 1;">add</span>
            Report a Dog
          </RouterLink>
        </div>

        <!-- Loading skeletons -->
        <div v-if="loading" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <div v-for="i in 3" :key="i" class="card overflow-hidden">
            <div class="aspect-square skeleton"></div>
            <div class="p-4 space-y-2">
              <div class="skeleton h-3 w-1/3 rounded-full"></div>
              <div class="skeleton h-4 w-2/3 rounded-full"></div>
              <div class="skeleton h-3 w-1/2 rounded-full"></div>
            </div>
          </div>
        </div>

        <!-- Error -->
        <div v-else-if="error" class="card p-12 text-center">
          <span class="material-symbols-outlined text-4xl text-outline-variant block mb-3">error_outline</span>
          <p class="text-sm text-error font-medium">{{ error }}</p>
        </div>

        <!-- Empty -->
        <div v-else-if="dogs.length === 0" class="card p-16 text-center">
          <div class="w-16 h-16 editorial-gradient rounded-2xl flex items-center justify-center mx-auto mb-5 shadow-card">
            <span class="material-symbols-outlined text-on-primary text-3xl" style="font-variation-settings:'FILL' 1;">pets</span>
          </div>
          <h3 class="font-headline font-bold text-xl mb-2 text-on-surface">No reports yet</h3>
          <p class="font-body text-sm text-on-surface-variant mb-6 max-w-xs mx-auto">Submit a lost or found report to start matching.</p>
          <RouterLink to="/report" class="btn btn-primary">
            <span class="material-symbols-outlined text-sm" style="font-variation-settings:'FILL' 1;">add</span>
            Report a Dog
          </RouterLink>
        </div>

        <!-- Dog cards -->
        <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <div
            v-for="(dog, i) in dogs"
            :key="dog.dog_id"
            class="card card-hover group overflow-hidden"
            :class="`stagger-${Math.min(i + 1, 6)}`"
          >
            <!-- Photo -->
            <div class="relative aspect-square bg-surface-container overflow-hidden">
              <img
                v-if="dog.image"
                :src="dog.image"
                :alt="dog.metadata.dog_name"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
              <div v-else class="w-full h-full flex items-center justify-center">
                <span class="material-symbols-outlined text-5xl text-outline-variant">pets</span>
              </div>
              <div class="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <span
                class="badge absolute top-2.5 left-2.5 shadow-sm"
                :class="dog.metadata.lost_or_found === 'found' ? 'badge-found' : 'badge-lost'"
              >{{ dog.metadata.lost_or_found }}</span>
              <span v-if="dog.status === 'reunited'" class="badge badge-reunited absolute top-2.5 right-2.5 shadow-sm">
                <span class="material-symbols-outlined text-xs" style="font-variation-settings:'FILL' 1;">favorite</span>
                Reunited
              </span>
            </div>

            <!-- Info -->
            <div class="p-4">
              <h3 class="font-headline font-bold text-base mb-0.5 text-on-surface">{{ dog.metadata.dog_name || "Unnamed" }}</h3>
              <p class="font-label text-xs text-on-surface-variant mb-0.5">{{ dog.metadata.breed }}</p>
              <p class="font-label text-xs text-on-surface-variant flex items-center gap-0.5 mb-1">
                <span class="material-symbols-outlined text-xs text-primary">location_on</span>
                {{ dog.metadata.location || "Unknown" }}
              </p>
              <p v-if="dog.created_at" class="font-label text-[0.65rem] text-on-surface-variant/60 mb-4">
                Reported {{ formatDate(dog.created_at) }}
              </p>

              <!-- Actions -->
              <div class="flex flex-col gap-2 pt-3 border-t border-surface-container">
                <div class="flex gap-2">
                  <RouterLink
                    :to="`/browse/${dog.dog_id}`"
                    class="btn btn-ghost btn-sm flex-1 text-xs"
                  >View</RouterLink>
                  <button
                    @click="findMatches(dog)"
                    :disabled="!dog.image"
                    class="btn btn-primary btn-sm flex-1 text-xs disabled:opacity-40"
                  >
                    <span class="material-symbols-outlined text-xs" style="font-variation-settings:'FILL' 1;">manage_search</span>
                    Find Matches
                  </button>
                </div>
                <button
                  @click="toggleReunited(dog)"
                  class="w-full text-xs font-headline font-semibold py-2 rounded-full border transition-all duration-150"
                  :class="dog.status === 'reunited'
                    ? 'bg-tertiary-container border-tertiary-container text-on-tertiary-container'
                    : 'border-outline-variant/50 text-on-surface-variant hover:bg-surface-container'"
                >
                  <span v-if="dog.status === 'reunited'">
                    <span class="material-symbols-outlined text-xs" style="font-variation-settings:'FILL' 1;">favorite</span>
                    Reunited — Reopen
                  </span>
                  <span v-else>Mark as Reunited</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
</style>
