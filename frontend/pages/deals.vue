<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Promotion, Provider } from '~/lib/api'
import { usePriyaApi } from '~/composables/usePriyaApi'
import ProviderLogo from '~/components/ProviderLogo.vue'
import Card from '~/components/ui/Card.vue'
import Input from '~/components/ui/Input.vue'
import Button from '~/components/ui/Button.vue'
import Badge from '~/components/ui/Badge.vue'
import DealCard from '~/components/DealCard.vue'
import DealDetailModal from '~/components/DealDetailModal.vue'
import MaterialIcon from '~/components/MaterialIcon.vue'

const route = useRoute()
const api = usePriyaApi()

const promotions = ref<Promotion[]>([])
const providers = ref<Provider[]>([])
const watchlistIds = ref<number[]>([])
const loading = ref(true)

// Filter states
const searchQuery = ref('')
const selectedProviderId = ref<number | null>(null)
const selectedOfferType = ref<string>('all')
const nigeriaOnly = ref(false)
const minConfidence = ref<number>(0)

// Modal state
const selectedDeal = ref<Promotion | null>(null)
const modalOpen = ref(false)

const loadData = async () => {
  loading.value = true
  try {
    const [promosRes, provsRes, wlRes] = await Promise.all([
      api.getPromotions({ limit: 100 }),
      api.getProviders(),
      api.getWatchlist()
    ])
    promotions.value = promosRes
    providers.value = provsRes
    watchlistIds.value = wlRes.promotion_ids

    // If query param provider exists in route
    if (route.query.provider) {
      selectedProviderId.value = Number(route.query.provider)
    }
  } catch (err) {
    console.error('Failed to load deals:', err)
  } finally {
    loading.value = false
  }
}

// Client-side filtering for fast reactivity
const filteredDeals = computed(() => {
  return promotions.value.filter((deal) => {
    // Search query
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      const matchTitle = deal.title.toLowerCase().includes(q)
      const matchProvider = (deal.provider_name || '').toLowerCase().includes(q)
      const matchCode = (deal.promo_code || '').toLowerCase().includes(q)
      if (!matchTitle && !matchProvider && !matchCode) return false
    }

    // Provider filter
    if (selectedProviderId.value !== null && deal.provider_id !== selectedProviderId.value) {
      return false
    }

    // Offer type
    if (selectedOfferType.value !== 'all' && deal.offer_type !== selectedOfferType.value) {
      return false
    }

    // Nigeria only filter
    if (nigeriaOnly.value) {
      const upperEl = (deal.eligible_countries || []).map((c) => c.toUpperCase())
      const upperEx = (deal.excluded_countries || []).map((c) => c.toUpperCase())
      if (upperEx.includes('NG') || upperEx.includes('NIGERIA')) return false
      const isEligible = upperEl.includes('NG') || upperEl.includes('GLOBAL') || upperEl.length === 0
      if (!isEligible) return false
    }

    // Minimum confidence
    if (deal.confidence_score < minConfidence.value) {
      return false
    }

    return true
  })
})

const openDealModal = (deal: Promotion) => {
  selectedDeal.value = deal
  modalOpen.value = true
}

const toggleWatchlist = async (id: number) => {
  try {
    const res = await api.togglePromotionWatchlist(id)
    watchlistIds.value = res.promotion_ids
  } catch (err) {
    console.error('Watchlist toggle error:', err)
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
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-foreground tracking-tight flex items-center gap-2">
          <span>Subscription Deals Database</span>
          <span class="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-medium border border-emerald-500/20">
            {{ filteredDeals.length }} active
          </span>
        </h1>
        <p class="text-xs text-muted-foreground mt-1">Verified promotions, free trial links, and student discounts across top AI providers</p>
      </div>
    </div>

    <!-- Filter Bar Card (Strict shadcn Card & Theme-adaptive) -->
    <Card class="p-4 bg-card border-border space-y-4 shadow-sm">
      <!-- Search input and provider buttons -->
      <div class="grid grid-cols-1 sm:grid-cols-12 gap-3">
        <!-- Search Query Input -->
        <div class="sm:col-span-5 relative">
          <MaterialIcon
            name="search"
            :size="18"
            class="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none"
          />
          <Input
            v-model="searchQuery"
            placeholder="Search by deal title, code, or provider..."
            class="pl-9 h-10 text-xs bg-background border-border text-foreground"
          />
        </div>

        <!-- Offer Type Filter Dropdown -->
        <div class="sm:col-span-4 flex items-center">
          <select
            v-model="selectedOfferType"
            class="h-10 w-full rounded-lg border border-border bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary transition-colors"
          >
            <option value="all">All Offer Types</option>
            <option value="free_trial">Free Trial</option>
            <option value="free_subscription">Free Subscription</option>
            <option value="discount">Discount</option>
            <option value="student_offer">Student Offer</option>
            <option value="referral">Referral Program</option>
          </select>
        </div>

        <!-- Minimum Confidence Selector -->
        <div class="sm:col-span-3 flex items-center">
          <select
            v-model.number="minConfidence"
            class="h-10 w-full rounded-lg border border-border bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary transition-colors"
          >
            <option :value="0">Any Confidence</option>
            <option :value="50">Likely Valid (50%+)</option>
            <option :value="75">Verified Only (75%+)</option>
          </select>
        </div>
      </div>

      <!-- Quick Provider Selector & Nigeria Usability Toggle -->
      <div class="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border text-xs">
        <!-- Provider Filter Pills with Logos -->
        <div class="flex flex-wrap items-center gap-1.5">
          <Button
            size="sm"
            :variant="selectedProviderId === null ? 'default' : 'secondary'"
            class="h-7 text-xs px-2.5 rounded-md"
            @click="selectedProviderId = null"
          >
            All Providers
          </Button>

          <Button
            v-for="prov in providers"
            :key="prov.id"
            size="sm"
            :variant="selectedProviderId === prov.id ? 'default' : 'secondary'"
            class="h-7 text-xs px-2.5 rounded-md gap-1.5"
            @click="selectedProviderId = prov.id"
          >
            <ProviderLogo :provider="prov.slug" :size="13" />
            <span>{{ prov.name }}</span>
          </Button>
        </div>

        <!-- Nigeria Available Toggle -->
        <label class="flex items-center gap-2 cursor-pointer select-none text-foreground font-medium">
          <input
            v-model="nigeriaOnly"
            type="checkbox"
            class="rounded border-border text-primary focus:ring-primary h-4 w-4 bg-background"
          />
          <span class="text-xs">Nigeria Compatible Only</span>
        </label>
      </div>
    </Card>

    <!-- Deals Results Grid -->
    <div v-if="filteredDeals.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <DealCard
        v-for="deal in filteredDeals"
        :key="deal.id"
        :deal="deal"
        :is-bookmarked="watchlistIds.includes(deal.id)"
        @select="openDealModal"
        @toggle-watchlist="toggleWatchlist"
      />
    </div>

    <!-- Loading Skeleton -->
    <div v-else-if="loading" class="text-center py-16 text-muted-foreground text-sm">
      <MaterialIcon name="sync" :size="28" class="animate-spin mb-2 text-primary" />
      <p>Loading subscription deals...</p>
    </div>

    <!-- Empty Filter Results -->
    <div v-else class="text-center py-16 border border-dashed border-border rounded-2xl p-8 bg-card/40">
      <MaterialIcon name="filter_list_off" :size="36" class="text-muted-foreground mb-2" />
      <p class="text-sm font-semibold text-foreground">No deals match your filter criteria</p>
      <p class="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
        Try clearing your search query or selecting "All Providers" to see more results.
      </p>
      <Button
        variant="secondary"
        size="sm"
        class="mt-4"
        @click="searchQuery = ''; selectedProviderId = null; selectedOfferType = 'all'; minConfidence = 0; nigeriaOnly = false"
      >
        Reset Filters
      </Button>
    </div>

    <!-- Deal Detail Modal -->
    <DealDetailModal
      :deal="selectedDeal"
      :open="modalOpen"
      @update:open="(val) => (modalOpen = val)"
      @updated="handleDealUpdated"
    />
  </div>
</template>
