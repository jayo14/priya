<script setup lang="ts">
import { cn } from '~/lib/utils'

interface Props {
  orientation?: 'horizontal' | 'vertical'
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  orientation: 'horizontal',
  class: ''
})
</script>

<template>
  <div
    :class="
      cn(
        'shrink-0 bg-border',
        props.orientation === 'vertical' ? 'h-full w-[1px]' : 'h-[1px] w-full',
        props.class
      )
    "
  />
</template>
