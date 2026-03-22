import { ref, watchEffect } from 'vue'
import { useDark, useToggle } from '@vueuse/core'

/**
 * Global theme state and toggler using @vueuse/core.
 * It will add "dark" class to the HTML tag based on the state.
 */
export function useTheme() {
  const isDark = useDark({
    initialValue: 'light',
    storageKey: 'vueuse-color-scheme',
  })
  const toggleDark = useToggle(isDark)

  return {
    isDark,
    toggleDark
  }
}
