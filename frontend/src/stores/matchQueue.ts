/**
 * Transient store for "find matches for this dog" flow.
 * ProfileView sets a pending image; MatchesView picks it up on mount and clears it.
 */
import { ref } from "vue";

const pendingImage = ref<{
  dataUrl: string;
  filename: string;
  dogId: string;
  lostOrFound: "lost" | "found";
} | null>(null);

export function usePendingMatch() {
  function set(dataUrl: string, filename: string, dogId: string, lostOrFound: "lost" | "found") {
    pendingImage.value = { dataUrl, filename, dogId, lostOrFound };
  }

  function take() {
    const val = pendingImage.value;
    pendingImage.value = null;
    return val;
  }

  return { pendingImage, set, take };
}
