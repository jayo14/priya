<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Promotion, Provider, WatchlistSummary } from '~/lib/api'
import { usePriyaApi } from '~/composables/usePriyaApi'
import ProviderLogo from '~/components/ProviderLogo.vue'
import Card from '~/components/ui/Card.vue'
import Button from '~/components/ui/Button.vue'
import DealCard from '~/components/DealCard.vue'
import DealDetailModal from '~/components/DealDetailModal.vue'
import MaterialIcon from '~/components/MaterialIcon.vue'

const api = usePriyaApi()

const bookmarkedDeals = ref<Promotion[]>([])
const providers = ref<Provider[]>([])
const watchlistSummary = ref<WatchlistSummary | null>(null)
const loading = ref(true)

const selectedDeal = ref<Promotion | null>(null)
const modalOpen = ref(false)

const loadData = async () => {
  loading.value = true
  try {
    const [itemsRes, provsRes, summaryRes] = await Promise.all([
      api.getWatchlistItems(),
      api.getProviders(),
      api.getWatchlist()
    ])
    bookmarkedDeals.value = itemsRes
    providers.value = provsRes
    watchlistSummary.value = summaryRes
  } catch (err) {
    console.error('Failed to load watchlist:', err)
  } finally {
    loading.value = false
  }
}

const toggleWatchlist = async (id: number) => {
  try {
    await api.togglePromotionWatchlist(id)
    bookmarkedDeals.value = bookmarkedDeals.value.filter((d) => d.id !== id)
  } catch (err) {
    console.error('Error removing bookmark:', err)
  }
}

const toggleWatchProvider = async (providerId: number) => {
  try {
    const res = await api.toggleProviderWatchlist(providerId)
    if (watchlistSummary.value) {
      watchlistSummary.value.provider_ids = res.provider_ids
    }
  } catch (err) {
    console.error('Error toggling provider watch:', err)
  }
}

const openDealModal = (deal: Promotion) => {
  selectedDeal.value = deal
  modalOpen.value = true
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="space-y-8">
    <div>
      <h1 class="text-2xl font-bold text-foreground tracking-tight flex items-center gap-2">
        <MaterialIcon name="bookmark" :size="24" class="text-primary" />
        <span>Your Watchlist & Saved Deals</span>
      </h1>
      <p class="text-xs text-muted-foreground mt-1">Keep track of priority AI providers and bookmarked subscription promotions</p>
    </div>

    <!-- Watched AI Providers Section (Strict shadcn Card & Theme-adaptive) -->
    <div class="space-y-3">
      <h2 class="text-xs font-bold text-foreground uppercase tracking-wider">Watched Providers</h2>
      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <Card
          v-for="prov in providers"
          :key="prov.id"
          class="p-3.5 flex flex-col justify-between transition-all bg-card border-border"
          :class="watchlistSummary?.provider_ids.includes(prov.id) ? 'border-primary/50 shadow-sm' : ''"
        >
          <div class="flex items-center gap-2 mb-2">
            <div class="h-7 w-7 rounded-lg bg-muted/80 flex items-center justify-center shrink-0">
              <ProviderLogo :provider="prov.slug" :size="16" />
            </div>
            <div class="overflow-hidden">
              <p class="font-semibold text-xs text-foreground truncate">{{ prov.name }}</p>
              <p class="text-[10px] text-muted-foreground">{{ prov.promotions_count }} active</p>
            </div>
          </div>

          <Button
            size="sm"
            :variant="watchlistSummary?.provider_ids.includes(prov.id) ? 'default' : 'secondary'"
            class="mt-2 h-7 text-[11px] font-medium w-full gap-1"
            @click="toggleWatchProvider(prov.id)"
          >
            <MaterialIcon
              :name="watchlistSummary?.provider_ids.includes(prov.id) ? 'visibility' : 'visibility_off'"
              :size="13"
            />
            <span>{{ watchlistSummary?.provider_ids.includes(prov.id) ? 'Watching' : 'Watch' }}</span>
          </Button>
        </Card>
      </div>
    </div>

    <!-- Bookmarked Deals Grid -->
    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <h2 class="text-xs font-bold text-foreground uppercase tracking-wider">
          Bookmarked Promotions ({{ bookmarkedDeals.length }})
        </h2>
      </div>

      <div v-if="bookmarkedDeals.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <DealCard
          v-for="deal in bookmarkedDeals"
          :key="deal.id"
          :deal="deal"
          :is-bookmarked="true"
          @select="openDealModal"
          @toggle-watchlist="toggleWatchlist"
        />
      </div>

      <div v-else-if="!loading" class="text-center py-16 border border-dashed border-border rounded-2xl p-8 bg-card/40">
        <MaterialIcon name="bookmark_border" :size="36" class="text-muted-foreground mb-2" />
        <p class="text-sm font-semibold text-foreground">Your watchlist is currently empty</p>
        <p class="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
          Click the bookmark icon on any promotional deal card in the Deals directory to save it here for quick access.
        </p>
        <NuxtLink to="/deals">
          <Button variant="secondary" size="sm" class="mt-4">
            Discover Deals
          </Button>
        </NuxtLink>
      </div>
    </div>

    <!-- Deal Detail Modal -->
    <DealDetailModal
      :deal="selectedDeal"
      :open="modalOpen"
      @update:open="(val) => (modalOpen = val)"
    />
  </div>
</template>
