import { ref, watchEffect, type Ref } from 'vue'

/**
 * Calculates how wide the image would be if scaled to fill the section height.
 */
export function useImageWidth(bgImage: string, sectionHeight: Ref<number>) {
  const imageWidth = ref(0)

  // watchEffect runs during SSR, but Image is only available in the browser.
  watchEffect(() => {
    if (import.meta.server) return
    if (!bgImage) return

    const img = new Image()
    img.src = bgImage
    img.onload = () => {
      if (img.naturalHeight > 0) {
        imageWidth.value = img.naturalWidth * (sectionHeight.value / img.naturalHeight)
      }
    }
  })

  return imageWidth
}
