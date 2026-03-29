// src/composables/useBreakpoint.js
import { ref, onMounted, onUnmounted } from 'vue'

export function useBreakpoint() {
    const isMobile = ref(false)      // < 768px
    const isTablet = ref(false)      // 768px - 1023px
    const isDesktop = ref(false)     // >= 1024px
    const isLargeScreen = ref(false) // >= 1024px (consistent with existing logic)

    function update() {
        const w = window.innerWidth
        isMobile.value = w < 768
        isTablet.value = w >= 768 && w < 1024
        isDesktop.value = w >= 1024
        isLargeScreen.value = w >= 1024
    }

    onMounted(() => {
        update()
        window.addEventListener('resize', update)
    })

    onUnmounted(() => {
        window.removeEventListener('resize', update)
    })

    return { isMobile, isTablet, isDesktop, isLargeScreen }
}
