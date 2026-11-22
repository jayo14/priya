<script setup lang="ts">
import { watch } from 'vue'

const props = defineProps<{
  open: boolean
  title?: string
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
}>()

const close = () => {
  emit('update:open', false)
}

watch(
  () => props.open,
  (isOpen) => {
    if (typeof document !== 'undefined') {
      if (isOpen) {
        document.body.style.overflow = 'hidden'
      } else {
        document.body.style.overflow = ''
      }
    }
  }
)
</script>

<template>
  <Teleport to="body">
    <div
      v-if="props.open"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 md:p-10"
    >
      <!-- Backdrop -->
      <div
        class="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
        @click="close"
      />

      <!-- Content -->
      <div
        class="relative z-50 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-zinc-800 bg-zinc-950 p-6 text-foreground shadow-2xl animate-in fade-in-0 zoom-in-95"
      >
        <div class="flex items-center justify-between pb-4 border-b border-zinc-800/80 mb-4">
          <h2 v-if="props.title" class="text-lg font-semibold tracking-tight text-white flex items-center gap-2">
            <slot name="title">{{ props.title }}</slot>
          </h2>
          <button
            class="rounded-lg p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-800/80 transition-colors"
            @click="close"
          >
            <MaterialIcon name="close" :size="20" />
          </button>
        </div>

        <slot />
      </div>
    </div>
  </Teleport>
</template>
