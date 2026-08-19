import { ref, onMounted, onUnmounted, type Ref } from 'vue'

export interface MaskPosition {
  x: number
  y: number
  sw: number
  sh: number
}

/**
 * Composable to handle shared background image masking logic.
 * Takes a ref to the section container and a ref to an array of card elements.
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
    if (containerRef.value) {
      observer = new ResizeObserver(updatePositions)
      observer.observe(containerRef.value)
      updatePositions()
      // Initial delay to ensure layout is settled
      setTimeout(updatePositions, 100)
    }
  })

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
