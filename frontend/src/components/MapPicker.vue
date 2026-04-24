<template>
  <div class="flex flex-col gap-2">
    <div
      ref="mapContainer"
      class="w-full h-48 rounded-xl overflow-hidden border border-outline-variant z-0"
    ></div>
    <div class="flex items-center justify-between text-xs text-on-surface-variant">
      <span v-if="modelValue">
        {{ modelValue.lat.toFixed(5) }}, {{ modelValue.lng.toFixed(5) }}
      </span>
      <span v-else class="italic">Click the map to pin a location</span>
      <button
        v-if="modelValue"
        type="button"
        @click="clearPin"
        class="text-error underline"
      >
        Clear pin
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from "vue";

const props = defineProps<{
  modelValue: { lat: number; lng: number } | null;
}>();
const emit = defineEmits<{
  (e: "update:modelValue", v: { lat: number; lng: number } | null): void;
}>();

const mapContainer = ref<HTMLElement | null>(null);
let mapInstance: any = null;
let markerInstance: any = null;

onMounted(async () => {
  const L = (await import("leaflet")).default;

  // Fix default icon paths broken by bundlers
  delete (L.Icon.Default.prototype as any)._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  });

  mapInstance = L.map(mapContainer.value!, { zoomControl: true }).setView(
    [39.5, -98.35],
    4,
  );

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
    maxZoom: 18,
  }).addTo(mapInstance);

  if (props.modelValue) {
    markerInstance = L.marker([props.modelValue.lat, props.modelValue.lng]).addTo(mapInstance);
    mapInstance.setView([props.modelValue.lat, props.modelValue.lng], 12);
  }

  mapInstance.on("click", (e: any) => {
    const { lat, lng } = e.latlng;
    if (markerInstance) {
      markerInstance.setLatLng([lat, lng]);
    } else {
      markerInstance = L.marker([lat, lng]).addTo(mapInstance);
    }
    emit("update:modelValue", { lat, lng });
  });
});

onUnmounted(() => {
  mapInstance?.remove();
});

function clearPin() {
  if (markerInstance && mapInstance) {
    mapInstance.removeLayer(markerInstance);
    markerInstance = null;
  }
  emit("update:modelValue", null);
}

watch(
  () => props.modelValue,
  async (val) => {
    if (!mapInstance) return;
    const L = (await import("leaflet")).default;
    if (val) {
      if (markerInstance) {
        markerInstance.setLatLng([val.lat, val.lng]);
      } else {
        markerInstance = L.marker([val.lat, val.lng]).addTo(mapInstance);
      }
    } else {
      if (markerInstance) {
        mapInstance.removeLayer(markerInstance);
        markerInstance = null;
      }
    }
  },
);
</script>
