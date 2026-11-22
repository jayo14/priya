<script setup lang="ts">
import { onMounted } from 'vue'
import { useTheme } from '~/composables/useTheme'

const { initTheme } = useTheme()

onMounted(() => {
  initTheme()
})
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col text-foreground transition-colors duration-200">
    <Navbar />

    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <slot />
    </main>

    <footer class="border-t border-border/60 bg-card/60 py-6 text-center text-xs text-muted-foreground">
      <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <span class="font-semibold text-foreground">Priya</span>
          <span>·</span>
          <span>Personal AI Subscription Deal Scout</span>
        </div>
        <div class="flex items-center gap-4 text-muted-foreground">
          <span>Deterministic Verification</span>
          <span>·</span>
          <span>Zero Paid APIs</span>
          <span>·</span>
          <span>Nigeria Usability Focused</span>
        </div>
      </div>
    </footer>
  </div>
</template>
