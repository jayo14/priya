<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Source } from '~/lib/api'
import { usePriyaApi } from '~/composables/usePriyaApi'

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
        <h1 class="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <MaterialIcon name="travel_explore" :size="24" class="text-emerald-400" />
          <span>Monitored Sources & Ingestion</span>
        </h1>
        <p class="text-xs text-zinc-400 mt-1">Configured Telegram public channels, Reddit communities, newsroom RSS, and web feeds</p>
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
      class="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-300 flex items-center justify-between"
    >
      <div class="flex items-center gap-2">
        <MaterialIcon name="check_circle" :size="18" class="text-emerald-400" />
        <span>{{ pipelineNotice }}</span>
      </div>
      <button class="text-zinc-400 hover:text-white" @click="pipelineNotice = null">
        <MaterialIcon name="close" :size="16" />
      </button>
    </div>

    <!-- Sources Table Card -->
    <Card class="overflow-hidden bg-zinc-950/70 border-zinc-800">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-zinc-900/80 text-zinc-400 font-semibold border-b border-zinc-800">
            <tr>
              <th class="p-3.5">Platform</th>
              <th class="p-3.5">Source Name</th>
              <th class="p-3.5">Identifier</th>
              <th class="p-3.5">Discovered Items</th>
              <th class="p-3.5">Last Polled</th>
              <th class="p-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60 text-zinc-300">
            <tr v-for="source in sources" :key="source.id" class="hover:bg-zinc-900/40 transition-colors">
              <td class="p-3.5">
                <span
                  class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded font-medium text-[11px] capitalize border"
                  :class="source.source_type === 'telegram' ? 'bg-sky-500/10 text-sky-400 border-sky-500/20' : source.source_type === 'reddit' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'"
                >
                  <MaterialIcon
                    :name="source.source_type === 'telegram' ? 'send' : source.source_type === 'reddit' ? 'forum' : 'rss_feed'"
                    :size="12"
                  />
                  {{ source.source_type }}
                </span>
              </td>
              <td class="p-3.5 font-semibold text-white">
                {{ source.name }}
              </td>
              <td class="p-3.5 font-mono text-zinc-400">
                {{ source.identifier }}
              </td>
              <td class="p-3.5 font-semibold text-emerald-400">
                {{ source.discovered_items_count }}
              </td>
              <td class="p-3.5 text-zinc-400 text-[11px]">
                {{ source.last_polled_at ? new Date(source.last_polled_at).toLocaleTimeString() : 'Pending' }}
              </td>
              <td class="p-3.5 text-right">
                <Button
                  variant="secondary"
                  size="sm"
                  class="h-7 text-[11px] px-2.5"
                  :disabled="collectingId === source.id"
                  @click="collectSource(source.id)"
                >
                  <MaterialIcon name="refresh" :size="13" :class="collectingId === source.id ? 'animate-spin mr-1' : 'mr-1'" />
                  {{ collectingId === source.id ? 'Scouting' : 'Scout' }}
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  </div>
</template>
