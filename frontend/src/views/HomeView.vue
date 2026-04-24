<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { RouterLink } from "vue-router";
import { storeToRefs } from "pinia";
import NavBar from "@/components/NavBar.vue";
import AppFooter from "@/components/AppFooter.vue";
import DogCard from "@/components/DogCard.vue";
import { listDogs } from "@/api";
import { useAuthStore } from "@/stores/auth";
import { useInboxStore } from "@/stores/inbox";
import type { DogDetailResponse } from "@/types";

const { user, isLoggedIn } = storeToRefs(useAuthStore());
const inboxStore = useInboxStore();

const recentDogs = ref<DogDetailResponse[]>([]);
const myDogs = ref<(DogDetailResponse & { created_at?: string | null; status?: string })[]>([]);
const loadingFeed = ref(true);
const loadingMyDogs = ref(true);

const BASE = `${import.meta.env.VITE_API_BASE_URL ?? ""}/api`;

onMounted(async () => {
  try {
    const res = await listDogs(8, 0);
    recentDogs.value = res.dogs;
  } catch { /* silent */ }
  finally { loadingFeed.value = false; }

  if (isLoggedIn.value) {
    try {
      const res = await fetch(`${BASE}/users/me/dogs`, { credentials: "include" });
      if (res.ok) myDogs.value = (await res.json()).dogs;
    } catch { /* silent */ }
    finally { loadingMyDogs.value = false; }
  } else {
    loadingMyDogs.value = false;
  }
});

const activeDogs = computed(() => myDogs.value.filter(d => d.status !== "reunited"));
const reunitedCount = computed(() => myDogs.value.filter(d => d.status === "reunited").length);

// Pick two dogs for the hero mockup — prefer one lost + one found
const heroDogA = computed(() =>
  recentDogs.value.find(d => d.metadata.lost_or_found === "lost") ?? recentDogs.value[0] ?? null
);
const heroDogB = computed(() =>
  recentDogs.value.find(d => d.metadata.lost_or_found === "found") ?? recentDogs.value[1] ?? null
);
</script>

<template>
  <div class="min-h-screen" style="background-color:#fff5ea;">
    <NavBar />

    <!-- ══════════════════════════════════════════
         GUEST LANDING
    ══════════════════════════════════════════ -->
    <template v-if="!isLoggedIn">
      <main>

        <!-- ── HERO ── -->
        <section class="relative overflow-hidden pt-28 pb-20 px-6 md:px-10">
          <!-- Background ambient glow -->
          <div class="absolute -top-32 right-0 w-[600px] h-[600px] rounded-full pointer-events-none" style="background:radial-gradient(circle, rgba(248,160,16,0.15) 0%, transparent 65%);"></div>
          <div class="absolute bottom-0 left-0 w-80 h-80 rounded-full pointer-events-none" style="background:radial-gradient(circle, rgba(250,236,85,0.12) 0%, transparent 70%);"></div>

          <div class="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center relative z-10">

            <!-- Left: copy -->
            <div class="animate-fade-up">
              <span class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold uppercase tracking-widest mb-7 font-label" style="background:rgba(129,81,0,0.08); color:#815100; border:1px solid rgba(129,81,0,0.15);">
                <span class="w-1.5 h-1.5 rounded-full animate-pulse inline-block" style="background:#f8a010;"></span>
                AI-Powered Pet Recovery
              </span>

              <h1 class="font-headline font-extrabold leading-[1.05] mb-5 text-on-surface" style="font-size:clamp(2.5rem,5vw,3.75rem);">
                Every lost dog deserves<br/>
                <span class="text-gradient">a way back home.</span>
              </h1>

              <p class="font-body text-lg text-on-surface-variant max-w-lg mb-8 leading-relaxed">
                Submit a photo report and our AI instantly scans thousands of entries to find visual matches — in under a second.
              </p>

              <div class="flex flex-wrap gap-3 mb-8">
                <RouterLink to="/report?type=lost" class="btn btn-primary text-base px-8 py-4">
                  <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">search</span>
                  I Lost My Dog
                </RouterLink>
                <RouterLink to="/report?type=found" class="btn btn-secondary text-base px-8 py-4">
                  <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">pets</span>
                  I Found a Dog
                </RouterLink>
              </div>

              <!-- Trust signals -->
              <div class="flex items-center gap-6">
                <div class="text-center">
                  <p class="font-headline font-extrabold text-2xl text-gradient">30+</p>
                  <p class="font-label text-[0.65rem] uppercase tracking-widest text-on-surface-variant">Active Reports</p>
                </div>
                <div class="w-px h-8" style="background:rgba(204,168,107,0.4);"></div>
                <div class="text-center">
                  <p class="font-headline font-extrabold text-2xl text-gradient">&lt;1s</p>
                  <p class="font-label text-[0.65rem] uppercase tracking-widest text-on-surface-variant">Match Speed</p>
                </div>
                <div class="w-px h-8" style="background:rgba(204,168,107,0.4);"></div>
                <div class="text-center">
                  <p class="font-headline font-extrabold text-2xl text-gradient">1280</p>
                  <p class="font-label text-[0.65rem] uppercase tracking-widest text-on-surface-variant">Embedding Dims</p>
                </div>
              </div>

              <p class="mt-6 text-xs text-on-surface-variant font-label">
                Already have an account?
                <RouterLink to="/login" class="text-primary font-semibold hover:underline ml-1">Sign in →</RouterLink>
              </p>
            </div>

            <!-- Right: live product preview -->
            <div class="relative hidden lg:block animate-fade-up" style="animation-delay:0.12s;">
              <!-- Main match result card mockup -->
              <div class="card card-raised overflow-hidden">
                <!-- Header bar -->
                <div class="px-5 py-3.5 flex items-center justify-between border-b" style="border-color:rgba(204,168,107,0.2);">
                  <div class="flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full" style="background:#f95630;"></span>
                    <span class="w-2.5 h-2.5 rounded-full" style="background:#faec55;"></span>
                    <span class="w-2.5 h-2.5 rounded-full" style="background:#4caf50;"></span>
                  </div>
                  <span class="font-label text-xs text-on-surface-variant">AI Match Results</span>
                  <span class="font-label text-[0.65rem] text-on-surface-variant opacity-0">.</span>
                </div>

                <!-- Side-by-side comparison -->
                <div class="grid grid-cols-2 gap-0">
                  <div class="p-4 border-r" style="border-color:rgba(204,168,107,0.2);">
                    <p class="font-label text-[0.65rem] uppercase tracking-widest text-on-surface-variant mb-2">Lost dog</p>
                    <div class="aspect-square rounded-xl overflow-hidden relative flex items-center justify-center" style="background:linear-gradient(135deg,#ffeed8,#ffd796);">
                      <img v-if="heroDogA?.image" :src="heroDogA.image" :alt="heroDogA.metadata.dog_name" class="w-full h-full object-cover" />
                      <span v-else class="material-symbols-outlined text-primary opacity-40" style="font-size:5rem;font-variation-settings:'FILL' 1;">pets</span>
                      <span class="badge badge-lost absolute bottom-2 left-2">Lost</span>
                    </div>
                    <p class="font-label text-xs text-on-surface-variant mt-2 text-center truncate">{{ heroDogA?.metadata.breed || 'Golden Retriever' }}</p>
                  </div>
                  <div class="p-4">
                    <p class="font-label text-[0.65rem] uppercase tracking-widest text-on-surface-variant mb-2">Found nearby</p>
                    <div class="aspect-square rounded-xl overflow-hidden relative flex items-center justify-center" style="background:linear-gradient(135deg,#ffd796,#ffdeaa);">
                      <img v-if="heroDogB?.image" :src="heroDogB.image" :alt="heroDogB.metadata.dog_name" class="w-full h-full object-cover" />
                      <span v-else class="material-symbols-outlined text-primary opacity-40" style="font-size:5rem;font-variation-settings:'FILL' 1;">pets</span>
                      <span class="badge badge-found absolute bottom-2 left-2">Found</span>
                    </div>
                    <p class="font-label text-xs text-on-surface-variant mt-2 text-center truncate">{{ heroDogB?.metadata.location || 'Brooklyn, NY' }}</p>
                  </div>
                </div>

                <!-- Similarity bar -->
                <div class="px-5 py-4 border-t" style="border-color:rgba(204,168,107,0.2); background:#fffdf8;">
                  <div class="flex items-center justify-between mb-2">
                    <span class="font-label text-xs text-on-surface-variant">Visual similarity</span>
                    <span class="font-headline font-extrabold text-sm text-gradient">87% match</span>
                  </div>
                  <div class="h-2 w-full rounded-full overflow-hidden" style="background:#ffeed8;">
                    <div class="h-full rounded-full editorial-gradient transition-all" style="width:87%;"></div>
                  </div>
                  <p class="font-label text-[0.65rem] text-on-surface-variant mt-2 text-center">
                    <span class="material-symbols-outlined text-xs text-primary">bolt</span>
                    Result returned in 0.38s · EfficientNetV2 + ChromaDB
                  </p>
                </div>
              </div>

              <!-- Floating notification -->
              <div class="card card-raised absolute -top-4 -right-6 p-3.5 w-52 animate-fade-up" style="animation-delay:0.3s;">
                <div class="flex items-start gap-2.5">
                  <div class="w-8 h-8 editorial-gradient rounded-lg flex items-center justify-center shrink-0">
                    <span class="material-symbols-outlined text-on-primary text-sm" style="font-variation-settings:'FILL' 1;">notifications_active</span>
                  </div>
                  <div>
                    <p class="font-headline font-bold text-xs text-on-surface">New match found!</p>
                    <p class="font-label text-[0.65rem] text-on-surface-variant mt-0.5">A dog matching Buddy was reported near you.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- ── HOW IT WORKS ── -->
        <section class="py-24 px-6 md:px-10" style="background:#ffeed8;">
          <div class="max-w-7xl mx-auto">

            <div class="text-center mb-16">
              <span class="font-label text-xs uppercase tracking-widest font-semibold text-primary block mb-3">Simple Process</span>
              <h2 class="font-headline text-4xl font-extrabold text-on-surface mb-4">From report to reunion</h2>
              <p class="font-body text-on-surface-variant max-w-lg mx-auto">Three steps. Under 2 minutes to file. AI works in the background around the clock.</p>
            </div>

            <!-- Step 1 -->
            <div class="grid lg:grid-cols-2 gap-12 items-center mb-20">
              <div class="stagger-1">
                <span class="inline-flex items-center justify-center w-10 h-10 editorial-gradient rounded-2xl text-on-primary font-headline font-extrabold text-lg shadow-btn mb-6">1</span>
                <h3 class="font-headline font-extrabold text-2xl text-on-surface mb-4">File a detailed report</h3>
                <p class="font-body text-on-surface-variant leading-relaxed mb-6">
                  Upload up to 5 photos, add breed, color, age, and drop a pin on the map. Our AI identifies the breed from your photo automatically.
                </p>
                <ul class="space-y-2">
                  <li v-for="f in ['Multi-photo upload (up to 5)', 'AI breed identification from photo', 'Map pin for radius search', 'Instant live on submission']" :key="f"
                    class="flex items-center gap-2.5 font-label text-sm text-on-surface-variant">
                    <span class="material-symbols-outlined text-primary text-base" style="font-variation-settings:'FILL' 1;">check_circle</span>
                    {{ f }}
                  </li>
                </ul>
              </div>
              <!-- Report form mockup -->
              <div class="card card-raised overflow-hidden stagger-2">
                <div class="p-5 border-b flex items-center gap-2" style="border-color:rgba(204,168,107,0.2);">
                  <span class="material-symbols-outlined text-primary text-lg" style="font-variation-settings:'FILL' 1;">add_a_photo</span>
                  <span class="font-headline font-bold text-sm text-on-surface">Report a Dog</span>
                </div>
                <div class="p-5 space-y-3">
                  <!-- Photo strip mockup -->
                  <div class="grid grid-cols-5 gap-2">
                    <div class="aspect-square rounded-lg overflow-hidden relative col-span-1">
                      <img v-if="heroDogA?.image" :src="heroDogA.image" class="w-full h-full object-cover" />
                      <div v-else class="w-full h-full editorial-gradient flex items-center justify-center">
                        <span class="material-symbols-outlined text-on-primary text-lg" style="font-variation-settings:'FILL' 1;">pets</span>
                      </div>
                      <span class="absolute bottom-0 left-0 right-0 text-[0.5rem] text-center font-bold text-on-primary py-0.5" style="background:rgba(0,0,0,0.35);">PRIMARY</span>
                    </div>
                    <div v-for="(dog, i) in recentDogs.slice(1, 3)" :key="i" class="aspect-square rounded-lg overflow-hidden">
                      <img v-if="dog.image" :src="dog.image" class="w-full h-full object-cover" />
                      <div v-else class="w-full h-full" style="background:#ffeed8;"></div>
                    </div>
                    <div class="aspect-square rounded-lg border-2 border-dashed flex items-center justify-center col-span-2" style="border-color:rgba(204,168,107,0.4);">
                      <span class="material-symbols-outlined text-outline-variant text-lg">add</span>
                    </div>
                  </div>
                  <!-- Fields mockup -->
                  <div class="grid grid-cols-2 gap-2">
                    <div class="rounded-lg p-2.5 flex items-center gap-2" style="background:#ffdeaa;">
                      <span class="material-symbols-outlined text-primary text-sm" style="font-variation-settings:'FILL' 1;">auto_awesome</span>
                      <span class="font-label text-xs text-on-surface truncate">{{ heroDogA?.metadata.breed || 'Golden Retriever' }}</span>
                    </div>
                    <div class="rounded-lg p-2.5" style="background:#ffdeaa;">
                      <span class="font-label text-xs text-on-surface-variant truncate">{{ heroDogA?.metadata.color || 'Golden' }} · {{ heroDogA?.metadata.age || 'Adult' }}</span>
                    </div>
                  </div>
                  <div class="rounded-lg p-2.5 flex items-center gap-2" style="background:#ffdeaa;">
                    <span class="material-symbols-outlined text-primary text-sm">location_on</span>
                    <span class="font-label text-xs text-on-surface truncate">{{ heroDogA?.metadata.location || 'Brooklyn, NY' }}</span>
                  </div>
                  <div class="editorial-gradient rounded-full py-2.5 text-center">
                    <span class="font-headline font-bold text-xs text-on-primary">Submit Report</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Step 2 -->
            <div class="grid lg:grid-cols-2 gap-12 items-center mb-20">
              <!-- AI match mockup -->
              <div class="card card-raised overflow-hidden stagger-1 order-2 lg:order-1">
                <div class="p-5 border-b flex items-center justify-between" style="border-color:rgba(204,168,107,0.2);">
                  <span class="font-headline font-bold text-sm text-on-surface">Visual Match Results</span>
                  <span class="badge badge-found">3 found</span>
                </div>
                <div class="p-4 space-y-3">
                  <div v-for="(m, i) in [
                    { score: 87, dog: recentDogs[0] },
                    { score: 74, dog: recentDogs[1] },
                    { score: 61, dog: recentDogs[2] },
                  ].filter(m => m.dog)" :key="i"
                    class="flex items-center gap-3 p-3 rounded-xl"
                    :style="i === 0 ? 'background:#fff5ea; box-shadow:0 2px 8px rgba(64,43,0,0.08);' : 'background:#fffdf8;'"
                  >
                    <div class="w-12 h-12 rounded-xl shrink-0 overflow-hidden" style="background:linear-gradient(135deg,#ffeed8,#ffd796);">
                      <img v-if="m.dog?.image" :src="m.dog.image" class="w-full h-full object-cover" />
                      <div v-else class="w-full h-full flex items-center justify-center">
                        <span class="material-symbols-outlined text-primary text-xl" style="font-variation-settings:'FILL' 1;">pets</span>
                      </div>
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center justify-between mb-1">
                        <span class="font-headline font-bold text-sm text-on-surface">{{ m.score }}% match</span>
                        <span class="badge" :class="m.dog?.metadata.lost_or_found === 'found' ? 'badge-found' : 'badge-lost'">{{ m.dog?.metadata.lost_or_found }}</span>
                      </div>
                      <div class="h-1.5 w-full rounded-full overflow-hidden" style="background:#ffeed8;">
                        <div class="h-full rounded-full editorial-gradient" :style="`width:${m.score}%;`"></div>
                      </div>
                      <p class="font-label text-[0.65rem] text-on-surface-variant mt-1 flex items-center gap-1">
                        <span class="material-symbols-outlined text-xs text-primary">location_on</span>
                        {{ m.dog?.metadata.location || '—' }}
                      </p>
                    </div>
                  </div>
                </div>
                <div class="px-4 pb-4">
                  <p class="font-label text-[0.65rem] text-on-surface-variant text-center">
                    <span class="material-symbols-outlined text-xs text-primary">bolt</span>
                    Scanned 30+ reports in 0.38s using 1280-dim embeddings
                  </p>
                </div>
              </div>
              <div class="stagger-2 order-1 lg:order-2">
                <span class="inline-flex items-center justify-center w-10 h-10 editorial-gradient rounded-2xl text-on-primary font-headline font-extrabold text-lg shadow-btn mb-6">2</span>
                <h3 class="font-headline font-extrabold text-2xl text-on-surface mb-4">AI scans every report instantly</h3>
                <p class="font-body text-on-surface-variant leading-relaxed mb-6">
                  Your photo is embedded into 1280 dimensions using EfficientNetV2 and compared against every report using cosine similarity — results in under a second.
                </p>
                <ul class="space-y-2">
                  <li v-for="f in ['Visual similarity scoring', 'Sorted by match confidence', 'Location-aware filtering', 'Email alerts for new matches']" :key="f"
                    class="flex items-center gap-2.5 font-label text-sm text-on-surface-variant">
                    <span class="material-symbols-outlined text-primary text-base" style="font-variation-settings:'FILL' 1;">check_circle</span>
                    {{ f }}
                  </li>
                </ul>
              </div>
            </div>

            <!-- Step 3 -->
            <div class="grid lg:grid-cols-2 gap-12 items-center">
              <div class="stagger-1">
                <span class="inline-flex items-center justify-center w-10 h-10 editorial-gradient rounded-2xl text-on-primary font-headline font-extrabold text-lg shadow-btn mb-6">3</span>
                <h3 class="font-headline font-extrabold text-2xl text-on-surface mb-4">Connect and get reunited</h3>
                <p class="font-body text-on-surface-variant leading-relaxed mb-6">
                  Message the finder or owner directly through the app. No email addresses exposed until you're ready. Mark as reunited when your dog is home.
                </p>
                <ul class="space-y-2">
                  <li v-for="f in ['In-app messaging (no email needed)', 'Owner notified instantly', 'Mark as Reunited to close the report', 'Community celebrates every reunion']" :key="f"
                    class="flex items-center gap-2.5 font-label text-sm text-on-surface-variant">
                    <span class="material-symbols-outlined text-primary text-base" style="font-variation-settings:'FILL' 1;">check_circle</span>
                    {{ f }}
                  </li>
                </ul>
              </div>
              <!-- Messaging mockup -->
              <div class="card card-raised overflow-hidden stagger-2">
                <div class="p-4 border-b flex items-center gap-3" style="border-color:rgba(204,168,107,0.2);">
                  <div class="w-9 h-9 editorial-gradient rounded-full flex items-center justify-center shrink-0">
                    <span class="font-headline font-bold text-on-primary text-sm">B</span>
                  </div>
                  <div>
                    <p class="font-headline font-bold text-sm text-on-surface">About: Buddy</p>
                    <p class="font-label text-[0.65rem] text-on-surface-variant">Golden Retriever · Brooklyn, NY</p>
                  </div>
                  <span class="badge badge-found ml-auto">Reunited</span>
                </div>
                <div class="p-4 space-y-3" style="background:#fffdf8;">
                  <div class="flex justify-start">
                    <div class="rounded-2xl rounded-bl-sm px-4 py-2.5 max-w-[80%]" style="background:#ffe5bd;">
                      <p class="font-body text-xs text-on-surface">Hi! I found a golden retriever near Prospect Park. Is this your dog?</p>
                      <p class="font-label text-[0.6rem] text-on-surface-variant mt-1">2h ago</p>
                    </div>
                  </div>
                  <div class="flex justify-end">
                    <div class="rounded-2xl rounded-br-sm px-4 py-2.5 max-w-[80%] editorial-gradient">
                      <p class="font-body text-xs text-on-primary">Oh my gosh yes!! That's Buddy! Can I come pick him up?</p>
                      <p class="font-label text-[0.6rem] mt-1" style="color:rgba(255,240,227,0.6);">1h ago</p>
                    </div>
                  </div>
                  <div class="flex justify-start">
                    <div class="rounded-2xl rounded-bl-sm px-4 py-2.5 max-w-[80%]" style="background:#ffe5bd;">
                      <p class="font-body text-xs text-on-surface">Of course! He's been so well-behaved 🐾</p>
                      <p class="font-label text-[0.6rem] text-on-surface-variant mt-1">45m ago</p>
                    </div>
                  </div>
                </div>
                <div class="p-3 border-t flex items-center gap-2" style="border-color:rgba(204,168,107,0.2);">
                  <div class="flex-1 rounded-full px-4 py-2 font-body text-xs text-on-surface-variant" style="background:#ffeed8;">Type a message...</div>
                  <button class="w-8 h-8 editorial-gradient rounded-full flex items-center justify-center shrink-0 shadow-btn">
                    <span class="material-symbols-outlined text-on-primary text-sm" style="font-variation-settings:'FILL' 1;">send</span>
                  </button>
                </div>
              </div>
            </div>

          </div>
        </section>

        <!-- ── LIVE FEED ── -->
        <section class="py-24 px-6 md:px-10 max-w-7xl mx-auto">
          <div class="flex justify-between items-end mb-10">
            <div>
              <span class="font-label text-xs uppercase tracking-widest text-primary font-semibold mb-2 block">Community Reports</span>
              <h2 class="font-headline text-3xl font-extrabold text-on-surface">Dogs looking for help right now</h2>
            </div>
            <RouterLink to="/browse" class="btn btn-ghost btn-sm flex items-center gap-1.5 shrink-0">
              Browse all <span class="material-symbols-outlined text-sm">arrow_forward</span>
            </RouterLink>
          </div>

          <!-- Loading skeletons -->
          <div v-if="loadingFeed" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            <div v-for="i in 8" :key="i" class="card overflow-hidden">
              <div class="aspect-square skeleton"></div>
              <div class="p-3 space-y-2">
                <div class="skeleton h-3 w-2/3"></div>
                <div class="skeleton h-2.5 w-1/2"></div>
              </div>
            </div>
          </div>

          <div v-else-if="recentDogs.length > 0" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            <DogCard v-for="(dog, i) in recentDogs" :key="dog.dog_id" :dog="dog" :class="`stagger-${Math.min(i + 1, 6)}`" />
          </div>

          <div v-else class="card p-16 text-center">
            <span class="material-symbols-outlined text-5xl text-outline-variant block mb-4">pets</span>
            <p class="font-headline font-bold text-lg mb-2 text-on-surface">No reports yet</p>
            <p class="text-sm text-on-surface-variant mb-6">Be the first to help a dog get home.</p>
            <RouterLink to="/report" class="btn btn-primary btn-sm">
              <span class="material-symbols-outlined text-sm" style="font-variation-settings:'FILL' 1;">add</span>
              Submit a Report
            </RouterLink>
          </div>
        </section>

      </main>
    </template>

    <!-- ══════════════════════════════════════════
         LOGGED-IN DASHBOARD
    ══════════════════════════════════════════ -->
    <template v-else>
      <main class="pt-28 pb-20 max-w-6xl mx-auto px-6 md:px-10">

        <!-- Welcome -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-10 animate-fade-up">
          <div>
            <p class="font-label text-xs uppercase tracking-widest text-primary font-semibold mb-1">Welcome back</p>
            <h1 class="font-headline text-3xl font-extrabold text-on-surface">{{ user?.name }}</h1>
          </div>
          <RouterLink to="/report" class="btn btn-primary self-start sm:self-auto">
            <span class="material-symbols-outlined text-lg" style="font-variation-settings:'FILL' 1;">add</span>
            Report a Dog
          </RouterLink>
        </div>

        <!-- Stats row -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
          <div class="card p-5 stagger-1">
            <p class="font-label text-xs uppercase tracking-widest text-on-surface-variant mb-2">Active Reports</p>
            <p class="font-headline text-3xl font-extrabold text-on-surface">{{ activeDogs.length }}</p>
          </div>
          <div class="card p-5 stagger-2">
            <p class="font-label text-xs uppercase tracking-widest text-on-surface-variant mb-2">Reunited</p>
            <p class="font-headline text-3xl font-extrabold text-gradient">{{ reunitedCount }}</p>
          </div>
          <RouterLink to="/inbox" class="card card-hover col-span-2 p-5 flex items-center justify-between stagger-3">
            <div>
              <p class="font-label text-xs uppercase tracking-widest text-on-surface-variant mb-2">Unread Messages</p>
              <p class="font-headline text-3xl font-extrabold text-on-surface">{{ inboxStore.unreadCount }}</p>
            </div>
            <div class="flex items-center gap-2">
              <span v-if="inboxStore.unreadCount > 0" class="badge badge-lost px-3 py-1">{{ inboxStore.unreadCount }} new</span>
              <span class="material-symbols-outlined text-2xl text-primary" style="font-variation-settings:'FILL' 1;">mark_unread_chat_alt</span>
            </div>
          </RouterLink>
        </div>

        <!-- Active reports -->
        <div class="mb-12">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-headline text-xl font-bold text-on-surface">Your Active Reports</h2>
            <RouterLink to="/profile" class="btn btn-ghost btn-sm flex items-center gap-1">
              Manage all <span class="material-symbols-outlined text-sm">arrow_forward</span>
            </RouterLink>
          </div>

          <div v-if="loadingMyDogs" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <div v-for="i in 3" :key="i" class="card overflow-hidden">
              <div class="aspect-video skeleton"></div>
              <div class="p-4 space-y-2">
                <div class="skeleton h-3 w-2/3"></div>
                <div class="skeleton h-2.5 w-1/2"></div>
              </div>
            </div>
          </div>

          <div v-else-if="activeDogs.length === 0" class="card p-12 text-center">
            <span class="material-symbols-outlined text-5xl text-outline-variant block mb-4">pets</span>
            <h3 class="font-headline font-bold text-lg mb-2">No active reports</h3>
            <p class="font-body text-sm text-on-surface-variant mb-6">Submit a report to start finding matches.</p>
            <RouterLink to="/report" class="btn btn-primary btn-sm">
              <span class="material-symbols-outlined text-sm" style="font-variation-settings:'FILL' 1;">add</span>
              Report a Dog
            </RouterLink>
          </div>

          <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <RouterLink
              v-for="(dog, i) in activeDogs.slice(0, 6)"
              :key="dog.dog_id"
              :to="`/browse/${dog.dog_id}`"
              class="card card-hover group overflow-hidden"
              :class="`stagger-${i + 1}`"
            >
              <div class="relative aspect-video overflow-hidden" style="background:#ffe5bd;">
                <img v-if="dog.image" :src="dog.image" :alt="dog.metadata.dog_name" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <span class="material-symbols-outlined text-4xl text-outline-variant">pets</span>
                </div>
                <span class="badge absolute top-2 left-2" :class="dog.metadata.lost_or_found === 'found' ? 'badge-found' : 'badge-lost'">{{ dog.metadata.lost_or_found }}</span>
              </div>
              <div class="p-4">
                <h3 class="font-headline font-bold text-sm mb-0.5 text-on-surface">{{ dog.metadata.dog_name || 'Unknown' }}</h3>
                <p class="font-label text-xs text-on-surface-variant flex items-center gap-1">
                  <span class="material-symbols-outlined text-xs text-primary">location_on</span>
                  {{ dog.metadata.location || '—' }}
                </p>
              </div>
            </RouterLink>
          </div>
        </div>

        <div class="divider mb-12"></div>

        <!-- Recent community -->
        <div>
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-headline text-xl font-bold text-on-surface">Recent Community Reports</h2>
            <RouterLink to="/browse" class="btn btn-ghost btn-sm flex items-center gap-1">
              Browse all <span class="material-symbols-outlined text-sm">arrow_forward</span>
            </RouterLink>
          </div>
          <div v-if="loadingFeed" class="grid sm:grid-cols-4 gap-5">
            <div v-for="i in 4" :key="i" class="card overflow-hidden">
              <div class="aspect-square skeleton"></div>
              <div class="p-4 space-y-2">
                <div class="skeleton h-3 w-2/3"></div>
                <div class="skeleton h-2.5 w-1/2"></div>
              </div>
            </div>
          </div>
          <div v-else class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <DogCard v-for="dog in recentDogs.slice(0, 4)" :key="dog.dog_id" :dog="dog" />
          </div>
        </div>

      </main>
    </template>

    <AppFooter />
  </div>
</template>

<style scoped>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
.editorial-gradient { background: linear-gradient(135deg, #815100 0%, #f8a010 100%); }
</style>
