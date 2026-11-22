<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { DashboardStats, Promotion } from '~/lib/api'
import { usePriyaApi } from '~/composables/usePriyaApi'

const api = usePriyaApi()

const stats = ref<DashboardStats | null>(null)
const promotions = ref<Promotion[]>([])
const watchlistIds = ref<number[]>([])
const selectedDeal = ref<Promotion | null>(null)
const modalOpen = ref(false)
const loading = ref(true)

const loadData = async () => {
  loading.value = true
  try {
    const [statsRes, promosRes, wlRes] = await Promise.all([
      api.getDashboardStats(),
      api.getPromotions({ limit: 6 }),
      api.getWatchlist()
    ])
    stats.value = statsRes
    promotions.value = promosRes
    watchlistIds.value = wlRes.promotion_ids
  } catch (err) {
    console.error('Failed to load dashboard data:', err)
  } finally {
    loading.value = false
  }
}

const openDealModal = (deal: Promotion) => {
  selectedDeal.value = deal
  modalOpen.value = true
}

const toggleWatchlist = async (id: number) => {
  try {
    const res = await api.togglePromotionWatchlist(id)
    watchlistIds.value = res.promotion_ids
  } catch (err) {
    console.error('Failed to toggle watchlist:', err)
  }
}

const handleDealUpdated = (updated: Promotion) => {
  const idx = promotions.value.findIndex((p) => p.id === updated.id)
  if (idx !== -1) {
    promotions.value[idx] = updated
  }
}

onMounted(() => {
  loadData()
  if (typeof window !== 'undefined') {
    window.addEventListener('priya-refresh', loadData)
  }
})
</script>

<template>
  <div class="space-y-8">
    <!-- Hero Banner -->
    <div class="relative overflow-hidden rounded-3xl border border-zinc-800 bg-gradient-to-b from-zinc-900/80 to-zinc-950 p-6 sm:p-8">
      <div class="max-w-2xl">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-4">
          <MaterialIcon name="bolt" :size="15" />
          <span>Continuous Subscription Scouting</span>
        </div>
        <h1 class="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
          Find Free & Discounted <span class="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">AI Subscriptions</span>
        </h1>
        <p class="mt-3 text-sm sm:text-base text-zinc-400 leading-relaxed">
          Priya monitors Telegram channels, Reddit discussions, and announcement feeds for Claude Pro, ChatGPT Plus, Grok, Gemini, Perplexity, and Cursor deals.
        </p>

        <div class="mt-6 flex flex-wrap items-center gap-3">
          <NuxtLink to="/deals">
            <Button size="lg" class="gap-2 shadow-emerald-500/20">
              <MaterialIcon name="search" :size="18" />
              <span>Browse All Deals</span>
            </Button>
          </NuxtLink>

          <NuxtLink to="/sources">
            <Button variant="secondary" size="lg" class="gap-2">
              <MaterialIcon name="tune" :size="18" />
              <span>Manage Sources</span>
            </Button>
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- 4 Main KPI Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Card class="p-5 bg-zinc-950/60 border-zinc-800/80">
        <div class="flex items-center justify-between text-zinc-400 mb-2">
          <span class="text-xs font-medium">Discovered Posts</span>
          <MaterialIcon name="travel_explore" :size="20" class="text-zinc-500" />
        </div>
        <div class="text-2xl sm:text-3xl font-extrabold text-white">
          {{ stats?.total_discovered_items ?? 0 }}
        </div>
        <p class="text-[11px] text-zinc-500 mt-1">From Telegram, Reddit, RSS</p>
      </Card>

      <Card class="p-5 bg-zinc-950/60 border-zinc-800/80">
        <div class="flex items-center justify-between text-zinc-400 mb-2">
          <span class="text-xs font-medium">Verified Deals</span>
          <MaterialIcon name="verified" :size="20" class="text-emerald-400" />
        </div>
        <div class="text-2xl sm:text-3xl font-extrabold text-emerald-400">
          {{ stats?.verified_promotions ?? 0 }}
        </div>
        <p class="text-[11px] text-emerald-500/80 mt-1">Official destination verified</p>
      </Card>

      <Card class="p-5 bg-zinc-950/60 border-zinc-800/80">
        <div class="flex items-center justify-between text-zinc-400 mb-2">
          <span class="text-xs font-medium">Expiring Soon</span>
          <MaterialIcon name="timer" :size="20" class="text-amber-400" />
        </div>
        <div class="text-2xl sm:text-3xl font-extrabold text-amber-400">
          {{ stats?.expiring_promotions ?? 0 }}
        </div>
        <p class="text-[11px] text-zinc-500 mt-1">Ending within 48 hours</p>
      </Card>

      <Card class="p-5 bg-zinc-950/60 border-zinc-800/80">
        <div class="flex items-center justify-between text-zinc-400 mb-2">
          <span class="text-xs font-medium">Nigeria Usable</span>
          <MaterialIcon name="public" :size="20" class="text-teal-400" />
        </div>
        <div class="text-2xl sm:text-3xl font-extrabold text-teal-400">
          {{ stats?.nigeria_eligible_promotions ?? 0 }}
        </div>
        <p class="text-[11px] text-zinc-500 mt-1">Cards / Virtual USD supported</p>
      </Card>
    </div>

    <!-- Supported AI Providers Section -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-white tracking-tight">Tracked AI Providers</h2>
          <p class="text-xs text-zinc-400">Monitored subscription tiers across all major AI labs</p>
        </div>
        <NuxtLink to="/deals" class="text-xs text-emerald-400 hover:underline flex items-center gap-1 font-medium">
          View catalog
          <MaterialIcon name="arrow_forward" :size="14" />
        </NuxtLink>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <NuxtLink
          v-for="prov in stats?.providers"
          :key="prov.provider_id"
          :to="`/deals?provider=${prov.provider_id}`"
          class="p-3 rounded-xl border border-zinc-800/80 bg-zinc-950/50 hover:bg-zinc-900 hover:border-zinc-700 transition-all text-center group cursor-pointer"
        >
          <p class="font-semibold text-xs text-white group-hover:text-emerald-400 transition-colors truncate">
            {{ prov.name }}
          </p>
          <div class="flex items-center justify-center gap-1.5 mt-1.5 text-[11px] text-zinc-400 font-medium">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            <span>{{ prov.promotions_count }} deals</span>
          </div>
        </NuxtLink>
      </div>
    </div>

    <!-- Recent Opportunities Grid -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-white tracking-tight">Recent Opportunities</h2>
          <p class="text-xs text-zinc-400">Latest discovered and verified promotional offers</p>
        </div>

        <NuxtLink to="/deals">
          <Button variant="ghost" size="sm" class="gap-1 text-xs text-emerald-400">
            <span>Explore All Deals</span>
            <MaterialIcon name="arrow_forward" :size="14" />
          </Button>
        </NuxtLink>
      </div>

      <div v-if="promotions.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <DealCard
          v-for="deal in promotions"
          :key="deal.id"
          :deal="deal"
          :is-bookmarked="watchlistIds.includes(deal.id)"
          @select="openDealModal"
          @toggle-watchlist="toggleWatchlist"
        />
      </div>

      <div v-else-if="loading" class="text-center py-12 text-zinc-500 text-sm">
        <MaterialIcon name="sync" :size="24" class="animate-spin mb-2" />
        <p>Scouting subscription opportunities...</p>
      </div>

      <div v-else class="text-center py-12 border border-dashed border-zinc-800 rounded-2xl p-8">
        <MaterialIcon name="inventory_2" :size="32" class="text-zinc-600 mb-2" />
        <p class="text-sm font-semibold text-zinc-300">No promotions discovered yet</p>
        <p class="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
          Click "Scout Deals" above to trigger multi-source discovery across configured Telegram and Reddit sources.
        </p>
      </div>
    </div>

    <!-- Modal for Deal Details -->
    <DealDetailModal
      :deal="selectedDeal"
      :open="modalOpen"
      @update:open="(val) => (modalOpen = val)"
      @updated="handleDealUpdated"
    />
  </div>
</template>
