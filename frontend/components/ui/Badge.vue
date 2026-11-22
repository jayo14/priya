<script setup lang="ts">
import { computed } from 'vue'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '~/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-primary/20 text-emerald-400 border-emerald-500/30',
        secondary: 'border-transparent bg-secondary text-secondary-foreground',
        destructive: 'border-transparent bg-destructive/20 text-red-400 border-red-500/30',
        outline: 'text-foreground border-border',
        verified: 'border-emerald-500/30 bg-emerald-950/60 text-emerald-400',
        likely: 'border-blue-500/30 bg-blue-950/60 text-blue-400',
        unverified: 'border-zinc-700 bg-zinc-900 text-zinc-400',
        restricted: 'border-amber-500/30 bg-amber-950/60 text-amber-400',
        expired: 'border-zinc-800 bg-zinc-950 text-zinc-600 line-through'
      }
    },
    defaultVariants: {
      variant: 'default'
    }
  }
)

type BadgeVariants = VariantProps<typeof badgeVariants>

interface Props {
  variant?: BadgeVariants['variant']
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  class: ''
})

const classes = computed(() => cn(badgeVariants({ variant: props.variant }), props.class))
</script>

<template>
  <div :class="classes">
    <slot />
  </div>
</template>
