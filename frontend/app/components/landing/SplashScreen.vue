<script setup lang="ts">
import { ref, onMounted } from 'vue'

const emit = defineEmits(['complete'])

const counter = ref(0)
const exiting = ref(false)

onMounted(() => {
  const duration = 2000
  const steps = 100
  const stepTime = duration / steps

  const timer = setInterval(() => {
    if (counter.value < 100) {
      counter.value++
    } else {
      clearInterval(timer)
      setTimeout(() => {
        exiting.value = true
        setTimeout(() => {
          emit('complete')
        }, 700) // matches duration-700
      }, 200)
    }
  }, stepTime)
})
</script>

<template>
  <div
    class="fixed inset-0 z-[100] bg-white flex items-end justify-start transition-opacity duration-700 pointer-events-none"
    :class="{ 'opacity-0': exiting }"
  >
    <div class="text-7xl md:text-9xl font-bold tabular-nums p-6 md:p-10 leading-none text-black">
      {{ counter }}
    </div>
  </div>
</template>
