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
const testingBot = ref(false)
const testResult = ref<{ success: boolean; detail: string } | null>(null)
const recentNotifications = ref<any[]>([])

const loadSettings = async () => {
  loading.value = true
  try {
    const [prefsRes, notifsRes] = await Promise.all([
      api.getSettings(),
      api.getNotifications(5)
    ])
    preferences.value = prefsRes
    recentNotifications.value = notifsRes
  } catch (err) {
    console.error('Failed to load settings:', err)
  } finally {
    loading.value = false
  }
}

const sendTestAlert = async () => {
  testingBot.value = true
  testResult.value = null
  try {
    const res = await api.sendTestNotification()
    testResult.value = { success: res.success, detail: res.detail }
    recentNotifications.value = await api.getNotifications(5)
  } catch (err: any) {
    testResult.value = { success: false, detail: err.message || 'Error communicating with server' }
  } finally {
    testingBot.value = false
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

    <!-- Telegram Bot Live Test Card -->
    <Card class="p-6 bg-zinc-950/70 border-zinc-800 space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <MaterialIcon name="send" :size="18" class="text-sky-400" />
            <span>Telegram Channel Integration</span>
          </h2>
          <p class="text-xs text-zinc-400 mt-0.5">Test real-time alert delivery to your configured Telegram subscriber chat</p>
        </div>

        <Button
          size="sm"
          variant="secondary"
          class="gap-1.5 text-xs"
          :disabled="testingBot"
          @click="sendTestAlert"
        >
          <MaterialIcon name="bolt" :size="15" :class="testingBot ? 'animate-spin' : 'text-amber-400'" />
          <span>{{ testingBot ? 'Sending...' : 'Send Test Alert' }}</span>
        </Button>
      </div>

      <!-- Test Status Response -->
      <div
        v-if="testResult"
        class="p-3 rounded-lg text-xs flex items-center gap-2"
        :class="testResult.success ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-500/30' : 'bg-amber-950/40 text-amber-300 border border-amber-500/30'"
      >
        <MaterialIcon :name="testResult.success ? 'check_circle' : 'info'" :size="16" />
        <span>{{ testResult.detail }}</span>
      </div>

      <!-- Recent Notifications Log -->
      <div v-if="recentNotifications.length > 0" class="space-y-2 pt-2">
        <p class="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">Recent Dispatched Alerts</p>
        <div class="space-y-1.5">
          <div
            v-for="notif in recentNotifications"
            :key="notif.id"
            class="flex items-center justify-between p-2.5 rounded-lg bg-zinc-900/60 border border-zinc-800/80 text-xs"
          >
            <div class="flex items-center gap-2">
              <span
                class="h-2 w-2 rounded-full"
                :class="notif.status === 'sent' ? 'bg-emerald-500' : notif.status === 'pending' ? 'bg-amber-500' : 'bg-red-500'"
              />
              <span class="font-medium text-zinc-200 capitalize">{{ notif.notification_type.replace('_', ' ') }}</span>
              <span class="text-zinc-500">via {{ notif.channel }}</span>
            </div>
            <span class="text-[10px] text-zinc-500 font-mono">
              {{ new Date(notif.created_at).toLocaleTimeString() }}
            </span>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>
