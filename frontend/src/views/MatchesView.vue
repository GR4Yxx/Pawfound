<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { matchDog, listDogs } from "@/api";
import type { MatchResult, DogDetailResponse } from "@/types";
import { usePendingMatch } from "@/stores/matchQueue";
import MapPicker from "@/components/MapPicker.vue";
import NavBar from "@/components/NavBar.vue";
import AppFooter from "@/components/AppFooter.vue";

const router = useRouter();
const { take: takePendingMatch } = usePendingMatch();

// Upload state
const uploadedFile = ref<File | null>(null);
const uploadPreview = ref<string | null>(null);
const scanning = ref(false);
const error = ref("");

// Context from ProfileView "Find Matches" flow
const pendingExcludeId = ref<string | null>(null);
const pendingLostOrFound = ref<"lost" | "found" | null>(null);

// Results state
const matches = ref<MatchResult[]>([]);
const hasScanned = ref(false);

// Browse feed (shown before scan)
const allDogs = ref<DogDetailResponse[]>([]);
const feedLoading = ref(true);
const feedFilter = ref<"all" | "lost" | "found">("all");

// Location filter
const showLocationFilter = ref(false);
const filterCoords = ref<{ lat: number; lng: number } | null>(null);
const filterRadiusKm = ref(25);

const feedFiltered = () =>
  feedFilter.value === "all"
    ? allDogs.value
    : allDogs.value.filter((d) => d.metadata.lost_or_found === feedFilter.value);

onMounted(async () => {
  // If ProfileView queued a dog image for matching, pre-load it and auto-scan
  const pending = takePendingMatch();
  if (pending) {
    uploadPreview.value = pending.dataUrl;
    pendingExcludeId.value = pending.dogId;
    // Search for the opposite type: lost dog → find "found" reports, and vice versa
    pendingLostOrFound.value = pending.lostOrFound === "lost" ? "found" : "lost";
    // Convert base64 data URL → File so scanForMatches() can send it
    const res = await fetch(pending.dataUrl);
    const blob = await res.blob();
    uploadedFile.value = new File([blob], pending.filename, { type: blob.type });
    await scanForMatches();
  }

  try {
    const geo = filterCoords.value
      ? { lat: filterCoords.value.lat, lng: filterCoords.value.lng, radiusKm: filterRadiusKm.value }
      : undefined;
    const res = await listDogs(30, 0, geo);
    allDogs.value = res.dogs;
  } catch {
    // silent
  } finally {
    feedLoading.value = false;
  }
});

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  if (input.files?.[0]) {
    uploadedFile.value = input.files[0];
    uploadPreview.value = URL.createObjectURL(input.files[0]);
  }
}

function onDrop(e: DragEvent) {
  e.preventDefault();
  const file = e.dataTransfer?.files[0];
  if (file) {
    uploadedFile.value = file;
    uploadPreview.value = URL.createObjectURL(file);
  }
}

function clearUpload() {
  uploadedFile.value = null;
  uploadPreview.value = null;
  hasScanned.value = false;
  matches.value = [];
  error.value = "";
  pendingExcludeId.value = null;
  pendingLostOrFound.value = null;
}

async function scanForMatches() {
  if (!uploadedFile.value) {
    error.value = "Please upload a photo first.";
    return;
  }
  scanning.value = true;
  error.value = "";
  try {
    const form = new FormData();
    form.append("image", uploadedFile.value);
    if (pendingExcludeId.value) form.append("exclude_id", pendingExcludeId.value);
    if (pendingLostOrFound.value) form.append("lost_or_found", pendingLostOrFound.value);
    if (filterCoords.value) {
      form.append("filter_lat", String(filterCoords.value.lat));
      form.append("filter_lng", String(filterCoords.value.lng));
      form.append("filter_radius_km", String(filterRadiusKm.value));
    }
    const res = await matchDog(form);
    matches.value = res.matches;
    hasScanned.value = true;
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Scan failed. Please try again.";
  } finally {
    scanning.value = false;
  }
}

async function applyLocationFilter() {
  feedLoading.value = true;
  try {
    const geo = filterCoords.value
      ? { lat: filterCoords.value.lat, lng: filterCoords.value.lng, radiusKm: filterRadiusKm.value }
      : undefined;
    const res = await listDogs(30, 0, geo);
    allDogs.value = res.dogs;
  } catch {
    // silent
  } finally {
    feedLoading.value = false;
  }
}

function viewMatchDetail(dogId: string, similarity?: number) {
  router.push({
    path: `/matches/${dogId}`,
    state: {
      similarity,
      uploadPreview: uploadPreview.value,
    },
  });
}
</script>

<template>
  <div class="bg-background text-on-background font-body">
    <NavBar />

    <main class="pt-24 pb-20 px-8 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-10">

      <!-- ── Sidebar ── -->
      <aside class="lg:col-span-4 space-y-6">
        <div class="bg-surface-container-low p-7 rounded-xl">
          <h1 class="font-headline text-2xl font-bold text-on-surface mb-1">Find a Match</h1>
          <p class="text-on-surface-variant text-sm mb-6">Upload a photo — our AI compares it against every reported dog.</p>

          <!-- Upload zone -->
          <div @dragover.prevent @drop="onDrop">
            <label class="block aspect-square w-full bg-surface-container-highest border-2 border-dashed border-outline-variant/30 rounded-xl cursor-pointer relative overflow-hidden transition-all hover:bg-surface-container-high">
              <img v-if="uploadPreview" :src="uploadPreview" class="absolute inset-0 w-full h-full object-cover" alt="Upload preview" />
              <div v-else class="w-full h-full flex flex-col items-center justify-center gap-3 p-6 text-center">
                <span class="material-symbols-outlined text-4xl text-primary" style="font-variation-settings: 'FILL' 1;">add_a_photo</span>
                <p class="font-headline font-semibold text-on-surface text-sm">Drop photo here or click to browse</p>
                <p class="text-xs text-on-surface-variant font-label uppercase tracking-widest">JPG · PNG · max 5MB</p>
              </div>
              <input type="file" accept="image/*" class="hidden" @change="onFileChange" />
            </label>
          </div>

          <div class="mt-5 space-y-3">
            <button
              @click="scanForMatches"
              :disabled="scanning || !uploadedFile"
              class="w-full editorial-gradient text-on-primary font-headline font-bold py-3.5 rounded-full shadow-md transition-transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ scanning ? "Scanning…" : "Scan for Matches" }}
            </button>
            <button
              v-if="uploadPreview"
              @click="clearUpload"
              class="w-full text-sm font-headline font-semibold text-on-surface-variant py-2 rounded-full hover:bg-surface-container transition-colors"
            >
              Clear &amp; browse all dogs
            </button>
            <p v-if="error" class="text-xs text-error font-medium">{{ error }}</p>
          </div>
        </div>

        <!-- Feed filters (only shown in browse mode) -->
        <div v-if="!hasScanned" class="bg-surface-container-low p-5 rounded-xl">
          <p class="font-label text-xs uppercase tracking-widest text-on-surface-variant mb-3">Filter Reports</p>
          <div class="flex gap-2">
            <button
              v-for="f in ['all', 'lost', 'found'] as const"
              :key="f"
              @click="feedFilter = f"
              class="flex-1 py-2 rounded-full text-xs font-headline font-bold capitalize transition-colors"
              :class="feedFilter === f
                ? 'editorial-gradient text-on-primary shadow-sm'
                : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'"
            >
              {{ f }}
            </button>
          </div>
        </div>

        <!-- Location filter -->
        <div class="bg-surface-container-low p-5 rounded-xl">
          <button
            @click="showLocationFilter = !showLocationFilter"
            class="w-full flex items-center justify-between font-label text-xs uppercase tracking-widest text-on-surface-variant"
          >
            <span>Filter by Location</span>
            <span class="material-symbols-outlined text-base transition-transform" :class="showLocationFilter ? 'rotate-180' : ''">expand_more</span>
          </button>

          <div v-if="showLocationFilter" class="mt-4 space-y-4">
            <div>
              <label class="font-label text-xs text-on-surface-variant mb-1 block">Radius: {{ filterRadiusKm }} km</label>
              <input
                type="range"
                v-model.number="filterRadiusKm"
                min="1" max="200" step="1"
                class="w-full accent-primary"
              />
            </div>
            <MapPicker v-model="filterCoords" />
            <button
              @click="applyLocationFilter"
              class="w-full editorial-gradient text-on-primary text-xs font-headline font-bold py-2.5 rounded-full"
            >
              Apply Filter
            </button>
            <button
              v-if="filterCoords"
              @click="filterCoords = null; applyLocationFilter()"
              class="w-full text-xs font-headline font-semibold text-on-surface-variant py-2 rounded-full hover:bg-surface-container transition-colors"
            >
              Clear Location Filter
            </button>
          </div>
        </div>
      </aside>

      <!-- ── Main panel ── -->
      <section class="lg:col-span-8">

        <!-- ── SCAN RESULTS ── -->
        <template v-if="hasScanned">
          <div class="flex items-end justify-between mb-6">
            <div>
              <h2 class="font-headline text-3xl font-extrabold tracking-tight">Scan Results</h2>
              <p class="text-on-surface-variant text-sm mt-1">
                {{ matches.length > 0
                  ? `${matches.length} visual match${matches.length !== 1 ? 'es' : ''} found — sorted by similarity.`
                  : 'No matches above the similarity threshold.' }}
              </p>
            </div>
          </div>

          <div v-if="matches.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div
              v-for="match in matches"
              :key="match.dog_id"
              class="bg-surface-container-lowest rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-shadow cursor-pointer group"
              @click="viewMatchDetail(match.dog_id, match.similarity)"
            >
              <div class="relative aspect-square overflow-hidden bg-surface-container">
                <img v-if="match.image" :src="match.image" :alt="match.metadata.dog_name" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <span class="material-symbols-outlined text-5xl text-outline-variant">pets</span>
                </div>
                <!-- similarity badge -->
                <div class="absolute top-3 left-3">
                  <span
                    class="px-3 py-1 rounded-sm text-[0.7rem] font-label uppercase tracking-widest font-bold"
                    :class="match.similarity >= 0.8 ? 'bg-tertiary text-on-tertiary' : 'bg-secondary text-on-secondary'"
                  >
                    {{ Math.round(match.similarity * 100) }}% match
                  </span>
                </div>
                <!-- lost/found badge -->
                <div class="absolute top-3 right-3">
                  <span
                    class="text-[0.65rem] font-bold px-2 py-0.5 rounded-sm uppercase tracking-tight"
                    :class="match.metadata.lost_or_found === 'found' ? 'bg-tertiary-container text-on-tertiary-container' : 'bg-error-container text-on-error-container'"
                  >
                    {{ match.metadata.lost_or_found }}
                  </span>
                </div>
              </div>
              <div class="p-5">
                <h3 class="font-headline font-bold text-lg mb-0.5">{{ match.metadata.dog_name }}</h3>
                <p class="text-on-surface-variant text-xs mb-2">{{ match.metadata.breed }}</p>
                <p class="text-on-surface-variant text-sm line-clamp-2 mb-4">{{ match.metadata.distinctive_markings }}</p>
                <div class="flex items-center justify-between pt-3 border-t border-outline-variant/10">
                  <span class="flex items-center gap-1 text-xs font-label text-on-surface-variant">
                    <span class="material-symbols-outlined text-sm text-primary">location_on</span>
                    {{ match.metadata.location }}
                  </span>
                  <span class="text-primary font-headline font-bold text-xs hover:underline">View Details →</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="text-center py-20 bg-surface-container-lowest rounded-xl">
            <span class="material-symbols-outlined text-5xl text-outline-variant block mb-3">search_off</span>
            <h3 class="font-headline font-bold text-lg mb-1">No close matches found</h3>
            <p class="font-body text-sm text-on-surface-variant">Try a clearer photo or a different angle.</p>
          </div>
        </template>

        <!-- ── BROWSE ALL DOGS FEED ── -->
        <template v-else>
          <div class="flex items-end justify-between mb-6">
            <div>
              <h2 class="font-headline text-3xl font-extrabold tracking-tight">Browse Reports</h2>
              <p class="text-on-surface-variant text-sm mt-1">
                {{ feedLoading ? 'Loading…' : `${feedFiltered().length} report${feedFiltered().length !== 1 ? 's' : ''} · upload a photo to search by image` }}
              </p>
            </div>
          </div>

          <!-- Skeleton -->
          <div v-if="feedLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div v-for="i in 6" :key="i" class="bg-surface-container-lowest rounded-xl overflow-hidden animate-pulse">
              <div class="aspect-square bg-surface-container"></div>
              <div class="p-4 space-y-2">
                <div class="h-3 bg-surface-container rounded-full w-1/3"></div>
                <div class="h-4 bg-surface-container rounded-full w-2/3"></div>
                <div class="h-3 bg-surface-container rounded-full w-1/2"></div>
              </div>
            </div>
          </div>

          <!-- Feed grid -->
          <div v-else-if="feedFiltered().length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div
              v-for="dog in feedFiltered()"
              :key="dog.dog_id"
              class="bg-surface-container-lowest rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow group cursor-pointer"
              @click="viewMatchDetail(dog.dog_id)"
            >
              <div class="relative aspect-square overflow-hidden bg-surface-container">
                <img v-if="dog.image" :src="dog.image" :alt="dog.metadata.dog_name" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <span class="material-symbols-outlined text-5xl text-outline-variant">pets</span>
                </div>
                <div class="absolute top-3 left-3">
                  <span
                    class="text-[0.65rem] font-bold px-2 py-0.5 rounded-sm uppercase tracking-tight"
                    :class="dog.metadata.lost_or_found === 'found' ? 'bg-tertiary-container text-on-tertiary-container' : 'bg-error-container text-on-error-container'"
                  >
                    {{ dog.metadata.lost_or_found }}
                  </span>
                </div>
              </div>
              <div class="p-4">
                <h3 class="font-headline font-bold text-base mb-0.5">{{ dog.metadata.dog_name }}</h3>
                <p class="text-on-surface-variant text-xs mb-3">{{ dog.metadata.breed }}</p>
                <span class="flex items-center gap-1 text-xs font-label text-on-surface-variant">
                  <span class="material-symbols-outlined text-sm text-primary">location_on</span>
                  {{ dog.metadata.location }}
                </span>
              </div>
            </div>
          </div>

          <div v-else class="text-center py-20 bg-surface-container-lowest rounded-xl">
            <span class="material-symbols-outlined text-5xl text-outline-variant block mb-3">pets</span>
            <p class="font-body text-sm text-on-surface-variant">No reports yet.</p>
          </div>
        </template>

      </section>
    </main>

    <AppFooter />

    <RouterLink to="/report">
      <button class="fixed bottom-8 right-8 w-14 h-14 editorial-gradient text-on-primary rounded-full flex items-center justify-center shadow-lg active:scale-95 transition-transform z-40">
        <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">add</span>
      </button>
    </RouterLink>
  </div>
</template>

<style scoped>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
.editorial-gradient { background: linear-gradient(135deg, #815100 0%, #f8a010 100%); }
.bg-background { background-color: #fff5ea; }
.bg-surface-container { background-color: #ffe5bd; }
.bg-surface-container-low { background-color: #ffeed8; }
.bg-surface-container-lowest { background-color: #ffffff; }
.bg-surface-container-high { background-color: #ffdeaa; }
.bg-surface-container-highest { background-color: #ffd796; }
.bg-primary { background-color: #815100; }
.bg-secondary { background-color: #795500; }
.bg-tertiary { background-color: #645d00; }
.bg-tertiary-container { background-color: #faec55; }
.bg-error-container { background-color: #f95630; }
.text-on-background { color: #402b00; }
.text-on-surface { color: #402b00; }
.text-on-surface-variant { color: #735722; }
.text-on-primary { color: #fff0e3; }
.text-on-secondary { color: #fff1df; }
.text-on-tertiary { color: #fff5a1; }
.text-on-tertiary-container { color: #5d5600; }
.text-on-error-container { color: #520c00; }
.text-primary { color: #815100; }
.text-error { color: #b02500; }
.text-outline-variant { color: #cca86b; }
.border-outline-variant\/10 { border-color: rgba(204,168,107,0.1); }
.border-outline-variant\/30 { border-color: rgba(204,168,107,0.3); }
.font-headline { font-family: 'Plus Jakarta Sans', sans-serif; }
.font-body { font-family: 'Be Vietnam Pro', sans-serif; }
.font-label { font-family: 'Be Vietnam Pro', sans-serif; }
</style>
