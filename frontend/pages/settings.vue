<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { UserPreferences } from '~/lib/api'
import { usePriyaApi } from '~/composables/usePriyaApi'

const api = usePriyaApi()

const preferences = ref<UserPreferences>({
  min_confidence_score: 60,
  nigeria_only_filter: false,
  telegram_notifications_enabled: true,
  polling_interval_minutes: 5,
  auto_verify_links: true,
  theme: 'dark'
})

const loading = ref(true)
const saving = ref(false)
const savedMessage = ref<string | null>(null)

const loadSettings = async () => {
  loading.value = true
  try {
    preferences.value = await api.getSettings()
  } catch (err) {
    console.error('Failed to load settings:', err)
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    preferences.value = await api.updateSettings(preferences.value)
    savedMessage.value = 'Preferences saved successfully!'
    setTimeout(() => {
      savedMessage.value = null
    }, 3000)
  } catch (err) {
    console.error('Failed to update settings:', err)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
        <MaterialIcon name="settings" :size="24" class="text-emerald-400" />
        <span>Application & Alert Preferences</span>
      </h1>
      <p class="text-xs text-zinc-400 mt-1">Configure continuous deal discovery parameters, notification criteria, and Nigerian regional filters</p>
    </div>

    <!-- Feedback Message -->
    <div
      v-if="savedMessage"
      class="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2"
    >
      <MaterialIcon name="check_circle" :size="18" class="text-emerald-400" />
      <span>{{ savedMessage }}</span>
    </div>

    <Card class="p-6 bg-zinc-950/70 border-zinc-800 space-y-6">
      <!-- Minimum Confidence Score Slider -->
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <div>
            <label class="text-sm font-semibold text-white">Alert Confidence Threshold</label>
            <p class="text-xs text-zinc-400">Only notify and surface deals scoring above this evidence threshold</p>
          </div>
          <span class="text-sm font-bold font-mono text-emerald-400">{{ preferences.min_confidence_score }}%</span>
        </div>

        <input
          v-model.number="preferences.min_confidence_score"
          type="range"
          min="0"
          max="100"
          step="5"
          class="w-full accent-emerald-500 bg-zinc-800 rounded-lg cursor-pointer"
        />
        <div class="flex justify-between text-[11px] text-zinc-500">
          <span>0% (All discoveries)</span>
          <span>50% (Likely valid)</span>
          <span>75%+ (Strictly verified)</span>
        </div>
      </div>

      <hr class="border-zinc-800/80" />

      <!-- Nigeria Filter Toggle -->
      <div class="flex items-center justify-between gap-4">
        <div>
          <label class="text-sm font-semibold text-white">Default to Nigeria-Usable Only</label>
          <p class="text-xs text-zinc-400">Filter out deals that explicitly exclude Nigeria or require unsupported domestic bank cards</p>
        </div>
        <input
          v-model="preferences.nigeria_only_filter"
          type="checkbox"
          class="h-5 w-5 rounded border-zinc-700 bg-zinc-900 text-emerald-500 focus:ring-emerald-500/20 cursor-pointer"
        />
      </div>

      <hr class="border-zinc-800/80" />

      <!-- Telegram Notifications Toggle -->
      <div class="flex items-center justify-between gap-4">
        <div>
          <label class="text-sm font-semibold text-white">Telegram Bot Alerts</label>
          <p class="text-xs text-zinc-400">Receive instant push notifications when high-confidence AI deals are verified</p>
        </div>
        <input
          v-model="preferences.telegram_notifications_enabled"
          type="checkbox"
          class="h-5 w-5 rounded border-zinc-700 bg-zinc-900 text-emerald-500 focus:ring-emerald-500/20 cursor-pointer"
        />
      </div>

      <hr class="border-zinc-800/80" />

      <!-- Polling Interval -->
      <div class="space-y-2">
        <label class="text-sm font-semibold text-white">Discovery Polling Frequency (minutes)</label>
        <p class="text-xs text-zinc-400">How frequently Priya polls configured Telegram channels and Reddit communities</p>
        <select
          v-model.number="preferences.polling_interval_minutes"
          class="h-10 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 text-xs text-zinc-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
        >
          <option :value="2">Every 2 minutes (High frequency)</option>
          <option :value="5">Every 5 minutes (Recommended)</option>
          <option :value="15">Every 15 minutes (Standard)</option>
          <option :value="30">Every 30 minutes (Low resource)</option>
        </select>
      </div>

      <!-- Action Button -->
      <div class="pt-4 flex justify-end">
        <Button
          class="gap-2 shadow-emerald-500/20"
          :disabled="saving"
          @click="saveSettings"
        >
          <MaterialIcon name="save" :size="18" :class="saving ? 'animate-spin' : ''" />
          <span>{{ saving ? 'Saving Preferences...' : 'Save Preferences' }}</span>
        </Button>
      </div>
    </Card>
  </div>
</template>
