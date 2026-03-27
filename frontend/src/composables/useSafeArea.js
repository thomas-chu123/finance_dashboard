import { ref, onMounted } from 'vue'

export function useSafeArea() {
    const insets = ref({
        top: 0,
        bottom: 0,
        left: 0,
        right: 0
    })

    function updateInsets() {
        // Get computed safe area insets from CSS env() variables
        // Note: These must be exposed as CSS variables first in main.css
        const style = getComputedStyle(document.documentElement)

        insets.value = {
            top: parseInt(style.getPropertyValue('--safe-area-top')) || 0,
            bottom: parseInt(style.getPropertyValue('--safe-area-bottom')) || 0,
            left: parseInt(style.getPropertyValue('--safe-area-left')) || 0,
            right: parseInt(style.getPropertyValue('--safe-area-right')) || 0
        }
    }

    onMounted(() => {
        updateInsets()
        // Safe area might change on orientation change
        window.addEventListener('resize', updateInsets)
        window.addEventListener('orientationchange', updateInsets)
    })

    return { insets }
}
