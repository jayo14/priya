<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { DashboardStats, Promotion } from '~/lib/api'
import { usePriyaApi } from '~/composables/usePriyaApi'
import ProviderLogo from '~/components/ProviderLogo.vue'
import Card from '~/components/ui/Card.vue'
import Button from '~/components/ui/Button.vue'
import Badge from '~/components/ui/Badge.vue'
import DealCard from '~/components/DealCard.vue'
import DealDetailModal from '~/components/DealDetailModal.vue'
import MaterialIcon from '~/components/MaterialIcon.vue'

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
    <!-- Hero Banner (Theme-adaptive) -->
    <div class="relative overflow-hidden rounded-3xl border border-border bg-gradient-to-b from-card via-card/70 to-background p-6 sm:p-8 shadow-sm">
      <div class="max-w-2xl">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-semibold mb-4">
          <MaterialIcon name="bolt" :size="15" />
          <span>Continuous Subscription Scouting</span>
        </div>
        <h1 class="text-3xl sm:text-4xl font-extrabold text-foreground tracking-tight leading-tight">
          Find Free & Discounted <span class="bg-gradient-to-r from-emerald-500 to-teal-400 dark:from-emerald-400 dark:to-teal-300 bg-clip-text text-transparent">AI Subscriptions</span>
        </h1>
        <p class="mt-3 text-sm sm:text-base text-muted-foreground leading-relaxed">
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

    <!-- 4 Main KPI Cards (Strict shadcn UI & Theme-adaptive) -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Card class="p-5 bg-card border-border hover:shadow-sm transition-shadow">
        <div class="flex items-center justify-between text-muted-foreground mb-2">
          <span class="text-xs font-medium">Discovered Posts</span>
          <MaterialIcon name="travel_explore" :size="20" class="text-muted-foreground" />
        </div>
        <div class="text-2xl sm:text-3xl font-extrabold text-foreground">
          {{ stats?.total_discovered_items ?? 0 }}
        </div>
        <p class="text-[11px] text-muted-foreground mt-1">From Telegram, Reddit, RSS</p>
      </Card>

      <Card class="p-5 bg-card border-border hover:shadow-sm transition-shadow">
        <div class="flex items-center justify-between text-muted-foreground mb-2">
          <span class="text-xs font-medium">Verified Deals</span>
          <MaterialIcon name="verified" :size="20" class="text-emerald-500 dark:text-emerald-400" />
        </div>
        <div class="text-2xl sm:text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
          {{ stats?.verified_promotions ?? 0 }}
        </div>
        <p class="text-[11px] text-emerald-600/80 dark:text-emerald-500/80 mt-1">Official destination verified</p>
      </Card>

      <Card class="p-5 bg-card border-border hover:shadow-sm transition-shadow">
        <div class="flex items-center justify-between text-muted-foreground mb-2">
          <span class="text-xs font-medium">Expiring Soon</span>
          <MaterialIcon name="timer" :size="20" class="text-amber-500 dark:text-amber-400" />
        </div>
        <div class="text-2xl sm:text-3xl font-extrabold text-amber-600 dark:text-amber-400">
          {{ stats?.expiring_promotions ?? 0 }}
        </div>
        <p class="text-[11px] text-muted-foreground mt-1">Ending within 48 hours</p>
      </Card>

      <Card class="p-5 bg-card border-border hover:shadow-sm transition-shadow">
        <div class="flex items-center justify-between text-muted-foreground mb-2">
          <span class="text-xs font-medium">Nigeria Usable</span>
          <MaterialIcon name="public" :size="20" class="text-teal-500 dark:text-teal-400" />
        </div>
        <div class="text-2xl sm:text-3xl font-extrabold text-teal-600 dark:text-teal-400">
          {{ stats?.nigeria_eligible_promotions ?? 0 }}
        </div>
        <p class="text-[11px] text-muted-foreground mt-1">Cards / Virtual USD supported</p>
      </Card>
    </div>

    <!-- Tracked AI Providers Section with Official Brand Logos -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-foreground tracking-tight">Tracked AI Providers</h2>
          <p class="text-xs text-muted-foreground">Monitored subscription tiers across all major AI labs</p>
        </div>
        <NuxtLink to="/deals" class="text-xs text-primary hover:underline flex items-center gap-1 font-medium">
          View catalog
          <MaterialIcon name="arrow_forward" :size="14" />
        </NuxtLink>
      </div>

      <!-- Providers Grid using shadcn Cards with Provider Logos -->
      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <NuxtLink
          v-for="prov in stats?.providers"
          :key="prov.provider_id"
          :to="`/deals?provider=${prov.provider_id}`"
          class="group block"
        >
          <Card
            hoverable
            class="p-3.5 flex flex-col items-center justify-center text-center gap-2 h-full bg-card border-border transition-all duration-200 group-hover:border-primary/50 group-hover:shadow-md"
          >
            <!-- Platform Brand Logo Container -->
            <div class="h-10 w-10 rounded-xl bg-muted/80 flex items-center justify-center group-hover:scale-110 transition-transform duration-200 shadow-inner">
              <ProviderLogo :provider="prov.slug" :size="22" />
            </div>

            <!-- Provider Name & Deals Count -->
            <div class="w-full">
              <p class="font-semibold text-xs text-foreground group-hover:text-primary transition-colors truncate">
                {{ prov.name }}
              </p>
              <div class="flex items-center justify-center gap-1.5 mt-1 text-[11px] text-muted-foreground font-medium">
                <span class="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span>{{ prov.promotions_count }} {{ prov.promotions_count === 1 ? 'deal' : 'deals' }}</span>
              </div>
            </div>
          </Card>
        </NuxtLink>
      </div>
    </div>

    <!-- Recent Opportunities Grid -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-foreground tracking-tight">Recent Opportunities</h2>
          <p class="text-xs text-muted-foreground">Latest discovered and verified promotional offers</p>
        </div>

        <NuxtLink to="/deals">
          <Button variant="ghost" size="sm" class="gap-1 text-xs text-primary">
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

      <div v-else-if="loading" class="text-center py-12 text-muted-foreground text-sm">
        <MaterialIcon name="sync" :size="24" class="animate-spin mb-2 text-primary" />
        <p>Scouting subscription opportunities...</p>
      </div>

      <div v-else class="text-center py-12 border border-dashed border-border rounded-2xl p-8 bg-card/40">
        <MaterialIcon name="inventory_2" :size="32" class="text-muted-foreground mb-2" />
        <p class="text-sm font-semibold text-foreground">No promotions discovered yet</p>
        <p class="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
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
