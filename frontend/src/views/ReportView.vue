<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { storeToRefs } from "pinia";
import { reportDog, identifyBreed } from "@/api";
import { useAuthStore } from "@/stores/auth";
import NavBar from "@/components/NavBar.vue";
import AppFooter from "@/components/AppFooter.vue";
import MapPicker from "@/components/MapPicker.vue";

const router = useRouter();
const route = useRoute();
const { user } = storeToRefs(useAuthStore());

onMounted(() => {
  if (route.query.type === "found") lostOrFound.value = "found";
  else if (route.query.type === "lost") lostOrFound.value = "lost";
  if (user.value?.email) contactEmail.value = user.value.email;
});

const dogName = ref("");
const breed = ref("");
const color = ref("");
const age = ref("");
const marks = ref("");
const locationSearch = ref("");
const contactEmail = ref("");
const lostOrFound = ref<"lost" | "found">("lost");
const uploading = ref(false);
const error = ref("");
const identifying = ref(false);
const breedSuggestions = ref<{ breed: string; confidence: number }[]>([]);

const previewImgs = ref<string[]>([]);
const uploadedFiles = ref<File[]>([]);
const locationCoords = ref<{ lat: number; lng: number } | null>(null);

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  if (!input.files) return;
  const newFiles = Array.from(input.files);
  const remaining = 5 - uploadedFiles.value.length;
  for (const file of newFiles.slice(0, remaining)) {
    uploadedFiles.value.push(file);
    previewImgs.value.push(URL.createObjectURL(file));
  }
  input.value = "";
}

function removePhoto(idx: number) {
  uploadedFiles.value.splice(idx, 1);
  previewImgs.value.splice(idx, 1);
  if (uploadedFiles.value.length === 0) breedSuggestions.value = [];
}

async function runIdentify() {
  if (!uploadedFiles.value[0]) return;
  identifying.value = true;
  breedSuggestions.value = [];
  try {
    const res = await identifyBreed(uploadedFiles.value[0]);
    breedSuggestions.value = res.predictions;
  } catch {
    // silent — identify is optional
  } finally {
    identifying.value = false;
  }
}

function acceptBreed(b: string) {
  breed.value = b;
  breedSuggestions.value = [];
}

async function submitReport() {
  if (uploadedFiles.value.length === 0) {
    error.value = "Please upload at least one photo.";
    return;
  }
  if (!breed.value || !color.value || !age.value || !locationSearch.value || !contactEmail.value) {
    error.value = "Please fill in all required fields (breed, color, age, location, email).";
    return;
  }
  uploading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    for (const file of uploadedFiles.value) {
      form.append("images", file);
    }
    form.append("dog_name", dogName.value);
    form.append("breed", breed.value);
    form.append("color", color.value);
    form.append("age", age.value);
    form.append("distinctive_markings", marks.value);
    form.append("location", locationSearch.value);
    form.append("contact_email", contactEmail.value);
    form.append("lost_or_found", lostOrFound.value);
    if (locationCoords.value) {
      form.append("latitude", String(locationCoords.value.lat));
      form.append("longitude", String(locationCoords.value.lng));
    }
    const res = await reportDog(form);
    router.push({ path: "/report/success", query: { id: res.dog_id, type: lostOrFound.value } });
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Submission failed. Please try again.";
  } finally {
    uploading.value = false;
  }
}
</script>

<template>
  <div class="bg-surface font-body text-on-surface selection:bg-primary-container selection:text-on-primary-container">
    <NavBar />

    <main class="pt-32 pb-24 px-6 max-w-5xl mx-auto">
      <header class="mb-12 text-center">
        <h1 class="font-headline text-4xl font-extrabold text-on-surface tracking-tight mb-3">Help them find their way home.</h1>
        <p class="font-body text-on-surface-variant max-w-xl mx-auto">Your detailed report helps our community reconnect lost pets with their families. Every detail counts.</p>
      </header>

      <!-- Lost / Found toggle -->
      <div class="flex justify-center mb-12">
        <div class="bg-surface-container-high rounded-full p-1 flex gap-1">
          <button
            @click="lostOrFound = 'lost'"
            :class="['px-8 py-2.5 rounded-full font-headline font-bold text-sm transition-colors', lostOrFound === 'lost' ? 'bg-error-container text-on-error-container shadow' : 'text-on-surface-variant hover:bg-surface-container']"
          >
            I Lost a Dog
          </button>
          <button
            @click="lostOrFound = 'found'"
            :class="['px-8 py-2.5 rounded-full font-headline font-bold text-sm transition-colors', lostOrFound === 'found' ? 'bg-tertiary-container text-on-tertiary-container shadow' : 'text-on-surface-variant hover:bg-surface-container']"
          >
            I Found a Dog
          </button>
        </div>
      </div>

      <div class="bg-surface-container-low rounded-xl p-1 md:p-2">
        <div class="bg-surface-container-lowest rounded-lg p-8 md:p-12 shadow-sm">

          <!-- Step 1: Photo Upload -->
          <section class="space-y-6" id="step-1">
            <div>
              <h2 class="font-headline text-2xl font-bold text-on-surface mb-2">Upload Photos</h2>
              <p class="font-body text-sm text-on-surface-variant mb-6">Add up to 5 photos. Multiple angles improve match accuracy. The first photo is the primary.</p>
            </div>

            <!-- Upload zone (only shown if under 5 files) -->
            <label v-if="uploadedFiles.length < 5" class="border-2 border-dashed border-outline-variant/30 rounded-xl p-10 flex flex-col items-center justify-center bg-surface hover:bg-surface-container-low transition-colors group cursor-pointer">
              <span class="material-symbols-outlined text-5xl text-primary mb-4 group-hover:scale-110 transition-transform" style="font-variation-settings: 'FILL' 1;">add_a_photo</span>
              <p class="font-headline font-semibold text-on-surface mb-1">Click to upload</p>
              <p class="font-body text-sm text-on-surface-variant">{{ uploadedFiles.length }}/5 photos added</p>
              <input type="file" accept="image/*" multiple class="hidden" @change="onFileChange" />
            </label>

            <!-- Thumbnail strip -->
            <div v-if="previewImgs.length > 0" class="flex gap-3 flex-wrap">
              <div
                v-for="(img, idx) in previewImgs"
                :key="idx"
                class="relative w-24 h-24 rounded-xl overflow-hidden bg-surface-container"
              >
                <img :src="img" :alt="`Photo ${idx + 1}`" class="w-full h-full object-cover" />
                <div v-if="idx === 0" class="absolute bottom-0 left-0 right-0 bg-primary/80 text-on-primary text-[0.6rem] text-center py-0.5 font-bold">PRIMARY</div>
                <button
                  type="button"
                  @click="removePhoto(idx)"
                  class="absolute top-1 right-1 bg-black/50 text-white rounded-full w-5 h-5 flex items-center justify-center"
                >
                  <span class="material-symbols-outlined text-xs">close</span>
                </button>
              </div>
            </div>
          </section>

          <hr class="my-12 border-none h-px bg-surface-container" />

          <!-- Step 2: Dog Details -->
          <section class="space-y-10" id="step-2">
            <h2 class="font-headline text-2xl font-bold text-on-surface">Dog Details &amp; Location</h2>
            <div class="grid md:grid-cols-2 gap-8">
              <div class="space-y-6">
                <div class="space-y-2">
                  <label class="font-label text-sm font-semibold text-on-surface-variant ml-1">Dog Name <span class="text-on-surface-variant font-normal">(optional)</span></label>
                  <input v-model="dogName" class="w-full bg-surface-container-high border-none rounded-lg p-4 focus:bg-surface-container-highest transition-colors focus:ring-2 focus:ring-primary/20 placeholder:text-on-surface-variant/50" placeholder="e.g. Buddy, Max — or leave blank" type="text" />
                </div>
                <div class="space-y-2">
                  <div class="flex items-center justify-between ml-1 mb-1">
                    <label class="font-label text-sm font-semibold text-on-surface-variant">Breed <span class="text-error">*</span></label>
                    <button
                      type="button"
                      @click="runIdentify"
                      :disabled="uploadedFiles.length === 0 || identifying"
                      class="text-xs font-headline font-semibold text-primary flex items-center gap-1 disabled:opacity-40 disabled:cursor-not-allowed hover:underline"
                    >
                      <span class="material-symbols-outlined text-sm">auto_awesome</span>
                      {{ identifying ? 'Identifying…' : 'Identify from photo' }}
                    </button>
                  </div>
                  <input v-model="breed" class="w-full bg-surface-container-high border-none rounded-lg p-4 focus:bg-surface-container-highest transition-colors focus:ring-2 focus:ring-primary/20 placeholder:text-on-surface-variant/50" placeholder="e.g. Beagle, Mixed Breed" type="text" />
                  <!-- Breed suggestions -->
                  <div v-if="breedSuggestions.length > 0" class="flex flex-wrap gap-2 mt-1">
                    <button
                      v-for="s in breedSuggestions"
                      :key="s.breed"
                      type="button"
                      @click="acceptBreed(s.breed)"
                      class="flex items-center gap-1.5 px-3 py-1.5 bg-primary-container text-on-primary-container rounded-full text-xs font-headline font-semibold hover:brightness-95 transition-all"
                    >
                      {{ s.breed }}
                      <span class="opacity-70">{{ Math.round(s.confidence * 100) }}%</span>
                    </button>
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <label class="font-label text-sm font-semibold text-on-surface-variant ml-1">Primary Color <span class="text-error">*</span></label>
                    <select v-model="color" class="w-full bg-surface-container-high border-none rounded-lg p-4 focus:bg-surface-container-highest transition-colors focus:ring-2 focus:ring-primary/20">
                      <option value="">Select color</option>
                      <option>Golden</option>
                      <option>Black</option>
                      <option>White</option>
                      <option>Brown</option>
                      <option>Brindle</option>
                      <option>Tricolor</option>
                      <option>Grey</option>
                      <option>Tan</option>
                    </select>
                  </div>
                  <div class="space-y-2">
                    <label class="font-label text-sm font-semibold text-on-surface-variant ml-1">Estimated Age <span class="text-error">*</span></label>
                    <select v-model="age" class="w-full bg-surface-container-high border-none rounded-lg p-4 focus:bg-surface-container-highest transition-colors focus:ring-2 focus:ring-primary/20">
                      <option value="">Select age</option>
                      <option>Puppy</option>
                      <option>Young</option>
                      <option>Adult</option>
                      <option>Senior</option>
                    </select>
                  </div>
                </div>
                <div class="space-y-2">
                  <label class="font-label text-sm font-semibold text-on-surface-variant ml-1">Distinguishing Marks</label>
                  <textarea v-model="marks" class="w-full bg-surface-container-high border-none rounded-lg p-4 focus:bg-surface-container-highest transition-colors focus:ring-2 focus:ring-primary/20 placeholder:text-on-surface-variant/50" placeholder="Scars, collar color, unique patterns..." rows="3"></textarea>
                </div>
              </div>
              <div class="space-y-6">
                <div class="space-y-2">
                  <label class="font-label text-sm font-semibold text-on-surface-variant ml-1">Location <span class="text-error">*</span></label>
                  <input v-model="locationSearch" class="w-full bg-surface-container-high border-none rounded-lg p-4 focus:bg-surface-container-highest transition-colors focus:ring-2 focus:ring-primary/20 placeholder:text-on-surface-variant/50" placeholder="e.g. Brooklyn, NY" type="text" />
                </div>
                <div class="space-y-2">
                  <label class="font-label text-sm font-semibold text-on-surface-variant ml-1">Pin on Map <span class="text-on-surface-variant font-normal">(optional — enables radius search)</span></label>
                  <MapPicker v-model="locationCoords" />
                </div>
              </div>
            </div>
          </section>

          <hr class="my-12 border-none h-px bg-surface-container" />

          <!-- Step 3: Contact -->
          <section class="space-y-6" id="step-3">
            <h2 class="font-headline text-2xl font-bold text-on-surface">Contact Information</h2>
            <!-- Logged in: show read-only email pill -->
            <div v-if="user" class="flex items-center gap-3 bg-surface-container rounded-xl px-5 py-4">
              <span class="material-symbols-outlined text-primary text-xl" style="font-variation-settings:'FILL' 1;">check_circle</span>
              <div>
                <p class="font-headline font-semibold text-sm text-on-surface">Using your account email</p>
                <p class="font-label text-xs text-on-surface-variant">{{ user.email }}</p>
              </div>
            </div>
            <!-- Guest: show input -->
            <template v-else>
              <p class="font-body text-sm text-on-surface-variant">Shared only when a match is confirmed.</p>
              <div class="space-y-2">
                <label class="font-label text-sm font-semibold text-on-surface-variant ml-1">Email <span class="text-error">*</span></label>
                <input v-model="contactEmail" class="w-full bg-surface-container-high border-none rounded-lg p-4 focus:bg-surface-container-highest transition-colors focus:ring-2 focus:ring-primary/20" placeholder="you@example.com" type="email" />
              </div>
            </template>
          </section>

          <p v-if="error" class="mt-6 text-sm text-error font-medium">{{ error }}</p>

          <div class="mt-16 flex justify-end">
            <button
              @click="submitReport"
              :disabled="uploading"
              class="btn-gradient px-12 py-4 rounded-full text-on-primary font-headline font-bold text-lg shadow-lg hover:scale-[1.02] transition-transform flex items-center space-x-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <span>{{ uploading ? "Submitting..." : "Submit Report" }}</span>
              <span class="material-symbols-outlined text-lg">arrow_forward</span>
            </button>
          </div>

        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
.btn-gradient { background: linear-gradient(135deg, #815100 0%, #f8a010 100%); }
</style>
