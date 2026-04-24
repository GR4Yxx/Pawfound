<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch } from "vue";
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

// Context passed from MatchesView via router state
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

  // Load map after loading=false so the template has fully rendered
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
    await sendMessage(dog.value.dog_id, messageBody.value.trim());
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
  <div class="bg-surface text-on-surface font-body">
    <NavBar />

    <main class="pt-24 pb-20 max-w-7xl mx-auto px-8">

      <div class="mb-8">
        <RouterLink to="/matches" class="inline-flex items-center text-on-surface-variant hover:text-primary transition-colors text-sm font-medium gap-1">
          <span class="material-symbols-outlined text-sm">arrow_back</span>
          {{ fromScan ? 'Back to search results' : 'Back to browse' }}
        </RouterLink>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="space-y-6 animate-pulse">
        <div class="h-8 bg-surface-container rounded-full w-1/4"></div>
        <div class="grid md:grid-cols-2 gap-6">
          <div class="aspect-square bg-surface-container rounded-xl"></div>
          <div class="aspect-square bg-surface-container rounded-xl"></div>
        </div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="text-center py-24 text-error">
        <span class="material-symbols-outlined text-4xl block mb-3">error_outline</span>
        {{ error }}
      </div>

      <template v-else-if="dog">

        <!-- Reunited banner -->
        <div v-if="dog.status === 'reunited'" class="mb-6 bg-tertiary-container text-on-tertiary-container rounded-xl px-6 py-4 flex items-center gap-3">
          <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">favorite</span>
          <span class="font-headline font-semibold">This dog has been reunited with their owner!</span>
        </div>

        <!-- ── COMPARISON MODE (came from scan) ── -->
        <template v-if="fromScan">
          <div class="mb-8">
            <span class="font-label text-xs uppercase tracking-widest text-on-surface-variant mb-1 block">Visual Comparison</span>
            <h1 class="font-headline text-3xl font-extrabold text-on-surface">
              {{ Math.round((scanSimilarity ?? 0) * 100) }}% match with {{ dog.metadata.dog_name }}
            </h1>
          </div>

          <!-- Side-by-side photos -->
          <div class="grid grid-cols-2 gap-4 mb-10">
            <div class="bg-surface-container-lowest rounded-xl overflow-hidden shadow-sm">
              <div class="px-4 pt-4 pb-2 flex items-center justify-between">
                <span class="font-label text-xs uppercase tracking-widest text-on-surface-variant">Your photo</span>
                <span class="text-[0.65rem] font-bold px-2 py-0.5 bg-surface-container rounded-sm uppercase text-on-surface-variant">Reference</span>
              </div>
              <div class="aspect-square overflow-hidden bg-surface-container mx-3 mb-3 rounded-lg">
                <img v-if="scanPreview" :src="scanPreview" alt="Your uploaded photo" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <span class="material-symbols-outlined text-4xl text-outline-variant">image</span>
                </div>
              </div>
            </div>

            <div class="bg-surface-container-lowest rounded-xl overflow-hidden shadow-sm">
              <div class="px-4 pt-4 pb-2 flex items-center justify-between">
                <span class="font-label text-xs uppercase tracking-widest text-on-surface-variant">Matched dog</span>
                <span
                  class="text-[0.65rem] font-bold px-2 py-0.5 rounded-sm uppercase"
                  :class="dog.metadata.lost_or_found === 'found' ? 'bg-tertiary-container text-on-tertiary-container' : 'bg-error-container text-on-error-container'"
                >
                  {{ dog.metadata.lost_or_found }}
                </span>
              </div>
              <div class="mx-3 mb-3">
                <PhotoGallery v-if="allImages.length > 0" :images="allImages" />
                <div v-else class="aspect-square flex items-center justify-center bg-surface-container rounded-lg">
                  <span class="material-symbols-outlined text-4xl text-outline-variant">pets</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Similarity meter -->
          <div class="bg-surface-container-lowest rounded-xl p-6 mb-8 flex items-center gap-6 shadow-sm">
            <div class="flex-1">
              <div class="flex justify-between text-xs font-label text-on-surface-variant mb-2">
                <span>Visual similarity score</span>
                <span class="font-bold text-on-surface">{{ Math.round((scanSimilarity ?? 0) * 100) }}%</span>
              </div>
              <div class="h-2 w-full bg-surface-container rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-700"
                  :class="(scanSimilarity ?? 0) >= 0.8 ? 'bg-tertiary' : (scanSimilarity ?? 0) >= 0.6 ? 'bg-primary' : 'bg-secondary'"
                  :style="`width: ${Math.round((scanSimilarity ?? 0) * 100)}%`"
                ></div>
              </div>
            </div>
            <div class="text-center shrink-0">
              <span
                class="block text-3xl font-extrabold font-headline"
                :class="(scanSimilarity ?? 0) >= 0.8 ? 'text-tertiary' : 'text-primary'"
              >
                {{ Math.round((scanSimilarity ?? 0) * 100) }}%
              </span>
              <span class="text-xs font-label text-on-surface-variant">Match</span>
            </div>
          </div>
        </template>

        <!-- ── STANDARD MODE (browsing directly) ── -->
        <template v-else>
          <div class="mb-8">
            <div class="flex items-center gap-3 mb-2">
              <span
                class="text-xs font-bold px-3 py-1 rounded-sm uppercase tracking-wide"
                :class="dog.metadata.lost_or_found === 'found' ? 'bg-tertiary-container text-on-tertiary-container' : 'bg-error-container text-on-error-container'"
              >
                {{ dog.metadata.lost_or_found }}
              </span>
            </div>
            <h1 class="font-headline text-4xl font-extrabold text-on-surface mb-1">{{ dog.metadata.dog_name }}</h1>
            <p class="font-label text-sm text-on-surface-variant">{{ dog.metadata.breed }}</p>
          </div>
        </template>

        <!-- ── Dog details (shared) ── -->
        <div class="grid grid-cols-1 md:grid-cols-12 gap-8">

          <!-- Photo (only in standard mode) -->
          <div v-if="!fromScan" class="md:col-span-5">
            <PhotoGallery v-if="allImages.length > 0" :images="allImages" />
            <div v-else class="aspect-square bg-surface-container rounded-xl flex items-center justify-center">
              <span class="material-symbols-outlined text-6xl text-outline-variant">pets</span>
            </div>

            <!-- Mini-map (if coordinates available) -->
            <div v-show="dog.latitude != null" class="mt-4">
              <h4 class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-2">Last Known Location</h4>
              <div ref="mapContainer" class="w-full h-48 rounded-xl overflow-hidden border border-outline-variant/20"></div>
            </div>
          </div>

          <div :class="fromScan ? 'md:col-span-12' : 'md:col-span-7'" class="flex flex-col gap-6">

            <!-- Details grid -->
            <div class="bg-surface-container-low rounded-xl p-6 grid grid-cols-2 gap-5">
              <div>
                <h4 class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-1">Breed</h4>
                <p class="font-headline font-semibold">{{ dog.metadata.breed || '—' }}</p>
              </div>
              <div>
                <h4 class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-1">Color</h4>
                <p class="font-headline font-semibold">{{ dog.metadata.color || '—' }}</p>
              </div>
              <div>
                <h4 class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-1">Age</h4>
                <p class="font-headline font-semibold">{{ dog.metadata.age || '—' }}</p>
              </div>
              <div>
                <h4 class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-1">Location</h4>
                <p class="font-headline font-semibold flex items-center gap-1">
                  <span class="material-symbols-outlined text-sm text-primary">location_on</span>
                  {{ dog.metadata.location || '—' }}
                </p>
              </div>
              <div class="col-span-2">
                <h4 class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-1">Distinctive Markings</h4>
                <p class="font-body text-sm leading-relaxed">{{ dog.metadata.distinctive_markings || 'None noted.' }}</p>
              </div>
            </div>

            <!-- Contact -->
            <div class="bg-surface-container-lowest rounded-xl p-6 border border-outline-variant/10">
              <p class="text-xs font-label uppercase tracking-widest text-on-surface-variant mb-4 text-center">
                {{ dog.metadata.lost_or_found === 'found' ? 'Someone found this dog' : 'Owner is looking for this dog' }}
              </p>

              <!-- Message sent confirmation -->
              <div v-if="messageSent" class="mb-4 bg-tertiary-container text-on-tertiary-container text-sm font-medium text-center px-4 py-3 rounded-xl">
                Message sent! They'll be notified.
              </div>

              <!-- Message panel -->
              <div v-if="showMessagePanel" class="mb-4 space-y-3">
                <textarea
                  v-model="messageBody"
                  placeholder="Write your message..."
                  rows="4"
                  maxlength="2000"
                  class="w-full bg-surface-container-high border-none rounded-lg p-3 text-sm focus:ring-2 focus:ring-primary/20 placeholder:text-on-surface-variant/50 resize-none"
                ></textarea>
                <p v-if="messageError" class="text-xs text-error">{{ messageError }}</p>
                <div class="flex gap-2">
                  <button
                    @click="submitMessage"
                    :disabled="messageSending || !messageBody.trim()"
                    class="flex-1 btn-gradient text-on-primary py-2.5 rounded-full font-headline font-bold text-sm disabled:opacity-60"
                  >
                    {{ messageSending ? 'Sending...' : 'Send Message' }}
                  </button>
                  <button
                    @click="showMessagePanel = false; messageBody = ''; messageError = ''"
                    class="px-4 py-2.5 rounded-full font-headline font-bold text-sm bg-surface-container text-on-surface-variant"
                  >
                    Cancel
                  </button>
                </div>
              </div>

              <div class="flex flex-col gap-2" v-if="!showMessagePanel">
                <!-- In-app message button (only for logged-in non-owners) -->
                <button
                  v-if="isLoggedIn && !isOwner && !messageSent"
                  @click="showMessagePanel = true"
                  class="w-full btn-gradient text-on-primary py-3.5 px-8 rounded-full font-headline font-bold flex items-center justify-center gap-2 shadow-md hover:brightness-110 active:scale-95 transition-all duration-150"
                >
                  <span class="material-symbols-outlined">chat</span>
                  Message {{ dog.metadata.lost_or_found === 'found' ? 'Finder' : 'Owner' }}
                </button>

                <!-- Email fallback -->
                <a
                  :href="`mailto:${dog.metadata.contact_email}`"
                  class="w-full text-center py-3 px-8 rounded-full font-headline font-bold text-sm border border-outline-variant/30 text-on-surface-variant hover:bg-surface-container transition-colors flex items-center justify-center gap-2"
                >
                  <span class="material-symbols-outlined text-sm">mail</span>
                  Email {{ dog.metadata.lost_or_found === 'found' ? 'Finder' : 'Owner' }}
                </a>
              </div>

              <p class="mt-3 text-center text-xs text-on-surface-variant">
                {{ dog.metadata.contact_email }}
              </p>
            </div>
          </div>
        </div>

      </template>

      <div v-else class="text-center py-24 text-on-surface-variant">Dog not found.</div>

    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
.btn-gradient { background: linear-gradient(135deg, #815100 0%, #f8a010 100%); }
.bg-surface { background-color: #fff5ea; }
.bg-surface-container { background-color: #ffe5bd; }
.bg-surface-container-low { background-color: #ffeed8; }
.bg-surface-container-lowest { background-color: #ffffff; }
.bg-surface-container-high { background-color: #ffdeaa; }
.bg-secondary { background-color: #795500; }
.bg-tertiary { background-color: #645d00; }
.bg-tertiary-container { background-color: #faec55; }
.bg-error-container { background-color: #f95630; }
.text-on-surface { color: #402b00; }
.text-on-surface-variant { color: #735722; }
.text-on-primary { color: #fff0e3; }
.text-on-tertiary-container { color: #5d5600; }
.text-on-error-container { color: #520c00; }
.text-primary { color: #815100; }
.text-secondary { color: #795500; }
.text-tertiary { color: #645d00; }
.text-error { color: #b02500; }
.text-outline-variant { color: #cca86b; }
.border-outline-variant\/10 { border-color: rgba(204,168,107,0.1); }
.border-outline-variant\/20 { border-color: rgba(204,168,107,0.2); }
.font-headline { font-family: 'Plus Jakarta Sans', sans-serif; }
.font-body { font-family: 'Be Vietnam Pro', sans-serif; }
.font-label { font-family: 'Be Vietnam Pro', sans-serif; }
</style>
