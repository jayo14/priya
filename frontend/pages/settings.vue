<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { UserPreferences } from '~/lib/api'
import { usePriyaApi } from '~/composables/usePriyaApi'
import { useTheme } from '~/composables/useTheme'
import Card from '~/components/ui/Card.vue'
import Button from '~/components/ui/Button.vue'
import MaterialIcon from '~/components/MaterialIcon.vue'

const api = usePriyaApi()
const { theme, setTheme } = useTheme()

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

const handleThemeChange = (newTheme: 'light' | 'dark') => {
  preferences.value.theme = newTheme
  setTheme(newTheme)
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
      <h1 class="text-2xl font-bold text-foreground tracking-tight flex items-center gap-2">
        <MaterialIcon name="settings" :size="24" class="text-primary" />
        <span>Application & Alert Preferences</span>
      </h1>
      <p class="text-xs text-muted-foreground mt-1">Configure continuous deal discovery parameters, notification criteria, and Nigerian regional filters</p>
    </div>

    <!-- Feedback Message -->
    <div
      v-if="savedMessage"
      class="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-600 dark:text-emerald-300 flex items-center gap-2"
    >
      <MaterialIcon name="check_circle" :size="18" class="text-primary" />
      <span>{{ savedMessage }}</span>
    </div>

    <Card class="p-6 bg-card border-border space-y-6 shadow-sm">
      <!-- Theme Appearance Selector -->
      <div class="space-y-2">
        <label class="text-sm font-semibold text-foreground">Dashboard Appearance Theme</label>
        <p class="text-xs text-muted-foreground">Select between Light and Dark theme modes</p>
        <div class="grid grid-cols-2 gap-3 pt-1">
          <Button
            size="sm"
            :variant="theme === 'light' ? 'default' : 'secondary'"
            class="h-9 text-xs gap-2"
            @click="handleThemeChange('light')"
          >
            <MaterialIcon name="light_mode" :size="16" />
            <span>Light Theme</span>
          </Button>

          <Button
            size="sm"
            :variant="theme === 'dark' ? 'default' : 'secondary'"
            class="h-9 text-xs gap-2"
            @click="handleThemeChange('dark')"
          >
            <MaterialIcon name="dark_mode" :size="16" />
            <span>Dark Theme</span>
          </Button>
        </div>
      </div>

      <hr class="border-border" />

      <!-- Minimum Confidence Score Slider -->
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <div>
            <label class="text-sm font-semibold text-foreground">Alert Confidence Threshold</label>
            <p class="text-xs text-muted-foreground">Only notify and surface deals scoring above this evidence threshold</p>
          </div>
          <span class="text-sm font-bold font-mono text-primary">{{ preferences.min_confidence_score }}%</span>
        </div>

        <input
          v-model.number="preferences.min_confidence_score"
          type="range"
          min="0"
          max="100"
          step="5"
          class="w-full accent-emerald-500 bg-muted rounded-lg cursor-pointer h-2"
        />
        <div class="flex justify-between text-[11px] text-muted-foreground">
          <span>0% (All discoveries)</span>
          <span>50% (Likely valid)</span>
          <span>75%+ (Strictly verified)</span>
        </div>
      </div>

      <hr class="border-border" />

      <!-- Nigeria Filter Toggle -->
      <div class="flex items-center justify-between gap-4">
        <div>
          <label class="text-sm font-semibold text-foreground">Default to Nigeria-Usable Only</label>
          <p class="text-xs text-muted-foreground">Filter out deals that explicitly exclude Nigeria or require unsupported domestic bank cards</p>
        </div>
        <input
          v-model="preferences.nigeria_only_filter"
          type="checkbox"
          class="h-5 w-5 rounded border-border bg-background text-primary focus:ring-primary cursor-pointer"
        />
      </div>

      <hr class="border-border" />

      <!-- Telegram Notifications Toggle -->
      <div class="flex items-center justify-between gap-4">
        <div>
          <label class="text-sm font-semibold text-foreground">Telegram Bot Alerts</label>
          <p class="text-xs text-muted-foreground">Receive instant push notifications when high-confidence AI deals are verified</p>
        </div>
        <input
          v-model="preferences.telegram_notifications_enabled"
          type="checkbox"
          class="h-5 w-5 rounded border-border bg-background text-primary focus:ring-primary cursor-pointer"
        />
      </div>

      <hr class="border-border" />

      <!-- Polling Interval -->
      <div class="space-y-2">
        <label class="text-sm font-semibold text-foreground">Discovery Polling Frequency (minutes)</label>
        <p class="text-xs text-muted-foreground">How frequently Priya polls configured Telegram channels and Reddit communities</p>
        <select
          v-model.number="preferences.polling_interval_minutes"
          class="h-10 w-full rounded-lg border border-border bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary transition-colors"
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

    <!-- Telegram Bot Live Test Card (Strict shadcn Card & Theme-adaptive) -->
    <Card class="p-6 bg-card border-border space-y-4 shadow-sm">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-sm font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
            <MaterialIcon name="send" :size="18" class="text-sky-500" />
            <span>Telegram Channel Integration</span>
          </h2>
          <p class="text-xs text-muted-foreground mt-0.5">Test real-time alert delivery to your configured Telegram subscriber chat</p>
        </div>

        <Button
          size="sm"
          variant="secondary"
          class="gap-1.5 text-xs"
          :disabled="testingBot"
          @click="sendTestAlert"
        >
          <MaterialIcon name="bolt" :size="15" :class="testingBot ? 'animate-spin' : 'text-amber-500'" />
          <span>{{ testingBot ? 'Sending...' : 'Send Test Alert' }}</span>
        </Button>
      </div>

      <!-- Test Status Response -->
      <div
        v-if="testResult"
        class="p-3 rounded-lg text-xs flex items-center gap-2"
        :class="testResult.success ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-600 dark:text-amber-300 border border-amber-500/20'"
      >
        <MaterialIcon :name="testResult.success ? 'check_circle' : 'info'" :size="16" />
        <span>{{ testResult.detail }}</span>
      </div>

      <!-- Recent Notifications Log -->
      <div v-if="recentNotifications.length > 0" class="space-y-2 pt-2">
        <p class="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Recent Dispatched Alerts</p>
        <div class="space-y-1.5">
          <div
            v-for="notif in recentNotifications"
            :key="notif.id"
            class="flex items-center justify-between p-2.5 rounded-lg bg-muted/60 border border-border text-xs"
          >
            <div class="flex items-center gap-2">
              <span
                class="h-2 w-2 rounded-full"
                :class="notif.status === 'sent' ? 'bg-emerald-500' : notif.status === 'pending' ? 'bg-amber-500' : 'bg-destructive'"
              />
              <span class="font-medium text-foreground capitalize">{{ notif.notification_type.replace('_', ' ') }}</span>
              <span class="text-muted-foreground">via {{ notif.channel }}</span>
            </div>
            <span class="text-[10px] text-muted-foreground font-mono">
              {{ new Date(notif.created_at).toLocaleTimeString() }}
            </span>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>
