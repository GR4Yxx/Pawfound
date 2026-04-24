<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { getDog, sendMessage } from "@/api";
import type { DogDetailResponse } from "@/types";
import NavBar from "@/components/NavBar.vue";
import AppFooter from "@/components/AppFooter.vue";
import PhotoGallery from "@/components/PhotoGallery.vue";
import { useAuthStore } from "@/stores/auth";
import { storeToRefs } from "pinia";

const route = useRoute();
const { user, isLoggedIn } = storeToRefs(useAuthStore());

const dog = ref<DogDetailResponse | null>(null);
const loading = ref(true);
const error = ref("");

// Context passed from BrowseView via router state
const fromScan = ref(false);
const scanPreview = ref<string | null>(null);
const scanSimilarity = ref<number | null>(null);

// Message panel
const showMessagePanel = ref(false);
const messageBody = ref("");
const messageSending = ref(false);
const messageError = ref("");
const messageSent = ref(false);

// Map (lazy loaded)
let mapInstance: any = null;
const mapContainer = ref<HTMLElement | null>(null);

const isOwner = computed(() =>
  isLoggedIn.value && user.value?.email === dog.value?.metadata.contact_email,
);

const allImages = computed(() => {
  if (!dog.value) return [];
  if (dog.value.images && dog.value.images.length > 0) return dog.value.images;
  return dog.value.image ? [dog.value.image] : [];
});

const similarityPct = computed(() => Math.round((scanSimilarity.value ?? 0) * 100));

onMounted(async () => {
  const state = window.history.state as { similarity?: number; uploadPreview?: string } | null;
  if (state?.similarity != null) {
    fromScan.value = true;
    scanSimilarity.value = state.similarity;
    scanPreview.value = state.uploadPreview ?? null;
  }

  try {
    dog.value = await getDog(route.params.id as string);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to load dog details.";
  } finally {
    loading.value = false;
  }

  if (dog.value?.latitude != null && dog.value?.longitude != null) {
    await nextTick();
    await loadMiniMap(dog.value.latitude, dog.value.longitude);
  }
});

async function loadMiniMap(lat: number, lng: number) {
  if (!mapContainer.value) return;
  const L = (await import("leaflet")).default;
  delete (L.Icon.Default.prototype as any)._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  });
  mapInstance = L.map(mapContainer.value, { zoomControl: false, dragging: false, scrollWheelZoom: false }).setView([lat, lng], 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap",
    maxZoom: 18,
  }).addTo(mapInstance);
  L.marker([lat, lng]).addTo(mapInstance);
}

async function submitMessage() {
  if (!messageBody.value.trim() || !dog.value) return;
  messageSending.value = true;
  messageError.value = "";
  try {
    const msgId = dog.value.chroma_id ?? dog.value.dog_id;
    await sendMessage(msgId, messageBody.value.trim());
    messageSent.value = true;
    messageBody.value = "";
    showMessagePanel.value = false;
  } catch (e: unknown) {
    messageError.value = e instanceof Error ? e.message : "Failed to send message.";
  } finally {
    messageSending.value = false;
  }
}
</script>

<template>
  <div class="bg-surface text-on-surface font-body min-h-screen flex flex-col">
    <NavBar />

    <main class="flex-1 pt-24 pb-20 max-w-7xl mx-auto w-full px-6 md:px-8">

      <!-- Back link -->
      <div class="mb-8 animate-fade-up">
        <RouterLink to="/browse" class="inline-flex items-center gap-1.5 text-sm font-headline font-semibold text-on-surface-variant hover:text-primary transition-colors">
          <span class="material-symbols-outlined text-sm">arrow_back</span>
          {{ fromScan ? 'Back to search results' : 'Back to browse' }}
        </RouterLink>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="space-y-6">
        <div class="h-8 skeleton rounded-full w-1/4"></div>
        <div class="grid md:grid-cols-2 gap-6">
          <div class="aspect-square skeleton rounded-xl"></div>
          <div class="space-y-4">
            <div class="h-5 skeleton rounded-full w-3/4"></div>
            <div class="h-4 skeleton rounded-full w-1/2"></div>
            <div class="h-32 skeleton rounded-xl"></div>
          </div>
        </div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="text-center py-24">
        <span class="material-symbols-outlined text-5xl text-outline-variant block mb-4">error_outline</span>
        <p class="text-error font-headline font-semibold">{{ error }}</p>
      </div>

      <template v-else-if="dog">

        <!-- Reunited banner -->
        <div v-if="dog.status === 'reunited'" class="mb-6 bg-tertiary-container text-on-tertiary-container rounded-xl px-6 py-4 flex items-center gap-3 animate-fade-up">
          <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">favorite</span>
          <div>
            <p class="font-headline font-bold">Reunited!</p>
            <p class="text-sm opacity-80">This dog has been reunited with their owner.</p>
          </div>
        </div>

        <!-- ── COMPARISON MODE ── -->
        <template v-if="fromScan">
          <div class="mb-8 animate-fade-up">
            <span class="font-label text-xs uppercase tracking-widest text-primary font-semibold mb-1 block">AI Visual Comparison</span>
            <h1 class="font-headline text-3xl font-extrabold text-on-surface">
              {{ similarityPct }}% match — {{ dog.metadata.dog_name }}
            </h1>
          </div>

          <!-- Side-by-side -->
          <div class="grid grid-cols-2 gap-4 mb-8 animate-fade-up" style="animation-delay:0.05s;">
            <div class="card overflow-hidden">
              <div class="px-4 pt-4 pb-2 flex items-center justify-between">
                <span class="font-label text-xs uppercase tracking-widest text-on-surface-variant font-semibold">Your photo</span>
                <span class="text-[0.6rem] font-bold px-2 py-0.5 bg-surface-container rounded-full uppercase tracking-wide text-on-surface-variant">Reference</span>
              </div>
              <div class="aspect-square overflow-hidden bg-surface-container mx-3 mb-3 rounded-lg">
                <img v-if="scanPreview" :src="scanPreview" alt="Your uploaded photo" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <span class="material-symbols-outlined text-4xl text-outline-variant">image</span>
                </div>
              </div>
            </div>

            <div class="card overflow-hidden">
              <div class="px-4 pt-4 pb-2 flex items-center justify-between">
                <span class="font-label text-xs uppercase tracking-widest text-on-surface-variant font-semibold">Matched dog</span>
                <span
                  class="text-[0.6rem] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide"
                  :class="dog.metadata.lost_or_found === 'found' ? 'bg-tertiary-container text-on-tertiary-container' : 'bg-error-container text-on-error-container'"
                >{{ dog.metadata.lost_or_found }}</span>
              </div>
              <div class="mx-3 mb-3">
                <PhotoGallery v-if="allImages.length > 0" :images="allImages" />
                <div v-else class="aspect-square flex items-center justify-center bg-surface-container rounded-lg">
                  <span class="material-symbols-outlined text-4xl text-outline-variant">pets</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Similarity bar -->
          <div class="card p-6 mb-8 flex items-center gap-6 animate-fade-up" style="animation-delay:0.10s;">
            <div class="flex-1">
              <div class="flex justify-between text-xs font-label text-on-surface-variant mb-2">
                <span>Visual similarity score</span>
                <span class="font-bold text-on-surface">{{ similarityPct }}%</span>
              </div>
              <div class="h-2.5 w-full bg-surface-container rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-700"
                  :class="(scanSimilarity ?? 0) >= 0.8 ? 'bg-tertiary' : (scanSimilarity ?? 0) >= 0.6 ? 'bg-primary' : 'bg-secondary'"
                  :style="`width: ${similarityPct}%`"
                ></div>
              </div>
              <p class="text-xs text-on-surface-variant mt-2">
                <template v-if="(scanSimilarity ?? 0) >= 0.8">Strong visual match — very likely the same dog.</template>
                <template v-else-if="(scanSimilarity ?? 0) >= 0.6">Good match — worth investigating further.</template>
                <template v-else>Partial match — review the details below.</template>
              </p>
            </div>
            <div class="text-center shrink-0 w-20">
              <span
                class="block text-4xl font-extrabold font-headline leading-none"
                :class="(scanSimilarity ?? 0) >= 0.8 ? 'text-tertiary' : 'text-primary'"
              >{{ similarityPct }}%</span>
              <span class="text-xs font-label text-on-surface-variant">match</span>
            </div>
          </div>
        </template>

        <!-- ── STANDARD MODE ── -->
        <template v-else>
          <div class="mb-8 animate-fade-up">
            <div class="flex items-center gap-2 mb-3">
              <span
                class="badge"
                :class="dog.metadata.lost_or_found === 'found' ? 'badge-found' : 'badge-lost'"
              >{{ dog.metadata.lost_or_found }}</span>
              <span v-if="dog.status === 'reunited'" class="badge badge-reunited">
                <span class="material-symbols-outlined text-xs" style="font-variation-settings:'FILL' 1;">favorite</span>
                Reunited
              </span>
            </div>
            <h1 class="font-headline text-4xl font-extrabold text-on-surface mb-1">{{ dog.metadata.dog_name || 'Unknown Dog' }}</h1>
            <p class="font-label text-sm text-on-surface-variant">{{ dog.metadata.breed }}</p>
          </div>
        </template>

        <!-- ── Content grid ── -->
        <div class="grid grid-cols-1 md:grid-cols-12 gap-8">

          <!-- Photos column (standard mode only) -->
          <div v-if="!fromScan" class="md:col-span-5 space-y-4 animate-fade-up" style="animation-delay:0.05s;">
            <PhotoGallery v-if="allImages.length > 0" :images="allImages" />
            <div v-else class="aspect-square bg-surface-container rounded-xl flex items-center justify-center">
              <span class="material-symbols-outlined text-6xl text-outline-variant">pets</span>
            </div>

            <!-- Mini map -->
            <div v-show="dog.latitude != null" class="card p-3">
              <h4 class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-2 px-1">Last Known Location</h4>
              <div ref="mapContainer" class="w-full h-44 rounded-lg overflow-hidden"></div>
            </div>
          </div>

          <!-- Details column -->
          <div :class="fromScan ? 'md:col-span-12' : 'md:col-span-7'" class="flex flex-col gap-5 animate-fade-up" style="animation-delay:0.10s;">

            <!-- Details grid -->
            <div class="card p-6">
              <h3 class="font-headline font-bold text-sm text-on-surface-variant uppercase tracking-widest mb-5">Dog Details</h3>
              <div class="grid grid-cols-2 gap-x-8 gap-y-5">
                <div>
                  <p class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-1">Breed</p>
                  <p class="font-headline font-semibold text-on-surface">{{ dog.metadata.breed || '—' }}</p>
                </div>
                <div>
                  <p class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-1">Color</p>
                  <p class="font-headline font-semibold text-on-surface">{{ dog.metadata.color || '—' }}</p>
                </div>
                <div>
                  <p class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-1">Age</p>
                  <p class="font-headline font-semibold text-on-surface">{{ dog.metadata.age || '—' }}</p>
                </div>
                <div>
                  <p class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-1">Location</p>
                  <p class="font-headline font-semibold text-on-surface flex items-center gap-1">
                    <span class="material-symbols-outlined text-sm text-primary">location_on</span>
                    {{ dog.metadata.location || '—' }}
                  </p>
                </div>
                <div class="col-span-2" v-if="dog.metadata.distinctive_markings">
                  <p class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-1">Distinctive Markings</p>
                  <p class="font-body text-sm leading-relaxed text-on-surface">{{ dog.metadata.distinctive_markings }}</p>
                </div>
              </div>
            </div>

            <!-- Contact card -->
            <div class="card p-6">
              <p class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-5 text-center">
                {{ dog.metadata.lost_or_found === 'found' ? 'Someone found this dog' : 'Owner is searching for this dog' }}
              </p>

              <!-- Message sent -->
              <div v-if="messageSent" class="mb-4 bg-tertiary-container text-on-tertiary-container text-sm font-headline font-semibold text-center px-4 py-3.5 rounded-xl flex items-center justify-center gap-2">
                <span class="material-symbols-outlined text-sm" style="font-variation-settings:'FILL' 1;">check_circle</span>
                Message sent! They'll be notified.
              </div>

              <!-- Message compose panel -->
              <div v-if="showMessagePanel" class="mb-4 space-y-3">
                <textarea
                  v-model="messageBody"
                  placeholder="Write your message..."
                  rows="4"
                  maxlength="2000"
                  class="w-full bg-surface-container-high border-none rounded-xl p-4 text-sm focus:ring-2 focus:ring-primary/20 placeholder:text-on-surface-variant/50 resize-none focus:outline-none transition-colors"
                ></textarea>
                <p v-if="messageError" class="text-xs text-error font-medium flex items-center gap-1">
                  <span class="material-symbols-outlined text-xs">error</span>{{ messageError }}
                </p>
                <div class="flex gap-2">
                  <button
                    @click="submitMessage"
                    :disabled="messageSending || !messageBody.trim()"
                    class="flex-1 btn btn-primary btn-sm"
                  >
                    <span v-if="messageSending" class="material-symbols-outlined text-sm animate-spin-slow">autorenew</span>
                    {{ messageSending ? 'Sending…' : 'Send Message' }}
                  </button>
                  <button
                    @click="showMessagePanel = false; messageBody = ''; messageError = ''"
                    class="btn btn-ghost btn-sm px-4"
                  >Cancel</button>
                </div>
              </div>

              <div v-if="!showMessagePanel" class="flex flex-col gap-2.5">
                <button
                  v-if="isLoggedIn && !isOwner && !messageSent"
                  @click="showMessagePanel = true"
                  class="btn btn-primary w-full"
                >
                  <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">chat</span>
                  Message {{ dog.metadata.lost_or_found === 'found' ? 'Finder' : 'Owner' }}
                </button>

                <a
                  :href="`mailto:${dog.metadata.contact_email}`"
                  class="btn btn-secondary w-full text-on-surface"
                >
                  <span class="material-symbols-outlined text-sm">mail</span>
                  Email {{ dog.metadata.lost_or_found === 'found' ? 'Finder' : 'Owner' }}
                </a>

                <p v-if="!isLoggedIn" class="text-center text-xs text-on-surface-variant">
                  <RouterLink to="/login" class="text-primary font-semibold hover:underline">Sign in</RouterLink>
                  to send an in-app message
                </p>
              </div>

              <p class="mt-4 text-center text-xs text-on-surface-variant opacity-60">{{ dog.metadata.contact_email }}</p>
            </div>

            <!-- Map in comparison mode -->
            <div v-if="fromScan && dog.latitude != null" class="card p-3">
              <h4 class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-2 px-1">Last Known Location</h4>
              <div ref="mapContainer" class="w-full h-44 rounded-lg overflow-hidden"></div>
            </div>

          </div>
        </div>

      </template>

      <div v-else-if="!loading" class="text-center py-24 text-on-surface-variant">
        <span class="material-symbols-outlined text-5xl block mb-4">search_off</span>
        Dog not found.
      </div>

    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
</style>
