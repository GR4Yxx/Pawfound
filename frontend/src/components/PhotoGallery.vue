<template>
  <div class="flex flex-col gap-3">
    <!-- Main image -->
    <div class="relative w-full aspect-square rounded-2xl overflow-hidden bg-surface-container-high">
      <img
        :src="images[selectedIndex]"
        :alt="primaryLabel || 'Dog photo'"
        class="w-full h-full object-cover"
      />
      <div v-if="images.length > 1" class="absolute bottom-2 right-2 bg-scrim/60 text-white text-xs px-2 py-1 rounded-full">
        {{ selectedIndex + 1 }} / {{ images.length }}
      </div>
    </div>

    <!-- Thumbnail strip -->
    <div v-if="images.length > 1" class="flex gap-2 overflow-x-auto pb-1">
      <button
        v-for="(img, idx) in images"
        :key="idx"
        @click="selectedIndex = idx"
        class="flex-shrink-0 w-16 h-16 rounded-xl overflow-hidden border-2 transition-all"
        :class="selectedIndex === idx ? 'border-primary' : 'border-transparent opacity-60 hover:opacity-100'"
      >
        <img :src="img" :alt="`Photo ${idx + 1}`" class="w-full h-full object-cover" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{
  images: string[];
  primaryLabel?: string;
}>();

const selectedIndex = ref(0);
</script>
