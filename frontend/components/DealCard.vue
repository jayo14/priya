<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Promotion } from '~/lib/api'
import { usePriyaApi } from '~/composables/usePriyaApi'

const props = defineProps<{
  deal: Promotion
  isBookmarked?: boolean
}>()

const emit = defineEmits<{
  (e: 'select', deal: Promotion): void
  (e: 'toggleWatchlist', id: number): void
}>()

const api = usePriyaApi()
const copied = ref(false)

const copyCode = () => {
  if (!props.deal.promo_code) return
  navigator.clipboard.writeText(props.deal.promo_code)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

// Brand color heuristics
const providerColor = computed(() => {
  const p = (props.deal.provider_slug || '').toLowerCase()
  if (p.includes('anthropic') || p.includes('claude')) return 'text-amber-400 bg-amber-500/10 border-amber-500/20'
  if (p.includes('openai') || p.includes('chatgpt')) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
  if (p.includes('xai') || p.includes('grok')) return 'text-sky-400 bg-sky-500/10 border-sky-500/20'
  if (p.includes('google') || p.includes('gemini')) return 'text-blue-400 bg-blue-500/10 border-blue-500/20'
  if (p.includes('perplexity')) return 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20'
  if (p.includes('cursor')) return 'text-violet-400 bg-violet-500/10 border-violet-500/20'
  if (p.includes('github')) return 'text-purple-400 bg-purple-500/10 border-purple-500/20'
  return 'text-zinc-400 bg-zinc-800 border-zinc-700'
})

// Nigeria availability check
const isNigeriaAvailable = computed(() => {
  const upperEl = (props.deal.eligible_countries || []).map((c) => c.toUpperCase())
  const upperEx = (props.deal.excluded_countries || []).map((c) => c.toUpperCase())
  if (upperEx.includes('NG') || upperEx.includes('NIGERIA')) return false
  return upperEl.includes('NG') || upperEl.includes('GLOBAL') || upperEl.length === 0
})

const confidenceVariant = computed(() => {
  if (props.deal.status === 'verified') return 'verified'
  if (props.deal.status === 'likely_valid') return 'likely'
  if (props.deal.status === 'restricted') return 'restricted'
  if (props.deal.status === 'expired') return 'expired'
  return 'unverified'
})

const primaryLink = computed(() => {
  if (!props.deal.links || props.deal.links.length === 0) return null
  return props.deal.links.find((l) => l.is_primary) || props.deal.links[0]
})
</script>

<template>
  <Card hoverable class="p-5 flex flex-col justify-between group relative overflow-hidden bg-zinc-950/70 border-zinc-800/80 hover:border-zinc-700">
    <!-- Top Bar: Provider, Status & Watchlist Button -->
    <div>
      <div class="flex items-center justify-between gap-2 mb-3">
        <div class="flex items-center gap-2">
          <span
            class="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-md border"
            :class="providerColor"
          >
            {{ props.deal.provider_name || 'AI Provider' }}
          </span>

          <span
            v-if="props.deal.plan_name"
            class="text-xs text-zinc-300 font-medium"
          >
            {{ props.deal.plan_name }}
          </span>
        </div>

        <div class="flex items-center gap-1.5">
          <!-- Confidence Badge -->
          <Badge :variant="confidenceVariant" class="gap-1 capitalize text-[10px]">
            <MaterialIcon
              :name="props.deal.status === 'verified' ? 'verified' : props.deal.status === 'restricted' ? 'gpp_bad' : 'shield'"
              :size="12"
            />
            {{ props.deal.status.replace('_', ' ') }}
          </Badge>

          <!-- Watchlist Toggle -->
          <button
            class="p-1 rounded-md text-zinc-400 hover:text-emerald-400 hover:bg-zinc-800 transition-colors"
            :title="props.isBookmarked ? 'Remove from Watchlist' : 'Add to Watchlist'"
            @click.stop="emit('toggleWatchlist', props.deal.id)"
          >
            <MaterialIcon
              name="bookmark"
              :filled="props.isBookmarked"
              :size="18"
              :class="props.isBookmarked ? 'text-emerald-400' : 'text-zinc-500'"
            />
          </button>
        </div>
      </div>

      <!-- Title -->
      <h3
        class="text-base font-semibold text-white tracking-tight mb-2 line-clamp-2 group-hover:text-emerald-400 transition-colors cursor-pointer"
        @click="emit('select', props.deal)"
      >
        {{ props.deal.title }}
      </h3>

      <!-- Offer Highlights -->
      <div class="flex flex-wrap items-center gap-2 mb-3">
        <!-- Value Badge (Duration / Discount) -->
        <span
          v-if="props.deal.duration_days"
          class="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
        >
          <MaterialIcon name="schedule" :size="13" />
          {{ props.deal.duration_days }} Days Free
        </span>
        <span
          v-else-if="props.deal.discount_percentage"
          class="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
        >
          <MaterialIcon name="percent" :size="13" />
          {{ props.deal.discount_percentage }}% Off
        </span>

        <!-- Offer Type Pill -->
        <span class="text-xs text-zinc-400 px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 capitalize">
          {{ props.deal.offer_type.replace('_', ' ') }}
        </span>

        <!-- Nigerian Availability Pill -->
        <span
          v-if="isNigeriaAvailable"
          class="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 px-2 py-0.5 rounded bg-emerald-950/40 border border-emerald-800/40"
          title="Eligible in Nigeria (Virtual USD Card recommended for payment gateways)"
        >
          <MaterialIcon name="check_circle" :size="13" />
          Nigeria Available
        </span>
        <span
          v-else
          class="inline-flex items-center gap-1 text-[11px] font-medium text-amber-400 px-2 py-0.5 rounded bg-amber-950/40 border border-amber-800/40"
          title="Regionally restricted or excludes Nigeria"
        >
          <MaterialIcon name="warning" :size="13" />
          Region Restricted
        </span>
      </div>

      <!-- Description snippet -->
      <p v-if="props.deal.description" class="text-xs text-zinc-400 line-clamp-2 mb-4 leading-relaxed">
        {{ props.deal.description }}
      </p>
    </div>

    <!-- Bottom Actions: Promo Code, Confidence Meter & View Button -->
    <div class="pt-3 border-t border-zinc-800/80">
      <!-- Promo Code Bar if present -->
      <div
        v-if="props.deal.promo_code"
        class="flex items-center justify-between p-2 mb-3 rounded-lg bg-zinc-900/90 border border-zinc-800 text-xs font-mono"
      >
        <span class="text-emerald-400 font-bold select-all tracking-wider">{{ props.deal.promo_code }}</span>
        <button
          class="flex items-center gap-1 text-[11px] font-sans font-medium text-zinc-400 hover:text-white px-1.5 py-0.5 rounded hover:bg-zinc-800 transition-colors"
          @click.stop="copyCode"
        >
          <MaterialIcon :name="copied ? 'done' : 'content_copy'" :size="14" />
          {{ copied ? 'Copied' : 'Copy' }}
        </button>
      </div>

      <div class="flex items-center justify-between gap-3">
        <!-- Confidence Score Indicator -->
        <div class="flex items-center gap-2">
          <div class="w-12 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all"
              :class="props.deal.confidence_score >= 70 ? 'bg-emerald-500' : props.deal.confidence_score >= 50 ? 'bg-blue-500' : 'bg-amber-500'"
              :style="{ width: `${props.deal.confidence_score}%` }"
            />
          </div>
          <span class="text-[11px] text-zinc-400 font-mono">{{ props.deal.confidence_score }}%</span>
        </div>

        <!-- Buttons -->
        <div class="flex items-center gap-1.5">
          <Button
            size="sm"
            variant="secondary"
            class="text-xs h-8 px-2.5"
            @click="emit('select', props.deal)"
          >
            Details
          </Button>

          <a
            v-if="primaryLink"
            :href="primaryLink.original_url"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center justify-center gap-1 h-8 px-3 rounded-lg text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500 hover:text-zinc-950 transition-colors"
            @click.stop
          >
            <span>Claim</span>
            <MaterialIcon name="open_in_new" :size="13" />
          </a>
        </div>
      </div>
    </div>
  </Card>
</template>
