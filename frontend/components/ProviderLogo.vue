<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  provider?: string | null
  size?: number | string
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  provider: '',
  size: 20,
  class: ''
})

const normalizedProvider = computed(() => {
  const p = (props.provider || '').toLowerCase()
  if (p.includes('anthropic') || p.includes('claude')) return 'anthropic'
  if (p.includes('openai') || p.includes('chatgpt') || p.includes('gpt')) return 'openai'
  if (p.includes('xai') || p.includes('grok')) return 'xai'
  if (p.includes('google') || p.includes('gemini')) return 'google'
  if (p.includes('perplexity')) return 'perplexity'
  if (p.includes('cursor')) return 'cursor'
  if (p.includes('github') || p.includes('copilot')) return 'github'
  return 'default'
})

const pxSize = computed(() => {
  return typeof props.size === 'number' ? `${props.size}px` : props.size
})
</script>

<template>
  <span
    class="inline-flex items-center justify-center shrink-0 transition-transform duration-200"
    :class="props.class"
    :style="{ width: pxSize, height: pxSize }"
  >
    <!-- Anthropic / Claude -->
    <svg
      v-if="normalizedProvider === 'anthropic'"
      viewBox="0 0 24 24"
      fill="none"
      class="w-full h-full text-amber-500"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M13.82 3H10.18L4 21H7.82L9.27 16.73H14.73L16.18 21H20L13.82 3ZM10.36 13.55L12 8.64L13.64 13.55H10.36Z"
        fill="currentColor"
      />
    </svg>

    <!-- OpenAI / ChatGPT -->
    <svg
      v-else-if="normalizedProvider === 'openai'"
      viewBox="0 0 24 24"
      fill="currentColor"
      class="w-full h-full text-emerald-500"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M22.28 9.37a5.98 5.98 0 0 0-.52-4.9 6.09 6.09 0 0 0-6.52-2.88A6.07 6.07 0 0 0 10.98.5a6.03 6.03 0 0 0-5.75 4.19 6.07 6.07 0 0 0-4.08 2.95 6.01 6.01 0 0 0 .76 7.08 6.08 6.08 0 0 0 .52 4.9 6.09 6.09 0 0 0 6.52 2.88A6.07 6.07 0 0 0 13.02 23.5a6.03 6.03 0 0 0 5.75-4.19 6.07 6.07 0 0 0 4.08-2.95 6.01 6.01 0 0 0-.57-6.99ZM13.02 22a4.57 4.57 0 0 1-3.14-1.28l.15-.09 5.23-3.02a.76.76 0 0 0 .38-.66v-7.38l2.22 1.28a.07.07 0 0 1 .04.06v6.23a4.57 4.57 0 0 1-4.88 4.86Zm-8.4-4.52a4.56 4.56 0 0 1-.61-3.34l.16.1 5.23 3.02a.76.76 0 0 0 .76 0l6.39-3.69v2.56a.07.07 0 0 1-.03.06l-5.4 3.12a4.56 4.56 0 0 1-6.5-1.83Zm-1.8-8.91a4.58 4.58 0 0 1 2.53-2.07v6.2a.76.76 0 0 0 .38.66l6.39 3.69-2.22 1.28a.07.07 0 0 1-.07 0l-5.4-3.12a4.58 4.58 0 0 1-1.61-6.64Zm14.47 1.4-6.39-3.69 2.22-1.28a.07.07 0 0 1 .07 0l5.4 3.12a4.58 4.58 0 0 1-1.3 8.35v-6.2a.76.76 0 0 0-.38-.66l.38.36Zm2.41-3.63-.16-.1-5.23-3.02a.76.76 0 0 0-.76 0L7.16 6.91V4.35a.07.07 0 0 1 .03-.06l5.4-3.12a4.56 4.56 0 0 1 7.11 3.57v.6Zm-9.92 5.06-2.55-1.47 2.55-1.47 2.55 1.47-2.55 1.47Z"
      />
    </svg>

    <!-- xAI / Grok -->
    <svg
      v-else-if="normalizedProvider === 'xai'"
      viewBox="0 0 24 24"
      fill="currentColor"
      class="w-full h-full text-foreground"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
      />
    </svg>

    <!-- Google / Gemini -->
    <svg
      v-else-if="normalizedProvider === 'google'"
      viewBox="0 0 24 24"
      class="w-full h-full text-blue-500"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fill="currentColor"
        d="M12 2C12 7.52285 7.52285 12 2 12C7.52285 12 12 16.4772 12 22C12 16.4772 16.4772 12 22 12C16.4772 12 12 7.52285 12 2Z"
      />
    </svg>

    <!-- Perplexity -->
    <svg
      v-else-if="normalizedProvider === 'perplexity'"
      viewBox="0 0 24 24"
      fill="currentColor"
      class="w-full h-full text-cyan-500"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M12 2L4 7v10l8 5 8-5V7l-8-5zm6 13.8L12 19.5l-6-3.7V8.2L12 4.5l6 3.7v7.6zM12 7l4 2.5v5L12 17l-4-2.5v-5L12 7z"
      />
    </svg>

    <!-- Cursor -->
    <svg
      v-else-if="normalizedProvider === 'cursor'"
      viewBox="0 0 24 24"
      fill="currentColor"
      class="w-full h-full text-violet-500"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M12 2L2 8.5L12 15L22 8.5L12 2ZM2 10.5V15.5L12 22V17L2 10.5ZM22 10.5L12 17V22L22 15.5V10.5Z"
      />
    </svg>

    <!-- GitHub / Copilot -->
    <svg
      v-else-if="normalizedProvider === 'github'"
      viewBox="0 0 24 24"
      fill="currentColor"
      class="w-full h-full text-purple-500 dark:text-purple-400"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fill-rule="evenodd"
        clip-rule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
      />
    </svg>

    <!-- Default AI sparkle -->
    <svg
      v-else
      viewBox="0 0 24 24"
      fill="currentColor"
      class="w-full h-full text-emerald-500"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M12 2L13.8 8.2L20 10L13.8 11.8L12 18L10.2 11.8L4 10L10.2 8.2L12 2ZM19 16L19.9 19.1L23 20L19.9 20.9L19 24L18.1 20.9L15 20L18.1 19.1L19 16ZM5 16L5.9 19.1L9 20L5.9 20.9L5 24L4.1 20.9L1 20L4.1 19.1L5 16Z"
      />
    </svg>
  </span>
</template>
