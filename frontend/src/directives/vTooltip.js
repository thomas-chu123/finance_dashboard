/**
 * Smart Tooltip Directive
 * 
 * 動態計算 tooltip 位置，根據視口空間自動調整方向
 * 優先級：右 → 左 → 上 → 下
 * 
 * 使用方式：
 * <span v-tooltip.right="'Tooltip text'">Content</span>
 * <span v-tooltip:top="'Tooltip text'">Content</span>
 * <span v-tooltip="{ text: 'Tooltip text', placement: 'right' }">Content</span>
 */

const TOOLTIP_GAP = 8 // px，tooltip 與目標元素的距離
const TOOLTIP_WIDTH = 220 // px，tooltip 寬度
const VIEWPORT_PADDING = 16 // px，與視口邊緣的最小距離

/**
 * 計算最佳 tooltip 位置
 * @param {Element} el - 目標元素
 * @param {String} preferredPlacement - 首選位置 ('right', 'left', 'top', 'bottom')
 * @returns {Object} { placement, top, left/right }
 */
function calculateTooltipPosition(el, preferredPlacement = 'right') {
  const rect = el.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  // 計算各方向的可用空間
  const rightSpace = viewportWidth - rect.right
  const leftSpace = rect.left
  const topSpace = rect.top
  const bottomSpace = viewportHeight - rect.bottom

  // 判斷是否有足夠空間
  const hasRightSpace = rightSpace > TOOLTIP_WIDTH + TOOLTIP_GAP + VIEWPORT_PADDING
  const hasLeftSpace = leftSpace > TOOLTIP_WIDTH + TOOLTIP_GAP + VIEWPORT_PADDING
  const hasTopSpace = topSpace > 100 + VIEWPORT_PADDING // 假設 tooltip 高度約 100px
  const hasBottomSpace = bottomSpace > 100 + VIEWPORT_PADDING

  // 決定最終位置
  let placement = preferredPlacement
  if (preferredPlacement === 'right' && !hasRightSpace && hasLeftSpace) {
    placement = 'left'
  } else if (preferredPlacement === 'left' && !hasLeftSpace && hasRightSpace) {
    placement = 'right'
  } else if (preferredPlacement === 'top' && !hasTopSpace && hasBottomSpace) {
    placement = 'bottom'
  } else if (preferredPlacement === 'bottom' && !hasBottomSpace && hasTopSpace) {
    placement = 'top'
  }

  return {
    placement,
    hasSpace: {
      right: hasRightSpace,
      left: hasLeftSpace,
      top: hasTopSpace,
      bottom: hasBottomSpace
    }
  }
}

/**
 * 應用 tooltip 位置
 */
function applyTooltipPosition(el, placement) {
  // 移除所有位置相關的 class
  el.classList.remove(
    'tooltip-right',
    'tooltip-left',
    'tooltip-top',
    'tooltip-bottom'
  )
  // 添加新的位置 class
  el.classList.add(`tooltip-${placement}`)
}

/**
 * Tooltip Directive
 */
export const vTooltip = {
  mounted(el, binding) {
    const { value, arg, modifiers } = binding

    // 解析 tooltip 配置
    let text, placement
    if (typeof value === 'string') {
      text = value
      placement = arg || Object.keys(modifiers)[0] || 'right'
    } else if (typeof value === 'object') {
      text = value.text || value.content || ''
      placement = value.placement || arg || 'right'
    }

    if (!text) return

    // 添加 tooltip-trigger class
    el.classList.add('tooltip-trigger-smart')

    // 設置 data-tooltip
    el.setAttribute('data-tooltip', text)

    // 初始化位置計算
    const calculateAndApply = () => {
      const { placement: finalPlacement } = calculateTooltipPosition(el, placement)
      applyTooltipPosition(el, finalPlacement)
    }

    // 初次計算
    calculateAndApply()

    // 監聽視口變化
    const resizeObserver = new ResizeObserver(() => {
      calculateAndApply()
    })
    resizeObserver.observe(el)

    // 監聽窗口大小變化
    const handleWindowResize = () => {
      calculateAndApply()
    }
    window.addEventListener('resize', handleWindowResize)

    // 存儲清理函數
    el._tooltipCleanup = () => {
      resizeObserver.disconnect()
      window.removeEventListener('resize', handleWindowResize)
    }
  },

  updated(el, binding) {
    const { value, arg, modifiers } = binding

    // 更新 tooltip 文本
    let text
    if (typeof value === 'string') {
      text = value
    } else if (typeof value === 'object') {
      text = value.text || value.content || ''
    }

    if (text) {
      el.setAttribute('data-tooltip', text)
    }
  },

  unmounted(el) {
    if (el._tooltipCleanup) {
      el._tooltipCleanup()
      delete el._tooltipCleanup
    }
  }
}

export default vTooltip
