import { ref } from "vue";
import { defineStore } from "pinia";
import { getUnreadCount } from "@/api";

export const useInboxStore = defineStore("inbox", () => {
  const unreadCount = ref(0);
  let pollTimer: ReturnType<typeof setInterval> | null = null;

  async function refresh() {
    try {
      const res = await getUnreadCount();
      unreadCount.value = res.unread;
    } catch {
      // Not logged in or network error — ignore
    }
  }

  function startPolling() {
    refresh();
    pollTimer = setInterval(refresh, 60_000);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  return { unreadCount, refresh, startPolling, stopPolling };
});
