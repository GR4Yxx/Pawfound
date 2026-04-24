<template>
  <footer class="border-t mt-auto" style="background:#ffeed8; border-color:rgba(204,168,107,0.3);">
    <div class="max-w-7xl mx-auto px-6 md:px-10 py-10">
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <!-- Brand -->
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 editorial-gradient rounded-xl flex items-center justify-center shadow-sm">
            <span class="material-symbols-outlined text-on-primary text-base" style="font-variation-settings:'FILL' 1;">pets</span>
          </div>
          <div>
            <p class="font-headline font-extrabold text-on-surface text-sm">Pawfound</p>
            <p class="font-label text-[0.65rem] text-on-surface-variant">© 2026 · A Curated Sanctuary for Pets</p>
          </div>
        </div>

        <!-- Tagline -->
        <p class="font-label text-xs text-on-surface-variant">Helping reunite dogs with their families.</p>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
.editorial-gradient { background: linear-gradient(135deg, #815100 0%, #f8a010 100%); }
.font-headline { font-family: 'Plus Jakarta Sans', sans-serif; }
.font-label { font-family: 'Be Vietnam Pro', sans-serif; }
.text-on-surface { color: #402b00; }
.text-on-surface-variant { color: #735722; }
.text-on-primary { color: #fff0e3; }
.text-primary { color: #815100; }
</style>
