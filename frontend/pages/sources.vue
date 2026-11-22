<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Source } from '~/lib/api'
import { usePriyaApi } from '~/composables/usePriyaApi'
import Card from '~/components/ui/Card.vue'
import Button from '~/components/ui/Button.vue'
import MaterialIcon from '~/components/MaterialIcon.vue'

const api = usePriyaApi()

const sources = ref<Source[]>([])
const loading = ref(true)
const collectingId = ref<number | null>(null)
const collectingAll = ref(false)
const runningPipeline = ref(false)
const pipelineNotice = ref<string | null>(null)

const loadSources = async () => {
  loading.value = true
  try {
    sources.value = await api.getSources()
  } catch (err) {
    console.error('Failed to load sources:', err)
  } finally {
    loading.value = false
  }
}

const collectSource = async (id: number) => {
  collectingId.value = id
  try {
    const res = await api.collectSource(id)
    pipelineNotice.value = `Scouted ${res.items_discovered} item(s) from source.`
    await loadSources()
  } catch (err) {
    console.error('Error scouting source:', err)
  } finally {
    collectingId.value = null
  }
}

const collectAll = async () => {
  collectingAll.value = true
  try {
    const res = await api.collectAll()
    pipelineNotice.value = `Scouted ${res.total_items_discovered} new items across all channels.`
    await loadSources()
  } catch (err) {
    console.error('Error scouting all sources:', err)
  } finally {
    collectingAll.value = false
  }
}

const runPipeline = async () => {
  runningPipeline.value = true
  try {
    const res = await api.runProcessing(50)
    pipelineNotice.value = `Pipeline processed ${res.items_processed} items: ${res.promotions_created} new promotions created, ${res.promotions_corroborated} corroborated.`
    await loadSources()
  } catch (err) {
    console.error('Pipeline error:', err)
  } finally {
    runningPipeline.value = false
  }
}

onMounted(() => {
  loadSources()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-foreground tracking-tight flex items-center gap-2">
          <MaterialIcon name="travel_explore" :size="24" class="text-primary" />
          <span>Monitored Sources & Ingestion</span>
        </h1>
        <p class="text-xs text-muted-foreground mt-1">Configured Telegram public channels, Reddit communities, newsroom RSS, and web feeds</p>
      </div>

      <div class="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          class="gap-1 text-xs"
          :disabled="runningPipeline"
          @click="runPipeline"
        >
          <MaterialIcon name="filter_alt" :size="16" :class="runningPipeline ? 'animate-spin' : ''" />
          <span>{{ runningPipeline ? 'Processing...' : 'Run Pipeline' }}</span>
        </Button>

        <Button
          size="sm"
          class="gap-1 text-xs"
          :disabled="collectingAll"
          @click="collectAll"
        >
          <MaterialIcon name="sync" :size="16" :class="collectingAll ? 'animate-spin' : ''" />
          <span>{{ collectingAll ? 'Scouting All...' : 'Scout All Sources' }}</span>
        </Button>
      </div>
    </div>

    <!-- Notification Alert -->
    <div
      v-if="pipelineNotice"
      class="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-600 dark:text-emerald-300 flex items-center justify-between"
    >
      <div class="flex items-center gap-2">
        <MaterialIcon name="check_circle" :size="18" class="text-primary" />
        <span>{{ pipelineNotice }}</span>
      </div>
      <Button variant="ghost" size="icon" class="h-6 w-6 text-muted-foreground hover:text-foreground" @click="pipelineNotice = null">
        <MaterialIcon name="close" :size="16" />
      </Button>
    </div>

    <!-- Sources Table Card (Strict shadcn Card & Theme-adaptive) -->
    <Card class="overflow-hidden bg-card border-border shadow-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-muted/70 text-muted-foreground font-semibold border-b border-border">
            <tr>
              <th class="p-3.5">Platform</th>
              <th class="p-3.5">Source Name</th>
              <th class="p-3.5">Identifier</th>
              <th class="p-3.5">Discovered Items</th>
              <th class="p-3.5">Last Polled</th>
              <th class="p-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border text-foreground">
            <tr v-for="source in sources" :key="source.id" class="hover:bg-muted/40 transition-colors">
              <td class="p-3.5">
                <span
                  class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded font-medium text-[11px] capitalize border"
                  :class="source.source_type === 'telegram' ? 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20' : source.source_type === 'reddit' ? 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20' : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'"
                >
                  <MaterialIcon
                    :name="source.source_type === 'telegram' ? 'send' : source.source_type === 'reddit' ? 'forum' : 'rss_feed'"
                    :size="12"
                  />
                  <span>{{ source.source_type }}</span>
                </span>
              </td>

              <td class="p-3.5 font-semibold text-foreground">
                {{ source.name }}
              </td>

              <td class="p-3.5 font-mono text-[11px] text-muted-foreground">
                {{ source.identifier }}
              </td>

              <td class="p-3.5 font-semibold text-foreground">
                {{ source.discovered_items_count }}
              </td>

              <td class="p-3.5 text-muted-foreground">
                {{ source.last_collected_at ? new Date(source.last_collected_at).toLocaleTimeString() : 'Never' }}
              </td>

              <td class="p-3.5 text-right">
                <Button
                  size="sm"
                  variant="ghost"
                  class="h-7 text-xs gap-1 text-primary hover:text-primary hover:bg-primary/10"
                  :disabled="collectingId === source.id"
                  @click="collectSource(source.id)"
                >
                  <MaterialIcon
                    name="refresh"
                    :size="14"
                    :class="collectingId === source.id ? 'animate-spin' : ''"
                  />
                  <span>Scout</span>
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  </div>
</template>
