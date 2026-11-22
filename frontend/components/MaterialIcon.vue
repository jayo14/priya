<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    name: string
    filled?: boolean
    size?: number | string
    class?: string
  }>(),
  {
    filled: false,
    size: 20,
    class: ''
  }
)

const style = computed(() => {
  const s = typeof props.size === 'number' ? `${props.size}px` : props.size
  return {
    fontSize: s,
    width: s,
    height: s
  }
})
</script>

<template>
  <span
    class="material-symbols-rounded select-none inline-flex items-center justify-center shrink-0"
    :class="[props.filled ? 'filled' : '', props.class]"
    :style="style"
  >
    {{ props.name }}
  </span>
</template>
