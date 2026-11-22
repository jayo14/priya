<template>
  <div class="min-h-screen bg-background flex flex-col text-foreground">
    <Navbar />

    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <slot />
    </main>

    <footer class="border-t border-border/60 bg-zinc-950/60 py-6 text-center text-xs text-zinc-500">
      <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <span class="font-semibold text-zinc-300">Priya</span>
          <span>·</span>
          <span>Personal AI Subscription Deal Scout</span>
        </div>
        <div class="flex items-center gap-4 text-zinc-400">
          <span>Deterministic Verification</span>
          <span>·</span>
          <span>Zero Paid APIs</span>
          <span>·</span>
          <span>Nigeria Usability Focused</span>
        </div>
      </div>
    </footer>
  </div>
</template>
