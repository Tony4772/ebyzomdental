<script setup lang="ts">
import { computed, type CSSProperties } from 'vue'

interface MaskPosition {
  x: number
  y: number
  sw: number
  sh: number
}

interface Props {
  bgImage: string
  position?: MaskPosition
  imageWidth?: number
  focalX?: number
  className?: string
}

const props = withDefaults(defineProps<Props>(), {
  focalX: 0.8,
  imageWidth: 0,
  className: ''
})

const cardStyle = computed<CSSProperties>(() => {
  const { position, imageWidth, focalX, bgImage } = props
  if (!position || !bgImage) return {}

  const overflow = imageWidth > position.sw ? imageWidth - position.sw : 0
  const focalOffset = overflow * focalX

  return {
    backgroundImage: `url(${bgImage})`,
    backgroundSize: `auto ${position.sh}px`,
    backgroundPosition: `-${position.x + focalOffset}px -${position.y}px`,
    backgroundRepeat: 'no-repeat'
  }
})
</script>

<template>
  <div
    :class="className"
    :style="cardStyle"
  >
    <slot />
  </div>
</template>
