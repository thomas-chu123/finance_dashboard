import { ref } from 'vue'

/**
 * Vue 3 Composition API for HTML5 Drag & Drop functionality
 * 提供拖放操作的組合邏輯和狀態管理
 */
export function useDragDrop() {
  // 正在拖動的元素索引
  const draggedIndex = ref(null)
  const draggedElement = ref(null)
  const dragOverIndex = ref(null)
  
  // 拖放視覺反饋狀態
  const isDragging = ref(false)

  /**
   * 開始拖動事件處理
   * @param {DragEvent} event - 拖動事件
   * @param {number} index - 卡片索引
   */
  function handleDragStart(event, index) {
    draggedIndex.value = index
    draggedElement.value = event.currentTarget
    isDragging.value = true
    
    // 設置拖動效果
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/html', event.currentTarget.innerHTML)
    
    // 視覺反饋：添加透明度
    setTimeout(() => {
      if (draggedElement.value) {
        draggedElement.value.style.opacity = '0.5'
      }
    }, 0)
  }

  /**
   * 拖動結束事件處理
   * @param {DragEvent} event - 拖動事件
   */
  function handleDragEnd(event) {
    isDragging.value = false
    dragOverIndex.value = null
    
    // 移除視覺反饋
    if (draggedElement.value) {
      draggedElement.value.style.opacity = '1'
    }
    
    draggedIndex.value = null
    draggedElement.value = null
  }

  /**
   * 拖動進入有效放置目標事件
   * @param {DragEvent} event - 拖動事件
   * @param {number} index - 目標卡片索引
   */
  function handleDragEnter(event, index) {
    event.preventDefault()
    dragOverIndex.value = index
    
    // 視覺反饋：目標卡片邊框或背景改變
    if (event.currentTarget) {
      event.currentTarget.classList.add('drag-over')
    }
  }

  /**
   * 拖動經過有效放置目標事件
   * @param {DragEvent} event - 拖動事件
   */
  function handleDragOver(event) {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }

  /**
   * 拖動離開有效放置目標事件
   * @param {DragEvent} event - 拖動事件
   */
  function handleDragLeave(event) {
    // 移除視覺反饋
    if (event.currentTarget) {
      event.currentTarget.classList.remove('drag-over')
    }
  }

  /**
   * 放置事件處理 - 返回索引對供父組件使用
   * @param {DragEvent} event - 拖動事件
   * @param {number} index - 放置目標索引
   * @returns {{fromIndex: number, toIndex: number}} 拖動和放置的索引
   */
  function handleDrop(event, index) {
    event.preventDefault()
    event.stopPropagation()
    
    // 移除視覺反饋
    if (event.currentTarget) {
      event.currentTarget.classList.remove('drag-over')
    }
    
    if (draggedIndex.value !== null && draggedIndex.value !== index) {
      return {
        fromIndex: draggedIndex.value,
        toIndex: index
      }
    }
    
    return null
  }

  /**
   * 重置拖放狀態
   */
  function resetDragState() {
    draggedIndex.value = null
    draggedElement.value = null
    dragOverIndex.value = null
    isDragging.value = false
  }

  return {
    // 狀態
    draggedIndex,
    draggedElement,
    dragOverIndex,
    isDragging,
    
    // 事件處理函數
    handleDragStart,
    handleDragEnd,
    handleDragEnter,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    resetDragState
  }
}
