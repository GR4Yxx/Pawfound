<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter, RouterLink } from "vue-router";
import { getDog } from "@/api";
import type { DogDetailResponse } from "@/types";
import NavBar from "@/components/NavBar.vue";
import AppFooter from "@/components/AppFooter.vue";

const route = useRoute();
const router = useRouter();

const dogId = route.query.id as string;
const reportType = (route.query.type as string) || "lost";

if (!dogId) router.replace("/report");

const dog = ref<DogDetailResponse | null>(null);
const loading = ref(true);

onMounted(async () => {
  try {
    dog.value = await getDog(dogId);
  } catch { /* silent */ }
  finally { loading.value = false; }
});
</script>

<template>
  <div style="background-color:#fff5ea; min-height:100vh;">
    <NavBar />

    <main class="pt-28 pb-20 max-w-xl mx-auto px-6">

      <!-- Success header -->
      <div class="text-center mb-10 animate-fade-up">
        <div class="w-20 h-20 editorial-gradient rounded-full flex items-center justify-center mx-auto mb-6 shadow-card-raised animate-pulse-ring">
          <span class="material-symbols-outlined text-on-primary text-4xl" style="font-variation-settings:'FILL' 1;">check_circle</span>
        </div>
        <h1 class="font-headline text-4xl font-extrabold text-on-surface mb-3">Report submitted!</h1>
        <p class="font-body text-on-surface-variant text-lg max-w-md mx-auto leading-relaxed">
          <template v-if="reportType === 'lost'">
            Your dog is now live. We'll notify you by email if a new report matches.
          </template>
          <template v-else>
            Thanks for helping! The owner will be notified if this dog matches any active lost reports.
          </template>
        </p>
      </div>

      <!-- Dog card preview -->
      <div class="card card-raised overflow-hidden mb-8 stagger-2">
        <div v-if="loading" class="aspect-video skeleton"></div>
        <template v-else-if="dog">
          <div class="relative aspect-video overflow-hidden" style="background:#ffe5bd;">
            <img v-if="dog.image" :src="dog.image" :alt="dog.metadata.dog_name" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full flex items-center justify-center">
              <span class="material-symbols-outlined text-6xl text-outline-variant">pets</span>
            </div>
            <span
              class="badge absolute top-3 left-3"
              :class="dog.metadata.lost_or_found === 'found' ? 'badge-found' : 'badge-lost'"
            >{{ dog.metadata.lost_or_found }}</span>
          </div>
          <div class="p-5">
            <h2 class="font-headline font-extrabold text-xl mb-1 text-on-surface">{{ dog.metadata.dog_name }}</h2>
            <p class="font-label text-sm text-on-surface-variant mb-0.5">{{ dog.metadata.breed }}</p>
            <p class="font-label text-xs text-on-surface-variant flex items-center gap-1">
              <span class="material-symbols-outlined text-xs text-primary">location_on</span>
              {{ dog.metadata.location }}
            </p>
          </div>
        </template>
      </div>

      <!-- Actions -->
      <div class="space-y-3 stagger-3">
        <RouterLink
          :to="`/browse?scan=${dogId}&type=${reportType}`"
          class="btn btn-primary w-full"
        >
          <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1;">manage_search</span>
          Search for matches now
        </RouterLink>
        <RouterLink to="/profile" class="btn btn-secondary w-full">
          <span class="material-symbols-outlined text-sm">person</span>
          View my reports
        </RouterLink>
        <RouterLink to="/" class="btn btn-ghost w-full text-on-surface-variant">
          Back to home
        </RouterLink>
      </div>

      <!-- What happens next -->
      <div class="card p-6 mt-10 stagger-4">
        <h3 class="font-headline font-bold text-sm mb-5 text-on-surface">What happens next</h3>
        <div class="space-y-4">
          <div
            v-for="(item, i) in [
              { icon: 'bolt', text: 'Your report is live and searchable immediately.' },
              { icon: 'notifications', text: 'You\'ll get an email if a new report closely matches your dog.' },
              { icon: 'chat', text: 'Anyone who finds a match can message you directly through the app.' },
              { icon: 'check_circle', text: 'Mark as Reunited from your profile once your dog is home.' },
            ]"
            :key="i"
            class="flex items-start gap-3"
          >
            <div class="w-7 h-7 editorial-gradient rounded-lg flex items-center justify-center shrink-0 shadow-sm mt-0.5">
              <span class="material-symbols-outlined text-on-primary text-sm" style="font-variation-settings:'FILL' 1;">{{ item.icon }}</span>
            </div>
            <p class="font-body text-sm text-on-surface-variant leading-relaxed">{{ item.text }}</p>
          </div>
        </div>
      </div>

    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
.editorial-gradient { background: linear-gradient(135deg, #815100 0%, #f8a010 100%); }
</style>
