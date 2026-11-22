<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '~/lib/utils'

interface Props {
  class?: string
  hoverable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  class: '',
  hoverable: false
})

const classes = computed(() =>
  cn(
    'rounded-xl border border-border bg-card text-card-foreground shadow-sm transition-all duration-200',
    props.hoverable ? 'hover:border-zinc-700 hover:shadow-md hover:-translate-y-0.5' : '',
    props.class
  )
)
</script>

<template>
  <div :class="classes">
    <slot />
  </div>
</template>
