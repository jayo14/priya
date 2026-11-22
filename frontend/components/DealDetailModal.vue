<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { Promotion, PromotionEligibility, VerificationCheck } from '~/lib/api'
import { usePriyaApi } from '~/composables/usePriyaApi'

const props = defineProps<{
  deal: Promotion | null
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'updated', deal: Promotion): void
}>()

const api = usePriyaApi()

const eligibility = ref<PromotionEligibility | null>(null)
const checks = ref<VerificationCheck[]>([])
const loading = ref(false)
const verifying = ref(false)
const copied = ref(false)

const copyCode = (code: string) => {
  navigator.clipboard.writeText(code)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

const loadDetails = async (id: number) => {
  loading.value = true
  try {
    const [eligRes, checksRes] = await Promise.all([
      api.getPromotionEligibility(id),
      api.getPromotionChecks(id)
    ])
    eligibility.value = eligRes
    checks.value = checksRes
  } catch (err) {
    console.error('Failed to load deal details:', err)
  } finally {
    loading.value = false
  }
}

const runLiveVerification = async () => {
  if (!props.deal || verifying.value) return
  verifying.value = true
  try {
    const res = await api.verifyPromotion(props.deal.id, false)
    // Update local checks
    checks.value = res.verification_checks
    // Emit updated promotion state
    emit('updated', {
      ...props.deal,
      confidence_score: res.confidence_score,
      status: res.status as any
    })
  } catch (err) {
    console.error('Verification error:', err)
  } finally {
    verifying.value = false
  }
}

watch(
  () => props.deal,
  (deal) => {
    if (deal && props.open) {
      loadDetails(deal.id)
    }
  },
  { immediate: true }
)

const primaryLink = computed(() => {
  if (!props.deal?.links || props.deal.links.length === 0) return null
  return props.deal.links.find((l) => l.is_primary) || props.deal.links[0]
})
</script>

<template>
  <Dialog
    :open="props.open"
    @update:open="(val) => emit('update:open', val)"
  >
    <template #title>
      <div v-if="props.deal" class="flex items-center gap-2">
        <span class="text-emerald-400 font-bold">{{ props.deal.provider_name }}</span>
        <span class="text-zinc-600">/</span>
        <span class="text-zinc-300 font-medium">{{ props.deal.plan_name || 'Offer Details' }}</span>
      </div>
    </template>

    <div v-if="props.deal" class="space-y-6">
      <!-- Top Title and Badges -->
      <div>
        <h3 class="text-lg font-bold text-white mb-2 leading-snug">
          {{ props.deal.title }}
        </h3>

        <div class="flex flex-wrap items-center gap-2">
          <Badge :variant="props.deal.status === 'verified' ? 'verified' : props.deal.status === 'restricted' ? 'restricted' : 'likely'">
            <MaterialIcon name="verified_user" :size="13" class="mr-1" />
            {{ props.deal.status.toUpperCase() }}
          </Badge>

          <span class="text-xs text-zinc-400 font-mono px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800">
            Score: <strong class="text-emerald-400">{{ props.deal.confidence_score }}/100</strong>
          </span>

          <span v-if="props.deal.duration_days" class="text-xs text-emerald-300 px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/40 font-medium">
            {{ props.deal.duration_days }} Days Free
          </span>

          <span v-else-if="props.deal.discount_percentage" class="text-xs text-emerald-300 px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/40 font-medium">
            {{ props.deal.discount_percentage }}% Discount
          </span>
        </div>
      </div>

      <!-- Description -->
      <div v-if="props.deal.description" class="p-3.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80 text-xs text-zinc-300 leading-relaxed">
        {{ props.deal.description }}
      </div>

      <!-- Promo Code Banner -->
      <div v-if="props.deal.promo_code" class="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/20 flex items-center justify-between">
        <div>
          <p class="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Promotional Code</p>
          <p class="text-lg font-mono font-bold text-white tracking-widest mt-0.5">{{ props.deal.promo_code }}</p>
        </div>
        <Button size="sm" class="gap-1.5" @click="copyCode(props.deal.promo_code)">
          <MaterialIcon :name="copied ? 'check' : 'content_copy'" :size="16" />
          {{ copied ? 'Copied' : 'Copy Code' }}
        </Button>
      </div>

      <!-- Nigerian Usability & Banking Feasibility Section -->
      <div class="rounded-xl border border-zinc-800 p-4 bg-zinc-900/40 space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <MaterialIcon name="public" :size="18" class="text-emerald-400" />
            <h4 class="text-xs font-bold text-white uppercase tracking-wider">Nigerian Regional & Banking Assessment</h4>
          </div>

          <span
            v-if="eligibility"
            class="text-[11px] font-semibold px-2 py-0.5 rounded border"
            :class="eligibility.is_nigeria_eligible ? 'bg-emerald-950/60 text-emerald-400 border-emerald-500/30' : 'bg-amber-950/60 text-amber-400 border-amber-500/30'"
          >
            {{ eligibility.status.toUpperCase() }}
          </span>
        </div>

        <div v-if="eligibility" class="space-y-2 text-xs">
          <!-- Banking / Virtual Card Guidance -->
          <div class="p-3 rounded-lg bg-zinc-950/80 border border-zinc-800 text-zinc-300 flex items-start gap-2.5">
            <MaterialIcon name="credit_card" :size="18" class="text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <p class="font-semibold text-white mb-0.5">Payment Feasibility</p>
              <p class="text-zinc-400 leading-relaxed">{{ eligibility.payment_card_guidance }}</p>
            </div>
          </div>

          <!-- Rules list -->
          <div v-if="eligibility.rules.length > 0" class="space-y-1.5 pt-1">
            <p class="text-[11px] font-medium text-zinc-400">Eligibility Conditions:</p>
            <div
              v-for="rule in eligibility.rules"
              :key="rule.id"
              class="flex items-center gap-2 text-[11px] text-zinc-300 p-2 rounded bg-zinc-900/80 border border-zinc-800/80"
            >
              <MaterialIcon name="info" :size="14" class="text-zinc-400 shrink-0" />
              <span>{{ rule.description }}</span>
            </div>
          </div>
        </div>

        <div v-else class="text-xs text-zinc-500 italic py-2">
          Evaluating regional restrictions...
        </div>
      </div>

      <!-- Verification Audit Trail Section -->
      <div class="rounded-xl border border-zinc-800 p-4 bg-zinc-900/40 space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <MaterialIcon name="fact_check" :size="18" class="text-emerald-400" />
            <h4 class="text-xs font-bold text-white uppercase tracking-wider">Verification Audit Trail</h4>
          </div>

          <Button
            size="sm"
            variant="ghost"
            class="h-7 text-[11px] gap-1 text-zinc-400 hover:text-white"
            :disabled="verifying"
            @click="runLiveVerification"
          >
            <MaterialIcon name="refresh" :size="14" :class="verifying ? 'animate-spin' : ''" />
            {{ verifying ? 'Checking...' : 'Re-verify' }}
          </Button>
        </div>

        <div v-if="checks.length > 0" class="space-y-2">
          <div
            v-for="check in checks"
            :key="check.id"
            class="flex items-center justify-between p-2.5 rounded-lg bg-zinc-950/80 border border-zinc-800 text-xs"
          >
            <div class="flex items-center gap-2.5">
              <span
                class="h-2 w-2 rounded-full"
                :class="check.result === 'pass' ? 'bg-emerald-500' : check.result === 'warning' ? 'bg-amber-500' : 'bg-red-500'"
              />
              <div>
                <p class="font-medium text-zinc-200 capitalize">{{ check.check_type.replace('_', ' ') }}</p>
                <p class="text-[11px] text-zinc-400">
                  {{ check.details?.final_domain || check.details?.summary_notes || check.details?.explanation || 'Check completed successfully' }}
                </p>
              </div>
            </div>

            <span class="text-[10px] text-zinc-500 font-mono">
              {{ new Date(check.checked_at).toLocaleDateString() }}
            </span>
          </div>
        </div>

        <div v-else class="text-xs text-zinc-500 italic py-2">
          No verification checks on record.
        </div>
      </div>

      <!-- Bottom Action: Claim Offer Link -->
      <div class="pt-4 border-t border-zinc-800 flex items-center justify-between gap-3">
        <div class="text-[11px] text-zinc-500">
          Discovered in {{ props.deal.discoveries_count }} independent source(s).
        </div>

        <div class="flex items-center gap-2">
          <Button variant="secondary" size="sm" @click="emit('update:open', false)">
            Close
          </Button>

          <a
            v-if="primaryLink"
            :href="primaryLink.original_url"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-2 h-9 px-4 rounded-lg text-sm font-semibold bg-emerald-500 text-zinc-950 hover:bg-emerald-400 transition-colors shadow-lg shadow-emerald-500/20"
          >
            <span>Open Redemption Page</span>
            <MaterialIcon name="launch" :size="16" />
          </a>
        </div>
      </div>
    </div>
  </Dialog>
</template>
