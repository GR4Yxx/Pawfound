<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { matchDog, listDogs, getDog } from "@/api";
import type { MatchResult, DogDetailResponse } from "@/types";
import { usePendingMatch } from "@/stores/matchQueue";
import MapPicker from "@/components/MapPicker.vue";
import NavBar from "@/components/NavBar.vue";
import AppFooter from "@/components/AppFooter.vue";

const router = useRouter();
const route = useRoute();
const { take: takePendingMatch } = usePendingMatch();

const uploadedFile = ref<File | null>(null);
const uploadPreview = ref<string | null>(null);
const scanning = ref(false);
const error = ref("");
const pendingExcludeId = ref<string | null>(null);
const pendingLostOrFound = ref<"lost" | "found" | null>(null);
const matches = ref<MatchResult[]>([]);
const hasScanned = ref(false);
const allDogs = ref<DogDetailResponse[]>([]);
const feedLoading = ref(true);
const feedFilter = ref<"all" | "lost" | "found">("all");
const showLocationFilter = ref(false);
const filterCoords = ref<{ lat: number; lng: number } | null>(null);
const filterRadiusKm = ref(25);

const feedFiltered = () =>
  feedFilter.value === "all"
    ? allDogs.value
    : allDogs.value.filter(d => d.metadata.lost_or_found === feedFilter.value);

onMounted(async () => {
  const scanId = route.query.scan as string | undefined;
  const scanType = route.query.type as "lost" | "found" | undefined;
  if (scanId) {
    try {
      const reported = await getDog(scanId);
      if (reported.image) {
        const res = await fetch(reported.image);
        const blob = await res.blob();
        uploadedFile.value = new File([blob], `${reported.metadata.dog_name}.jpg`, { type: blob.type });
        uploadPreview.value = reported.image;
        pendingExcludeId.value = scanId;
        pendingLostOrFound.value = scanType === "lost" ? "found" : "lost";
        await scanForMatches();
      }
    } catch { /* silent */ }
  }

  const pending = takePendingMatch();
  if (!scanId && pending) {
    uploadPreview.value = pending.dataUrl;
    pendingExcludeId.value = pending.dogId;
    pendingLostOrFound.value = pending.lostOrFound === "lost" ? "found" : "lost";
    const res = await fetch(pending.dataUrl);
    const blob = await res.blob();
    uploadedFile.value = new File([blob], pending.filename, { type: blob.type });
    await scanForMatches();
  }

  try {
    const geo = filterCoords.value
      ? { lat: filterCoords.value.lat, lng: filterCoords.value.lng, radiusKm: filterRadiusKm.value }
      : undefined;
    const res = await listDogs(40, 0, geo);
    allDogs.value = res.dogs;
  } catch { /* silent */ }
  finally { feedLoading.value = false; }
});

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  if (input.files?.[0]) {
    uploadedFile.value = input.files[0];
    uploadPreview.value = URL.createObjectURL(input.files[0]);
    hasScanned.value = false;
    matches.value = [];
    pendingExcludeId.value = null;
    pendingLostOrFound.value = null;
  }
}

function onDrop(e: DragEvent) {
  e.preventDefault();
  const file = e.dataTransfer?.files[0];
  if (file) {
    uploadedFile.value = file;
    uploadPreview.value = URL.createObjectURL(file);
    hasScanned.value = false;
    matches.value = [];
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
  if (!uploadedFile.value) { error.value = "Please upload a photo first."; return; }
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
    error.value = e instanceof Error ? e.message : "Scan failed.";
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
    allDogs.value = (await listDogs(40, 0, geo)).dogs;
  } catch { /* silent */ }
  finally { feedLoading.value = false; }
}

function viewDetail(dogId: string, similarity?: number) {
  router.push({ path: `/browse/${dogId}`, state: { similarity, uploadPreview: uploadPreview.value } });
}
</script>

<template>
  <div style="background-color:#fff5ea; min-height:100vh;">
    <NavBar />

    <main class="pt-24 pb-20 px-6 md:px-10 max-w-7xl mx-auto">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">

        <!-- ── Sidebar ── -->
        <aside class="lg:col-span-4 space-y-4">

          <!-- Search panel -->
          <div class="card card-raised overflow-hidden animate-fade-up">
            <div class="editorial-gradient px-6 py-5">
              <h1 class="font-headline text-xl font-extrabold text-on-primary mb-0.5">Find a Match</h1>
              <p class="font-label text-xs" style="color:rgba(255,240,227,0.75);">Upload a photo — our AI scans every report instantly.</p>
            </div>

            <div class="p-5">
              <div @dragover.prevent @drop="onDrop">
                <label class="block aspect-square w-full rounded-xl cursor-pointer relative overflow-hidden transition-all group border-2 border-dashed hover:border-primary/40" style="background:#ffeed8; border-color:rgba(204,168,107,0.3);">
                  <img v-if="uploadPreview" :src="uploadPreview" class="absolute inset-0 w-full h-full object-cover" alt="preview" />
                  <div v-else class="w-full h-full flex flex-col items-center justify-center gap-3 p-6 text-center">
                    <div class="w-14 h-14 editorial-gradient rounded-2xl flex items-center justify-center shadow-btn group-hover:shadow-btn-hover transition-shadow">
                      <span class="material-symbols-outlined text-on-primary text-2xl" style="font-variation-settings:'FILL' 1;">add_a_photo</span>
                    </div>
                    <p class="font-headline font-semibold text-on-surface text-sm">Drop photo or click to browse</p>
                    <p class="text-xs text-on-surface-variant font-label">JPG · PNG · max 5MB</p>
                  </div>
                  <div v-if="uploadPreview" class="absolute inset-0 bg-black/0 group-hover:bg-black/25 transition-colors flex items-center justify-center">
                    <span class="opacity-0 group-hover:opacity-100 transition-opacity text-white font-headline font-bold text-sm bg-black/40 px-3 py-1.5 rounded-full">Change photo</span>
                  </div>
                  <input type="file" accept="image/*" class="hidden" @change="onFileChange" />
                </label>
              </div>

              <div class="mt-4 space-y-2">
                <button
                  @click="scanForMatches"
                  :disabled="scanning || !uploadedFile"
                  class="btn btn-primary w-full"
                >
                  <span v-if="scanning" class="material-symbols-outlined text-lg animate-spin-slow">autorenew</span>
                  <span v-else class="material-symbols-outlined text-lg" style="font-variation-settings:'FILL' 1;">manage_search</span>
                  {{ scanning ? "Scanning…" : "Scan for Matches" }}
                </button>
                <button v-if="uploadPreview" @click="clearUpload" class="btn btn-ghost w-full btn-sm">
                  <span class="material-symbols-outlined text-sm">close</span>
                  Clear &amp; browse all
                </button>
                <p v-if="error" class="text-xs text-error font-medium text-center pt-1">{{ error }}</p>
              </div>
            </div>
          </div>

          <!-- Feed filter -->
          <div v-if="!hasScanned" class="card p-4 animate-fade-up" style="animation-delay:0.05s;">
            <p class="font-label text-xs uppercase tracking-widest text-on-surface-variant font-semibold mb-3">Filter by type</p>
            <div class="flex gap-2">
              <button
                v-for="f in (['all', 'lost', 'found'] as const)"
                :key="f"
                @click="feedFilter = f"
                class="flex-1 py-2.5 rounded-full text-xs font-headline font-bold capitalize transition-all"
                :class="feedFilter === f ? 'editorial-gradient text-on-primary shadow-btn' : 'btn-tonal'"
              >{{ f }}</button>
            </div>
          </div>

          <!-- Location filter -->
          <div class="card p-4 animate-fade-up" style="animation-delay:0.10s;">
            <button @click="showLocationFilter = !showLocationFilter" class="w-full flex items-center justify-between">
              <span class="font-label text-xs uppercase tracking-widest text-on-surface-variant font-semibold">Filter by Location</span>
              <span class="material-symbols-outlined text-on-surface-variant text-base transition-transform duration-200" :class="showLocationFilter ? 'rotate-180' : ''">expand_more</span>
            </button>
            <div v-if="showLocationFilter" class="mt-4 space-y-4 animate-slide-down">
              <div>
                <label class="font-label text-xs text-on-surface-variant mb-1.5 block">Radius: <span class="font-bold text-on-surface">{{ filterRadiusKm }} km</span></label>
                <input type="range" v-model.number="filterRadiusKm" min="1" max="200" step="1" class="w-full accent-primary" />
              </div>
              <MapPicker v-model="filterCoords" />
              <button @click="applyLocationFilter" class="btn btn-primary w-full btn-sm">Apply Filter</button>
              <button v-if="filterCoords" @click="filterCoords = null; applyLocationFilter()" class="btn btn-ghost w-full btn-sm">Clear Filter</button>
            </div>
          </div>

        </aside>

        <!-- ── Main panel ── -->
        <section class="lg:col-span-8">

          <!-- SCAN RESULTS -->
          <template v-if="hasScanned">
            <div class="flex items-end justify-between mb-6 animate-fade-up">
              <div>
                <span class="font-label text-xs uppercase tracking-widest text-primary font-semibold mb-1 block">AI Results</span>
                <h2 class="font-headline text-3xl font-extrabold">Visual Matches</h2>
                <p class="text-on-surface-variant text-sm mt-1">
                  {{ matches.length > 0
                    ? `${matches.length} match${matches.length !== 1 ? 'es' : ''} found — sorted by visual similarity`
                    : 'No matches above the similarity threshold' }}
                </p>
              </div>
            </div>

            <div v-if="matches.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div
                v-for="(match, i) in matches"
                :key="match.dog_id"
                class="card card-hover group overflow-hidden"
                :class="`stagger-${Math.min(i + 1, 6)}`"
                @click="viewDetail(match.dog_id, match.similarity)"
              >
                <div class="relative aspect-square overflow-hidden" style="background:#ffe5bd;">
                  <img v-if="match.image" :src="match.image" :alt="match.metadata.dog_name" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                  <div v-else class="w-full h-full flex items-center justify-center">
                    <span class="material-symbols-outlined text-5xl text-outline-variant">pets</span>
                  </div>
                  <div class="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent"></div>
                  <span
                    class="badge absolute top-2.5 left-2.5 shadow-md"
                    :class="match.similarity >= 0.8 ? 'bg-tertiary text-on-tertiary' : match.similarity >= 0.6 ? 'editorial-gradient text-on-primary' : 'bg-surface-container text-on-surface'"
                  >{{ Math.round(match.similarity * 100) }}% match</span>
                  <span
                    class="badge absolute top-2.5 right-2.5 shadow-md"
                    :class="match.metadata.lost_or_found === 'found' ? 'badge-found' : 'badge-lost'"
                  >{{ match.metadata.lost_or_found }}</span>
                </div>
                <div class="p-5">
                  <h3 class="font-headline font-bold text-lg mb-0.5 text-on-surface">{{ match.metadata.dog_name }}</h3>
                  <p class="text-on-surface-variant text-xs mb-3 font-label">{{ match.metadata.breed }}</p>
                  <div class="flex items-center justify-between">
                    <span class="flex items-center gap-1 text-xs font-label text-on-surface-variant">
                      <span class="material-symbols-outlined text-sm text-primary">location_on</span>
                      {{ match.metadata.location }}
                    </span>
                    <span class="text-primary font-headline font-bold text-xs">View Details →</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="card p-16 text-center animate-scale-in">
              <span class="material-symbols-outlined text-5xl text-outline-variant block mb-4">search_off</span>
              <h3 class="font-headline font-bold text-xl mb-2">No close matches found</h3>
              <p class="font-body text-sm text-on-surface-variant mb-6 max-w-xs mx-auto">Try a clearer photo or a different angle. Your report is still live.</p>
              <button @click="clearUpload" class="btn btn-tonal btn-sm">Browse all reports →</button>
            </div>
          </template>

          <!-- BROWSE FEED -->
          <template v-else>
            <div class="flex items-end justify-between mb-6 animate-fade-up">
              <div>
                <span class="font-label text-xs uppercase tracking-widest text-primary font-semibold mb-1 block">Community Reports</span>
                <h2 class="font-headline text-3xl font-extrabold">Browse Dogs</h2>
                <p class="text-on-surface-variant text-sm mt-1">
                  {{ feedLoading ? 'Loading…' : `${feedFiltered().length} report${feedFiltered().length !== 1 ? 's' : ''} · upload a photo to search by image` }}
                </p>
              </div>
            </div>

            <div v-if="feedLoading" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
              <div v-for="i in 6" :key="i" class="card overflow-hidden">
                <div class="aspect-square skeleton"></div>
                <div class="p-4 space-y-2">
                  <div class="skeleton h-3 w-1/3"></div>
                  <div class="skeleton h-4 w-2/3"></div>
                  <div class="skeleton h-3 w-1/2"></div>
                </div>
              </div>
            </div>

            <div v-else-if="feedFiltered().length > 0" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
              <div
                v-for="(dog, i) in feedFiltered()"
                :key="dog.dog_id"
                class="card card-hover group overflow-hidden"
                :class="`stagger-${Math.min(i + 1, 6)}`"
                @click="viewDetail(dog.dog_id)"
              >
                <div class="relative aspect-square overflow-hidden" style="background:#ffe5bd;">
                  <img v-if="dog.image" :src="dog.image" :alt="dog.metadata.dog_name" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                  <div v-else class="w-full h-full flex items-center justify-center">
                    <span class="material-symbols-outlined text-5xl text-outline-variant">pets</span>
                  </div>
                  <div class="absolute inset-0 bg-gradient-to-t from-black/25 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  <span class="badge absolute top-2.5 left-2.5" :class="dog.metadata.lost_or_found === 'found' ? 'badge-found' : 'badge-lost'">{{ dog.metadata.lost_or_found }}</span>
                  <span v-if="dog.status === 'reunited'" class="badge badge-reunited absolute top-2.5 right-2.5">
                    <span class="material-symbols-outlined text-xs" style="font-variation-settings:'FILL' 1;">favorite</span>
                    Reunited
                  </span>
                </div>
                <div class="p-4">
                  <h3 class="font-headline font-bold text-base mb-0.5 text-on-surface">{{ dog.metadata.dog_name || 'Unknown Dog' }}</h3>
                  <p class="text-on-surface-variant text-xs mb-2 font-label">{{ dog.metadata.breed }}</p>
                  <span class="flex items-center gap-1 text-xs font-label text-on-surface-variant">
                    <span class="material-symbols-outlined text-sm text-primary">location_on</span>
                    {{ dog.metadata.location }}
                  </span>
                </div>
              </div>
            </div>

            <div v-else class="card p-16 text-center">
              <span class="material-symbols-outlined text-5xl text-outline-variant block mb-3">pets</span>
              <p class="font-body text-sm text-on-surface-variant">No reports yet.</p>
            </div>
          </template>

        </section>
      </div>
    </main>

    <AppFooter />

    <!-- FAB -->
    <RouterLink to="/report">
      <button class="btn btn-primary fixed bottom-8 right-8 shadow-card-raised z-40 animate-fade-in">
        <span class="material-symbols-outlined text-lg" style="font-variation-settings:'FILL' 1;">add</span>
        Report a Dog
      </button>
    </RouterLink>
  </div>
</template>

<style scoped>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
.editorial-gradient { background: linear-gradient(135deg, #815100 0%, #f8a010 100%); }
</style>
