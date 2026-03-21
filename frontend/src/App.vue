<template>
  <router-view />
</template>

<script setup>
import { useTheme } from './composables/useTheme'
// Initialize global theme state to apply "dark" class to html tag globally
useTheme()
</script>
