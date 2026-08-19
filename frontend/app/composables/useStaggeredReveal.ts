import { ref, onMounted, onUnmounted, type CSSProperties } from 'vue'

/**
 * Composable for scroll-triggered staggered animations using IntersectionObserver.
 */
export function useStaggeredReveal(threshold = 0.1) {
  const containerRef = ref<HTMLElement | null>(null)
  const visible = ref(false)

  let observer: IntersectionObserver | null = null

  onMounted(() => {
    // Fallback: force visible after 2 seconds if observer fails
    setTimeout(() => {
      visible.value = true
    }, 2000)

    const init = () => {
      if (!containerRef.value) {
        setTimeout(init, 50)
        return
      }

      observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            visible.value = true
            if (observer) observer.disconnect()
          }
        },
        { threshold }
      )

      observer.observe(containerRef.value)
    }
    init()
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
      transition: `opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1) ${index * 100}ms, transform 0.8s cubic-bezier(0.16, 1, 0.3, 1) ${index * 100}ms`
    }
  }

  return {
    containerRef,
    visible,
    getAnimStyle
  }
}
