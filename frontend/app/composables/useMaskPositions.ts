import { ref, onMounted, onUnmounted, type Ref, watch } from 'vue'

export interface MaskPosition {
  x: number
  y: number
  sw: number
  sh: number
}

/**
 * Composable to handle shared background image masking logic.
 */
export function useMaskPositions(
  containerRef: Ref<HTMLElement | null>,
  cardRefs: Ref<(HTMLElement | null)[]>
) {
  const positions = ref<MaskPosition[]>([])

  const updatePositions = () => {
    if (!containerRef.value) return

    const containerRect = containerRef.value.getBoundingClientRect()
    const sw = containerRect.width
    const sh = containerRect.height

    // If height is 0, we might need to wait or layout hasn't happened
    if (sh === 0) return

    positions.value = cardRefs.value.map((card) => {
      if (!card) return { x: 0, y: 0, sw, sh }
      const rect = card.getBoundingClientRect()
      return {
        x: rect.left - containerRect.left,
        y: rect.top - containerRect.top,
        sw,
        sh,
      }
    })
  }

  let observer: ResizeObserver | null = null

  onMounted(() => {
    // Retry logic if refs are not ready
    const init = () => {
      if (containerRef.value) {
        observer = new ResizeObserver(updatePositions)
        observer.observe(containerRef.value)
        updatePositions()
      } else {
        setTimeout(init, 50)
      }
    }
    init()
  })

  // Watch for changes in cardRefs to update positions
  watch(() => cardRefs.value.length, updatePositions)

  onUnmounted(() => {
    if (observer) {
      observer.disconnect()
    }
  })

  return {
    positions,
    updatePositions
  }
}
