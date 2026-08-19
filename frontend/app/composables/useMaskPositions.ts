import { ref, onMounted, onUnmounted, type Ref, watch } from 'vue'

export interface MaskPosition {
  x: number
  y: number
  sw: number
  sh: number
}

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

  let resizeObserver: ResizeObserver | null = null

  onMounted(() => {
    if (containerRef.value) {
      resizeObserver = new ResizeObserver(updatePositions)
      resizeObserver.observe(containerRef.value)
      // Forzar actualizaciones iniciales
      updatePositions()
      setTimeout(updatePositions, 100)
      setTimeout(updatePositions, 500)
    }
    window.addEventListener('resize', updatePositions)
  })

  onUnmounted(() => {
    resizeObserver?.disconnect()
    window.removeEventListener('resize', updatePositions)
  })

  // Re-calcular si el número de tarjetas cambia
  watch(() => cardRefs.value.length, updatePositions)

  return { positions, updatePositions }
}
