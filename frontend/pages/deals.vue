<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { Promotion, Provider } from '~/lib/api'
import { usePriyaApi } from '~/composables/usePriyaApi'

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
        <h1 class="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <span>Subscription Deals Database</span>
          <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-medium">
            {{ filteredDeals.length }} active
          </span>
        </h1>
        <p class="text-xs text-zinc-400 mt-1">Verified promotions, free trial links, and student discounts across top AI providers</p>
      </div>
    </div>

    <!-- Filter Bar Card -->
    <Card class="p-4 bg-zinc-950/80 border-zinc-800 space-y-4">
      <!-- Search input and provider buttons -->
      <div class="grid grid-cols-1 sm:grid-cols-12 gap-3">
        <!-- Search Query Input -->
        <div class="sm:col-span-5 relative">
          <MaterialIcon
            name="search"
            :size="18"
            class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none"
          />
          <Input
            v-model="searchQuery"
            placeholder="Search by deal title, code, or provider..."
            class="pl-9 h-10 text-xs"
          />
        </div>

        <!-- Offer Type Filter Dropdown -->
        <div class="sm:col-span-4 flex items-center">
          <select
            v-model="selectedOfferType"
            class="h-10 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 text-xs text-zinc-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
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
            class="h-10 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 text-xs text-zinc-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option :value="0">Any Confidence</option>
            <option :value="50">Likely Valid (50%+)</option>
            <option :value="75">Verified Only (75%+)</option>
          </select>
        </div>
      </div>

      <!-- Quick Provider Selector & Nigeria Usability Toggle -->
      <div class="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-zinc-800/80 text-xs">
        <!-- Provider Filter Pills -->
        <div class="flex flex-wrap items-center gap-1.5">
          <button
            class="px-2.5 py-1 rounded-md text-xs font-medium transition-colors"
            :class="selectedProviderId === null ? 'bg-emerald-500 text-zinc-950 font-semibold' : 'bg-zinc-900 text-zinc-400 hover:text-white'"
            @click="selectedProviderId = null"
          >
            All Providers
          </button>

          <button
            v-for="prov in providers"
            :key="prov.id"
            class="px-2.5 py-1 rounded-md text-xs font-medium transition-colors"
            :class="selectedProviderId === prov.id ? 'bg-emerald-500 text-zinc-950 font-semibold' : 'bg-zinc-900 text-zinc-400 hover:text-white'"
            @click="selectedProviderId = prov.id"
          >
            {{ prov.name }}
          </button>
        </div>

        <!-- Nigeria Available Toggle -->
        <label class="flex items-center gap-2 cursor-pointer select-none">
          <input
            v-model="nigeriaOnly"
            type="checkbox"
            class="h-4 w-4 rounded border-zinc-700 bg-zinc-900 text-emerald-500 focus:ring-emerald-500/20"
          />
          <span class="text-zinc-300 font-medium">Nigeria Usable Only</span>
        </label>
      </div>
    </Card>

    <!-- Deals Grid -->
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

    <!-- Empty State -->
    <div v-else-if="!loading" class="text-center py-16 border border-dashed border-zinc-800 rounded-2xl p-8">
      <MaterialIcon name="filter_alt_off" :size="36" class="text-zinc-600 mb-2" />
      <p class="text-sm font-semibold text-zinc-300">No promotions match your current filters</p>
      <p class="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
        Try resetting your provider filter, widening the confidence score, or unchecking the Nigeria restriction.
      </p>
      <Button
        variant="secondary"
        size="sm"
        class="mt-4"
        @click="
          searchQuery = '';
          selectedProviderId = null;
          selectedOfferType = 'all';
          nigeriaOnly = false;
          minConfidence = 0;
        "
      >
        Reset Filters
      </Button>
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
