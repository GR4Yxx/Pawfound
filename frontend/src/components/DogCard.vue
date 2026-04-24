<script setup lang="ts">
import { RouterLink } from "vue-router";
import type { DogDetailResponse } from "@/types";

const props = defineProps<{
  dog: DogDetailResponse & { created_at?: string | null; similarity?: number };
  showMatch?: boolean;
}>();

function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const h = Math.floor(diff / 3_600_000);
  if (h < 1) return "Just now";
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d === 1) return "Yesterday";
  if (d < 7) return `${d}d ago`;
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
</script>

<template>
  <RouterLink :to="`/browse/${dog.dog_id}`" class="card card-hover group block overflow-hidden">
    <!-- Photo -->
    <div class="aspect-square overflow-hidden relative bg-surface-container">
      <img
        v-if="dog.image"
        :src="dog.image"
        :alt="dog.metadata.dog_name"
        class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
      />
      <div v-else class="w-full h-full flex items-center justify-center">
        <span class="material-symbols-outlined text-5xl text-outline-variant">pets</span>
      </div>

      <!-- Gradient overlay -->
      <div class="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

      <!-- Match % badge -->
      <div v-if="showMatch && dog.similarity != null" class="absolute top-2.5 left-2.5">
        <span class="badge" :class="dog.similarity >= 0.8 ? 'bg-tertiary text-on-tertiary' : 'bg-primary-container text-on-primary-container'">
          {{ Math.round(dog.similarity * 100) }}% match
        </span>
      </div>

      <!-- Lost/Found badge -->
      <div class="absolute top-2.5" :class="showMatch && dog.similarity != null ? 'right-2.5' : 'left-2.5'">
        <span class="badge" :class="dog.metadata.lost_or_found === 'found' ? 'badge-found' : 'badge-lost'">
          {{ dog.metadata.lost_or_found }}
        </span>
      </div>

      <!-- Reunited badge -->
      <div v-if="dog.status === 'reunited'" class="absolute bottom-2.5 left-2.5">
        <span class="badge badge-reunited gap-1">
          <span class="material-symbols-outlined text-xs" style="font-variation-settings:'FILL' 1;">favorite</span>
          Reunited
        </span>
      </div>
    </div>

    <!-- Info -->
    <div class="p-4">
      <div class="flex items-center justify-between mb-2">
        <span v-if="dog.created_at" class="text-[0.7rem] font-label text-on-surface-variant">{{ timeAgo(dog.created_at) }}</span>
      </div>
      <h3 class="font-headline font-bold text-base mb-0.5 text-on-surface">{{ dog.metadata.dog_name || "Unknown Dog" }}</h3>
      <p class="font-label text-xs text-on-surface-variant mb-2">{{ dog.metadata.breed }}</p>
      <div class="flex items-center gap-1 text-xs text-on-surface-variant">
        <span class="material-symbols-outlined text-sm text-primary">location_on</span>
        <span class="font-label truncate">{{ dog.metadata.location || "Unknown location" }}</span>
      </div>
    </div>
  </RouterLink>
</template>

<style scoped>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
</style>
