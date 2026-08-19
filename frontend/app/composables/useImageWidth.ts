import { ref, watch, type Ref } from 'vue'

export function useImageWidth(bgImage: string, sectionHeight: Ref<number>) {
  const imageWidth = ref(0)
  const naturalDimensions = ref({ w: 0, h: 0 })

  if (import.meta.client) {
    const img = new Image()
    img.src = bgImage
    img.onload = () => {
      naturalDimensions.value = { w: img.naturalWidth, h: img.naturalHeight }
      calculateWidth()
    }
  }

  const calculateWidth = () => {
    if (naturalDimensions.value.h > 0) {
      imageWidth.value = naturalDimensions.value.w * (sectionHeight.value / naturalDimensions.value.h)
    }
  }

  watch(sectionHeight, calculateWidth)

  return imageWidth
}
