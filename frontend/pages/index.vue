<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { DashboardStats, Promotion, ActivityItem } from '~/lib/api'
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
const activityLogs = ref<ActivityItem[]>([])
const watchlistIds = ref<number[]>([])
const selectedDeal = ref<Promotion | null>(null)
const modalOpen = ref(false)
const loading = ref(true)
const scouting = ref(false)
const scoutMessage = ref<string | null>(null)

const loadData = async () => {
  loading.value = true
  try {
    const [statsRes, promosRes, activityRes, wlRes] = await Promise.all([
      api.getDashboardStats(),
      api.getPromotions({ limit: 6 }),
      api.getDashboardActivity(15),
      api.getWatchlist()
    ])
    stats.value = statsRes
    promotions.value = promosRes
    activityLogs.value = activityRes
    watchlistIds.value = wlRes.promotion_ids
  } catch (err) {
    console.error('Failed to load dashboard data:', err)
  } finally {
    loading.value = false
  }
}

const triggerScout = async () => {
  scouting.value = true
  scoutMessage.value = 'Connecting to real-time sources...'
  try {
    const collectRes = await api.collectAll()
    scoutMessage.value = `Scraped ${collectRes.total_items_discovered} items. Analyzing offers...`
    await api.runProcessing(50)
    scoutMessage.value = 'Completed scout run!'
    await loadData()
    setTimeout(() => {
      scoutMessage.value = null
    }, 4000)
  } catch (err: any) {
    scoutMessage.value = `Error: ${err?.message || 'Failed to complete scout run'}`
  } finally {
    scouting.value = false
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

const formatTime = (ts: string) => {
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ts
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
  <div class="space-y-8 max-w-7xl mx-auto">
    <!-- Top Action Banner -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 rounded-2xl border border-border bg-card shadow-sm">
      <div class="space-y-1">
        <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
          <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Live Scouting Engine</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
          AI Subscription Scout
        </h1>
        <p class="text-xs sm:text-sm text-muted-foreground">
          Real-time discovery across Telegram, Reddit, RSS, and web announcement portals.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <Button
          size="lg"
          class="gap-2 shadow-sm font-semibold"
          :disabled="scouting"
          @click="triggerScout"
        >
          <MaterialIcon name="refresh" :size="18" :class="{ 'animate-spin': scouting }" />
          <span>{{ scouting ? 'Scouting Now...' : 'Run Live Scout' }}</span>
        </Button>

        <NuxtLink to="/sources">
          <Button variant="outline" size="lg" class="gap-2">
            <MaterialIcon name="tune" :size="18" />
            <span>Manage Sources</span>
          </Button>
        </NuxtLink>
      </div>
    </div>

    <!-- Scout Live Status Banner if active -->
    <div v-if="scoutMessage" class="p-3.5 px-4 rounded-xl border border-primary/20 bg-primary/5 text-primary text-xs font-medium flex items-center justify-between">
      <div class="flex items-center gap-2">
        <MaterialIcon name="info" :size="16" />
        <span>{{ scoutMessage }}</span>
      </div>
      <button class="hover:underline text-[11px]" @click="scoutMessage = null">Dismiss</button>
    </div>

    <!-- 4 Key Metrics Overview -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Card class="p-5 bg-card border-border hover:border-primary/40 transition-colors">
        <div class="flex items-center justify-between text-muted-foreground mb-2">
          <span class="text-xs font-medium">Scraped Raw Posts</span>
          <MaterialIcon name="travel_explore" :size="20" class="text-muted-foreground" />
        </div>
        <div class="text-2xl sm:text-3xl font-extrabold text-foreground">
          {{ stats?.total_discovered_items ?? 0 }}
        </div>
        <p class="text-[11px] text-muted-foreground mt-1">Real items extracted from sources</p>
      </Card>

      <Card class="p-5 bg-card border-border hover:border-primary/40 transition-colors">
        <div class="flex items-center justify-between text-muted-foreground mb-2">
          <span class="text-xs font-medium">Verified Promotions</span>
          <MaterialIcon name="verified" :size="20" class="text-emerald-500 dark:text-emerald-400" />
        </div>
        <div class="text-2xl sm:text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
          {{ stats?.verified_promotions ?? 0 }}
        </div>
        <p class="text-[11px] text-emerald-600/80 dark:text-emerald-500/80 mt-1">Valid redemption URLs</p>
      </Card>

      <Card class="p-5 bg-card border-border hover:border-primary/40 transition-colors">
        <div class="flex items-center justify-between text-muted-foreground mb-2">
          <span class="text-xs font-medium">Likely Valid Deals</span>
          <MaterialIcon name="check_circle" :size="20" class="text-teal-500 dark:text-teal-400" />
        </div>
        <div class="text-2xl sm:text-3xl font-extrabold text-teal-600 dark:text-teal-400">
          {{ stats?.likely_valid_promotions ?? 0 }}
        </div>
        <p class="text-[11px] text-muted-foreground mt-1">High confidence score (≥50)</p>
      </Card>

      <Card class="p-5 bg-card border-border hover:border-primary/40 transition-colors">
        <div class="flex items-center justify-between text-muted-foreground mb-2">
          <span class="text-xs font-medium">Nigeria Card Usable</span>
          <MaterialIcon name="credit_card" :size="20" class="text-primary" />
        </div>
        <div class="text-2xl sm:text-3xl font-extrabold text-primary">
          {{ stats?.nigeria_eligible_promotions ?? 0 }}
        </div>
        <p class="text-[11px] text-muted-foreground mt-1">Tested with Nigerian debit/virtual cards</p>
      </Card>
    </div>

    <!-- Tracked AI Providers Carousel / Row -->
    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-base font-bold text-foreground tracking-tight">Monitored AI Platforms</h2>
          <p class="text-xs text-muted-foreground">7 official platforms monitored for subscription deals</p>
        </div>
        <NuxtLink to="/deals" class="text-xs text-primary hover:underline flex items-center gap-1 font-medium">
          <span>Catalog</span>
          <MaterialIcon name="arrow_forward" :size="14" />
        </NuxtLink>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <NuxtLink
          v-for="prov in stats?.providers"
          :key="prov.provider_id"
          :to="`/deals?provider=${prov.provider_id}`"
          class="group block"
        >
          <Card
            hoverable
            class="p-3.5 flex flex-col items-center justify-center text-center gap-2 h-full bg-card border-border transition-all duration-200 group-hover:border-primary/50 group-hover:shadow-sm"
          >
            <div class="h-10 w-10 rounded-xl bg-muted/80 flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
              <ProviderLogo :provider="prov.slug" :size="22" />
            </div>
            <div class="w-full">
              <p class="font-semibold text-xs text-foreground group-hover:text-primary transition-colors truncate">
                {{ prov.name }}
              </p>
              <div class="flex items-center justify-center gap-1 mt-1 text-[11px] text-muted-foreground font-medium">
                <span class="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                <span>{{ prov.promotions_count }} {{ prov.promotions_count === 1 ? 'deal' : 'deals' }}</span>
              </div>
            </div>
          </Card>
        </NuxtLink>
      </div>
    </div>

    <!-- Active Deals Section -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-foreground tracking-tight">Active Discovered Deals</h2>
          <p class="text-xs text-muted-foreground">Authentic, extracted promotions with redemption links</p>
        </div>

        <NuxtLink to="/deals">
          <Button variant="ghost" size="sm" class="gap-1 text-xs text-primary">
            <span>View All</span>
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

      <div v-else-if="loading" class="text-center py-10 text-muted-foreground text-sm">
        <MaterialIcon name="sync" :size="24" class="animate-spin mb-2 text-primary mx-auto" />
        <p>Loading real active promotions...</p>
      </div>

      <div v-else class="text-center py-10 border border-dashed border-border rounded-2xl p-6 bg-card">
        <MaterialIcon name="verified_user" :size="32" class="text-muted-foreground mb-2 mx-auto" />
        <p class="text-sm font-semibold text-foreground">No active verified promotions right now</p>
        <p class="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
          All mock data has been wiped. Click <strong>"Run Live Scout"</strong> above to scrape real-time channels or add more feeds in <NuxtLink to="/sources" class="text-primary hover:underline font-medium">Sources</NuxtLink>.
        </p>
      </div>
    </div>

    <!-- REAL-TIME DISCOVERY STREAM & ACTIVITY LOGS (Prominently Placed) -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-foreground tracking-tight flex items-center gap-2">
            <MaterialIcon name="stream" :size="20" class="text-primary" />
            <span>Discovery Stream & Scraping Logs</span>
          </h2>
          <p class="text-xs text-muted-foreground">
            Live feed of actual posts, articles, and changelogs inspected by Priya's crawler
          </p>
        </div>

        <Button variant="outline" size="sm" class="gap-1 text-xs" @click="loadData">
          <MaterialIcon name="refresh" :size="14" />
          <span>Refresh Logs</span>
        </Button>
      </div>

      <Card class="bg-card border-border overflow-hidden">
        <div v-if="activityLogs.length > 0" class="divide-y divide-border">
          <div
            v-for="item in activityLogs"
            :key="item.id"
            class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-muted/30 transition-colors"
          >
            <div class="space-y-1 max-w-3xl">
              <div class="flex flex-wrap items-center gap-2">
                <span class="font-semibold text-xs text-foreground">
                  {{ item.source_name }}
                </span>
                <Badge variant="outline" class="text-[10px] uppercase font-mono px-1.5 py-0.2">
                  {{ item.source_type }}
                </Badge>
                <Badge
                  :variant="item.processing_status === 'processed' ? 'default' : 'secondary'"
                  class="text-[10px] font-semibold"
                >
                  {{ item.processing_status }}
                </Badge>
              </div>
              <p class="text-xs text-foreground/90 font-medium line-clamp-2">
                {{ item.title || 'Untitled scraped content item' }}
              </p>
            </div>

            <div class="flex items-center gap-1 text-[11px] text-muted-foreground whitespace-nowrap self-start sm:self-center">
              <MaterialIcon name="schedule" :size="13" />
              <span>{{ formatTime(item.discovered_at) }}</span>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-10 p-6 text-muted-foreground text-xs">
          <MaterialIcon name="history" :size="28" class="text-muted-foreground mb-1 mx-auto" />
          <p class="font-medium text-foreground">No discovery logs recorded yet</p>
          <p class="mt-0.5">Click "Run Live Scout" above to trigger an extraction cycle.</p>
        </div>
      </Card>
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
