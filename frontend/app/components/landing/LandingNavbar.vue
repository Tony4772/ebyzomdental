<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'

const isOpen = ref(false)

const toggleMenu = () => {
  isOpen.value = !isOpen.value
}

const navLinks = [
  { label: 'Inicio', to: '#' },
  { label: 'Servicios', to: '#' },
  { label: 'Nosotros', to: '#' },
  { label: 'Galería', to: '#' },
  { label: 'Contacto', to: '#' }
]

watch(isOpen, (val) => {
  if (val && typeof document !== 'undefined') {
    document.body.style.overflow = 'hidden'
  } else if (typeof document !== 'undefined') {
    document.body.style.overflow = ''
  }
})

onUnmounted(() => {
  if (typeof document !== 'undefined') {
    document.body.style.overflow = ''
  }
})
</script>

<template>
  <nav class="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 md:px-6 py-2 md:py-3 bg-white/80 backdrop-blur-md">
    <!-- Logo -->
    <div class="flex flex-col">
      <div class="text-xl md:text-2xl font-extrabold uppercase tracking-tight leading-none text-black">
        <div>EBYZOM</div>
        <div class="-mt-1.5 md:-mt-2">Dental</div>
      </div>
      <div class="text-[8px] md:text-[9px] font-medium leading-none mt-1.5 md:mt-2 text-black">
        gestión clínica avanzada
      </div>
    </div>

    <!-- Desktop Nav -->
    <div class="hidden md:flex items-center gap-6">
      <div class="text-sm font-semibold text-black">
        Urgencias Dentales
      </div>
      <NuxtLink
        to="/login"
        class="px-6 py-3 bg-white rounded-full border border-black text-sm font-semibold hover:bg-black hover:text-white transition-colors duration-200"
      >
        Acceder
      </NuxtLink>
    </div>

    <!-- Mobile Hamburger -->
    <button
      class="md:hidden w-10 h-10 flex items-center justify-center relative z-50"
      @click="toggleMenu"
    >
      <span
        class="absolute h-0.5 w-6 bg-black rounded-full transition-all duration-300 ease-[cubic-bezier(0.76,0,0.24,1)]"
        :class="isOpen ? 'rotate-45 translate-y-0' : '-translate-y-2'"
      />
      <span
        class="absolute h-0.5 w-6 bg-black rounded-full transition-all duration-300 ease-[cubic-bezier(0.76,0,0.24,1)]"
        :class="isOpen ? 'opacity-0 scale-x-0' : 'opacity-100 scale-x-100'"
      />
      <span
        class="absolute h-0.5 w-6 bg-black rounded-full transition-all duration-300 ease-[cubic-bezier(0.76,0,0.24,1)]"
        :class="isOpen ? '-rotate-45 translate-y-0' : 'translate-y-2'"
      />
    </button>

    <!-- Mobile Menu Overlay -->
    <div
      class="md:hidden fixed inset-0 z-40 transition-all duration-500"
      :class="isOpen ? 'pointer-events-auto' : 'pointer-events-none'"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/20 backdrop-blur-sm transition-opacity duration-500"
        :class="isOpen ? 'opacity-100' : 'opacity-0'"
        @click="isOpen = false"
      />

      <!-- Panel -->
      <div
        class="absolute top-0 right-0 h-full w-[85%] max-w-sm bg-white shadow-2xl transition-transform duration-500 ease-[cubic-bezier(0.76,0,0.24,1)]"
        :class="isOpen ? 'translate-x-0' : 'translate-x-full'"
      >
        <div class="flex flex-col justify-center h-full px-8 gap-1">
          <a
            v-for="(link, i) in navLinks"
            :key="link.label"
            :href="link.to"
            class="text-4xl font-bold text-black hover:text-neutral-500 transition-all duration-500 ease-[cubic-bezier(0.76,0,0.24,1)]"
            :style="{
              transitionDelay: `${100 + i * 60}ms`,
              opacity: isOpen ? 1 : 0,
              transform: isOpen ? 'translateX(0)' : 'translateX(32px)'
            }"
            @click="isOpen = false"
          >
            {{ link.label }}
          </a>

          <div
            class="mt-8 pt-8 border-t border-neutral-200 transition-all duration-500"
            :style="{
              transitionDelay: '450ms',
              opacity: isOpen ? 1 : 0,
              transform: isOpen ? 'translateY(0)' : 'translateY(16px)'
            }"
          >
            <div class="text-sm font-semibold text-black mb-4">
              Urgencias Dentales
            </div>
            <NuxtLink
              to="/login"
              class="block w-full px-6 py-4 bg-black rounded-full text-white text-center text-sm font-semibold hover:bg-neutral-800 transition-colors duration-200"
              @click="isOpen = false"
            >
              Iniciar Sesión
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>
