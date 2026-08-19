import { ref, onMounted, onUnmounted, type CSSProperties } from 'vue'

/**
 * Composable for scroll-triggered staggered animations using IntersectionObserver.
 */
export function useStaggeredReveal(threshold = 0.15) {
  const containerRef = ref<HTMLElement | null>(null)
  const visible = ref(false)

  let observer: IntersectionObserver | null = null

  onMounted(() => {
    if (!containerRef.value) return

    observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          visible.value = true
          // Fire once
          if (observer) {
            observer.disconnect()
          }
        }
      },
      { threshold }
    )

    observer.observe(containerRef.value)
  })

  onUnmounted(() => {
    if (observer) {
      observer.disconnect()
    }
  })

  const getAnimStyle = (index: number): CSSProperties => {
    return {
      opacity: visible.value ? 1 : 0,
      transform: visible.value ? 'translateY(0)' : 'translateY(24px)',
      transition: `opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1) ${index * 120}ms, transform 0.6s cubic-bezier(0.16, 1, 0.3, 1) ${index * 120}ms`
    }
  }

  return {
    containerRef,
    visible,
    getAnimStyle
  }
}
