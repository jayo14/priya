<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePriyaApi } from '~/composables/usePriyaApi'

const route = useRoute()
const api = usePriyaApi()

const health = ref<{ status: string; latency_ms: number } | null>(null)
const isCollecting = ref(false)

const navLinks = [
  { name: 'Overview', to: '/', icon: 'dashboard' },
  { name: 'Deals', to: '/deals', icon: 'local_offer' },
  { name: 'Watchlist', to: '/watchlist', icon: 'bookmark' },
  { name: 'Sources', to: '/sources', icon: 'travel_explore' },
  { name: 'Settings', to: '/settings', icon: 'settings' }
]

const checkHealth = async () => {
  try {
    const res = await api.getHealth()
    health.value = {
      status: res.status,
      latency_ms: res.database?.latency_ms || 1
    }
  } catch {
    health.value = null
  }
}

const triggerDiscovery = async () => {
  if (isCollecting.value) return
  isCollecting.value = true
  try {
    await api.collectAll()
    await api.runProcessing()
    // Reload current page state if on deals or overview
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('priya-refresh'))
    }
  } catch (err) {
    console.error('Discovery error:', err)
  } finally {
    isCollecting.value = false
  }
}

onMounted(() => {
  checkHealth()
})
</script>

<template>
  <header class="sticky top-0 z-40 w-full border-b border-border/80 bg-background/80 backdrop-blur-md">
    <div class="max-w-7xl mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
      <!-- Logo -->
      <NuxtLink to="/" class="flex items-center gap-3 group">
        <div class="h-9 w-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-zinc-950 font-bold shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform">
          <MaterialIcon name="auto_awesome" :size="20" class="text-zinc-950" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="font-bold text-lg text-white tracking-tight">Priya</span>
            <span class="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Scout</span>
          </div>
          <p class="text-[11px] text-zinc-400 font-medium">AI Subscription Deal Finder</p>
        </div>
      </NuxtLink>

      <!-- Navigation Links -->
      <nav class="hidden md:flex items-center gap-1 bg-zinc-900/50 p-1 rounded-xl border border-zinc-800/80">
        <NuxtLink
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          class="flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
          :class="[
            route.path === link.to
              ? 'bg-zinc-800 text-emerald-400 font-semibold shadow-sm'
              : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
          ]"
        >
          <MaterialIcon :name="link.icon" :size="16" />
          {{ link.name }}
        </NuxtLink>
      </nav>

      <!-- Right Action Items -->
      <div class="flex items-center gap-3">
        <!-- Live System Status -->
        <div
          v-if="health"
          class="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border bg-zinc-900/60 border-zinc-800"
          :title="`PostgreSQL latency: ${health.latency_ms}ms`"
        >
          <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span class="text-zinc-300">Live</span>
          <span class="text-zinc-500 text-[10px]">({{ health.latency_ms }}ms)</span>
        </div>

        <!-- Trigger Instant Scout Button -->
        <Button
          size="sm"
          class="gap-1.5 shadow-emerald-500/10"
          :disabled="isCollecting"
          @click="triggerDiscovery"
        >
          <MaterialIcon
            name="radar"
            :size="16"
            :class="isCollecting ? 'animate-spin' : ''"
          />
          <span class="hidden sm:inline">{{ isCollecting ? 'Scouting...' : 'Scout Deals' }}</span>
        </Button>
      </div>
    </div>
  </header>
</template>
