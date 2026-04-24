<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { getInbox, getThread } from "@/api";
import { useInboxStore } from "@/stores/inbox";
import type { MessageThread, MessageItem } from "@/types";
import NavBar from "@/components/NavBar.vue";
import AppFooter from "@/components/AppFooter.vue";

const inboxStore = useInboxStore();

const threads = ref<MessageThread[]>([]);
const selectedDogId = ref<string | null>(null);
const selectedDogName = ref("");
const threadMessages = ref<MessageItem[]>([]);
const inboxLoading = ref(true);
const threadLoading = ref(false);
let pollTimer: ReturnType<typeof setInterval> | null = null;

onMounted(async () => {
  await loadInbox();
  pollTimer = setInterval(() => {
    if (selectedDogId.value) loadThread(selectedDogId.value);
  }, 30_000);
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});

async function loadInbox() {
  inboxLoading.value = true;
  try {
    const res = await getInbox();
    threads.value = res.threads;
  } catch {
    // silent
  } finally {
    inboxLoading.value = false;
  }
}

async function loadThread(dogId: string) {
  threadLoading.value = true;
  try {
    const res = await getThread(dogId);
    threadMessages.value = res.messages;
    selectedDogName.value = res.dog_name;
    const thread = threads.value.find((t) => t.dog_id === dogId);
    if (thread) thread.unread_count = 0;
    inboxStore.refresh();
  } catch {
    // silent
  } finally {
    threadLoading.value = false;
  }
}

async function selectThread(t: MessageThread) {
  selectedDogId.value = t.dog_id;
  await loadThread(t.dog_id);
}

function matchAlertText(body: string): string {
  return body.replace(/\n\nView the potential match: \/browse\/\S+/, "").trim();
}

function matchAlertLink(body: string): string | null {
  const m = body.match(/\/browse\/([^\s]+)/);
  return m ? `/browse/${m[1]}` : null;
}

function formatTime(iso: string) {
  const d = new Date(iso);
  const diffMs = Date.now() - d.getTime();
  const diffH = diffMs / 3_600_000;
  if (diffH < 1) return "Just now";
  if (diffH < 24) return `${Math.floor(diffH)}h ago`;
  const diffD = Math.floor(diffH / 24);
  if (diffD === 1) return "Yesterday";
  if (diffD < 7) return `${diffD}d ago`;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
</script>

<template>
  <div class="bg-surface text-on-surface font-body min-h-screen flex flex-col">
    <NavBar />

    <main class="flex-1 pt-24 pb-20 max-w-6xl mx-auto w-full px-6">

      <!-- Page header -->
      <div class="mb-8 animate-fade-up">
        <span class="font-label text-xs uppercase tracking-widest text-primary font-semibold mb-1 block">Your Messages</span>
        <h1 class="font-headline text-3xl font-extrabold text-on-surface">Inbox</h1>
        <p v-if="inboxStore.unreadCount > 0" class="text-sm text-on-surface-variant mt-1">
          <span class="font-semibold text-error">{{ inboxStore.unreadCount }} unread</span> message{{ inboxStore.unreadCount !== 1 ? 's' : '' }}
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-12 gap-5 animate-fade-up" style="animation-delay:0.05s; min-height: 560px;">

        <!-- Thread list -->
        <div class="md:col-span-4 card overflow-hidden flex flex-col">
          <div class="px-4 py-3.5 border-b border-surface-container">
            <p class="font-headline font-bold text-sm text-on-surface">Conversations</p>
          </div>

          <!-- Loading -->
          <div v-if="inboxLoading" class="p-4 space-y-4">
            <div v-for="i in 3" :key="i" class="flex gap-3 animate-pulse">
              <div class="w-10 h-10 rounded-full skeleton shrink-0"></div>
              <div class="flex-1 space-y-2 pt-1">
                <div class="h-3 skeleton rounded-full w-2/3"></div>
                <div class="h-3 skeleton rounded-full w-full"></div>
              </div>
            </div>
          </div>

          <!-- Empty -->
          <div v-else-if="threads.length === 0" class="flex-1 flex items-center justify-center p-8 text-center">
            <div>
              <span class="material-symbols-outlined text-4xl text-outline-variant block mb-3">inbox</span>
              <p class="font-headline font-semibold text-on-surface mb-1">No messages yet</p>
              <p class="font-body text-xs text-on-surface-variant leading-relaxed">When someone messages you about a reported dog, it'll appear here.</p>
            </div>
          </div>

          <!-- Threads -->
          <div v-else class="flex-1 overflow-y-auto divide-y divide-surface-container">
            <button
              v-for="t in threads"
              :key="t.dog_id"
              @click="selectThread(t)"
              class="w-full text-left p-4 flex items-start gap-3 transition-colors"
              :class="selectedDogId === t.dog_id
                ? 'bg-surface-container-low'
                : 'hover:bg-surface-container/50'"
            >
              <!-- Avatar -->
              <div class="w-10 h-10 rounded-full editorial-gradient flex items-center justify-center shrink-0 text-sm font-extrabold text-on-primary font-headline shadow-sm">
                {{ t.dog_name?.charAt(0)?.toUpperCase() ?? "?" }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between mb-0.5">
                  <span class="font-headline font-semibold text-sm text-on-surface truncate">{{ t.dog_name }}</span>
                  <span class="text-[0.6rem] text-on-surface-variant shrink-0 ml-2">{{ formatTime(t.latest_at) }}</span>
                </div>
                <p class="text-xs text-on-surface-variant truncate">{{ t.sender_name }}: {{ t.latest_message }}</p>
              </div>
              <span v-if="t.unread_count > 0" class="bg-error text-white text-[0.6rem] font-bold px-1.5 py-0.5 rounded-full shrink-0 ml-1">
                {{ t.unread_count }}
              </span>
            </button>
          </div>
        </div>

        <!-- Thread detail -->
        <div class="md:col-span-8 card flex flex-col overflow-hidden">

          <!-- No thread selected -->
          <div v-if="!selectedDogId" class="flex-1 flex items-center justify-center p-8 text-center">
            <div>
              <div class="w-16 h-16 editorial-gradient rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-card">
                <span class="material-symbols-outlined text-on-primary text-2xl" style="font-variation-settings:'FILL' 1;">chat</span>
              </div>
              <p class="font-headline font-semibold text-on-surface mb-1">Select a conversation</p>
              <p class="font-body text-sm text-on-surface-variant">Click a thread on the left to read messages.</p>
            </div>
          </div>

          <template v-else>
            <!-- Thread header -->
            <div class="px-5 py-4 border-b border-surface-container flex items-center gap-3 shrink-0">
              <div class="w-9 h-9 rounded-full editorial-gradient flex items-center justify-center text-sm font-extrabold text-on-primary font-headline shadow-sm shrink-0">
                {{ selectedDogName?.charAt(0)?.toUpperCase() ?? "?" }}
              </div>
              <div>
                <p class="font-headline font-bold text-sm text-on-surface">{{ selectedDogName }}</p>
                <p class="font-label text-xs text-on-surface-variant">Messages about this dog</p>
              </div>
            </div>

            <!-- Messages -->
            <div class="flex-1 overflow-y-auto p-5 space-y-3 min-h-0">
              <!-- Loading -->
              <div v-if="threadLoading" class="space-y-4">
                <div v-for="i in 3" :key="i" class="flex animate-pulse" :class="i % 2 === 0 ? 'justify-end' : ''">
                  <div class="h-14 w-52 skeleton rounded-2xl"></div>
                </div>
              </div>

              <!-- Messages -->
              <template v-else v-for="msg in threadMessages" :key="msg.message_id">

                <!-- System match alert -->
                <div v-if="msg.is_system" class="flex justify-center">
                  <div class="w-full max-w-sm bg-surface-container border border-outline-variant/30 rounded-2xl px-4 py-4 shadow-sm">
                    <div class="flex items-center gap-2 mb-2">
                      <div class="w-6 h-6 editorial-gradient rounded-lg flex items-center justify-center shrink-0">
                        <span class="material-symbols-outlined text-on-primary text-xs" style="font-variation-settings:'FILL' 1;">pets</span>
                      </div>
                      <span class="text-xs font-bold text-primary uppercase tracking-widest font-label">Pawfound AI</span>
                      <span class="ml-auto text-[0.6rem] text-on-surface-variant opacity-60">{{ formatTime(msg.created_at) }}</span>
                    </div>
                    <p class="text-sm leading-relaxed text-on-surface whitespace-pre-line">{{ matchAlertText(msg.body) }}</p>
                    <RouterLink
                      v-if="matchAlertLink(msg.body)"
                      :to="matchAlertLink(msg.body)!"
                      class="mt-3 btn btn-primary btn-sm w-full text-xs"
                    >
                      <span class="material-symbols-outlined text-xs" style="font-variation-settings:'FILL' 1;">manage_search</span>
                      View potential match
                    </RouterLink>
                  </div>
                </div>

                <!-- Regular message -->
                <div
                  v-else
                  class="flex"
                  :class="msg.is_mine ? 'justify-end' : 'justify-start'"
                >
                  <div
                    class="max-w-[72%] px-4 py-3 shadow-sm"
                    :class="msg.is_mine
                      ? 'bg-primary-container text-on-primary-container rounded-2xl rounded-br-sm'
                      : 'bg-surface-container text-on-surface rounded-2xl rounded-bl-sm'"
                  >
                    <p v-if="!msg.is_mine" class="text-[0.65rem] font-bold text-on-surface-variant mb-1 uppercase tracking-wide">{{ msg.sender_name }}</p>
                    <p class="text-sm leading-relaxed">{{ msg.body }}</p>
                    <p class="text-[0.6rem] mt-1.5 opacity-50 text-right">{{ formatTime(msg.created_at) }}</p>
                  </div>
                </div>

              </template>

              <div v-if="!threadLoading && threadMessages.length === 0" class="text-center py-10 text-on-surface-variant">
                <span class="material-symbols-outlined text-3xl block mb-2">chat_bubble_outline</span>
                <p class="text-sm">No messages in this thread yet.</p>
              </div>
            </div>
          </template>

        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
</style>
