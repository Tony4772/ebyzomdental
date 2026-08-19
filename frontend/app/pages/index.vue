<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

definePageMeta({
  layout: false
})

const HERO_IMAGE = 'https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260624_113640_ccf3cf97-d447-425b-a134-d7b09fc743fc.png&w=1280&q=85';
const SECTION2_IMAGE = 'https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260624_114219_414dfe80-f15c-4e25-bf52-b13721f4bd88.png&w=1280&q=85';
const SECTION3_IMG1 = 'https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260624_115253_c19ab167-8dd5-48b4-967d-b9f0d9d6e8fb.png&w=1280&q=85';
const SECTION3_IMG2 = 'https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260624_115237_fc519057-6e87-4abf-999a-9610b8b085b4.png&w=1280&q=85';
const SECTION3_BG = 'https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260624_114355_752ba9e6-0942-4abb-9047-5d9bb16632e9.png&w=1280&q=85';

const featureBars = ['Odontología Avanzada', 'Equipamiento de Alta Calidad', 'Atención Especializada'];

const services = [
  { name: 'Carillas\nDentales', num: '01', active: true },
  { name: 'Coronas\nDentales', num: '02', active: false },
  { name: 'Blanqueamiento\nDental', num: '03', active: false },
  { name: 'Implantes\nDentales', num: null, active: false },
];

const showSplash = ref(true)

// Section 1 logic
const s1Reveal = useStaggeredReveal()
const s1CardRefs = ref<(HTMLElement | null)[]>([])
const { positions: s1Positions } = useMaskPositions(s1Reveal.containerRef, s1CardRefs)
const s1Height = computed(() => s1Positions.value[0]?.sh || 0)
const s1ImageWidth = useImageWidth(HERO_IMAGE, s1Height)

// Section 2 logic
const s2Reveal = useStaggeredReveal()
const s2CardRefs = ref<(HTMLElement | null)[]>([])
const { positions: s2Positions } = useMaskPositions(s2Reveal.containerRef, s2CardRefs)
const s2Height = computed(() => s2Positions.value[0]?.sh || 0)
const s2ImageWidth = useImageWidth(SECTION2_IMAGE, s2Height)

// Section 3 logic
const s3Reveal = useStaggeredReveal()

const isMobile = ref(false)
onMounted(() => {
  if (typeof window !== 'undefined') {
    const mql = window.matchMedia('(max-width: 767px)')
    isMobile.value = mql.matches
    mql.addEventListener('change', (e) => isMobile.value = e.matches)
  }
})

const s1FocalX = computed(() => isMobile.value ? 0.7 : 0.8)
const s2FocalX = computed(() => isMobile.value ? 0.65 : 0.8)

useHead({
  title: 'EBYZOM Dental - Cuidado Dental Profesional'
})
</script>

<template>
  <div class="bg-white text-black min-h-screen font-['Open_Sauce_One',_sans-serif] selection:bg-black selection:text-white">
    <SplashScreen
      v-if="showSplash"
      @complete="showSplash = false"
    />
    <LandingNavbar />

    <!-- SECTION 1 - HERO -->
    <section
      ref="s1Reveal.containerRef"
      class="h-screen w-full overflow-hidden flex flex-col pt-24 md:pt-24 px-3 md:px-5 pb-1.5 md:pb-2 gap-1.5 md:gap-2"
    >
      <MaskedCard
        v-for="(feature, i) in featureBars"
        :key="feature"
        ref="s1CardRefs"
        :bg-image="HERO_IMAGE"
        :position="s1Positions[i]"
        :image-width="s1ImageWidth"
        :focal-x="s1FocalX"
        className="w-full h-14 md:h-20 shrink-0 rounded-xl md:rounded-2xl overflow-hidden relative"
        :style="s1Reveal.getAnimStyle(i)"
      >
        <span class="flex items-center justify-center h-full text-black text-lg md:text-3xl font-bold text-center relative z-10">
          {{ feature }}
        </span>
      </MaskedCard>

      <MaskedCard
        ref="s1CardRefs"
        :bg-image="HERO_IMAGE"
        :position="s1Positions[3]"
        :image-width="s1ImageWidth"
        :focal-x="s1FocalX"
        className="w-full flex-1 min-h-0 rounded-xl md:rounded-2xl overflow-hidden relative"
        :style="s1Reveal.getAnimStyle(3)"
      >
        <div class="absolute top-4 left-4 md:top-7 md:left-7 text-black text-xs md:text-sm font-semibold leading-4 md:leading-5 max-w-[200px] md:max-w-[300px] z-10">
          Ofrecemos servicios dentales profesionales<br>con las últimas tecnologías del sector.
        </div>
        <div class="absolute bottom-5 left-3 md:bottom-8 md:left-4 z-10">
          <span class="block text-black text-xs md:text-sm font-semibold mb-1 md:mb-2">Tu Clínica Dental de Confianza</span>
          <h1 class="text-black text-[clamp(3rem,11vw,11rem)] font-bold leading-[0.79] tracking-tight uppercase">
            Cuidado<br>Dental
          </h1>
        </div>
        <div class="absolute bottom-6 right-4 md:bottom-10 md:right-8 text-white text-xs md:text-sm font-semibold z-10">
          Consulta Gratuita
        </div>
      </MaskedCard>
    </section>

    <!-- SECTION 2 - SMILE GALLERY -->
    <section
      ref="s2Reveal.containerRef"
      class="min-h-screen md:h-screen w-full overflow-hidden flex flex-col pt-1.5 md:pt-2 px-3 md:px-5 pb-1.5 md:pb-2 gap-1.5 md:gap-2"
    >
      <div class="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-2 grid-rows-[auto_auto_auto_auto] md:grid-rows-[1fr_1fr_0.8fr] gap-1.5 md:gap-2">
        <!-- Card 0 -->
        <MaskedCard
          ref="s2CardRefs"
          :bg-image="SECTION2_IMAGE"
          :position="s2Positions[0]"
          :image-width="s2ImageWidth"
          :focal-x="s2FocalX"
          className="rounded-xl md:rounded-2xl overflow-hidden relative min-h-[160px] md:min-h-0"
          :style="s2Reveal.getAnimStyle(0)"
        >
          <div class="absolute top-4 left-5 md:top-6 md:left-7 text-white md:text-black text-2xl md:text-3xl font-bold z-10">
            Galería de Sonrisas
          </div>
          <div class="absolute bottom-4 left-5 md:bottom-6 md:left-7 text-white md:text-black text-xs md:text-sm font-semibold z-10">
            Estética dental avanzada
          </div>
        </MaskedCard>

        <!-- Card 1 -->
        <MaskedCard
          ref="s2CardRefs"
          :bg-image="SECTION2_IMAGE"
          :position="s2Positions[1]"
          :image-width="s2ImageWidth"
          :focal-x="s2FocalX"
          className="md:row-span-2 rounded-xl md:rounded-2xl overflow-hidden relative min-h-[200px] md:min-h-0"
          :style="s2Reveal.getAnimStyle(1)"
        >
          <div class="absolute bottom-16 left-5 md:bottom-20 md:left-7 text-white text-xs md:text-sm font-semibold leading-4 md:leading-5 z-10">
            Si deseas una sonrisa espectacular,<br>contáctanos para un diseño personalizado.
          </div>
          <NuxtLink
            to="/login"
            class="absolute bottom-4 right-4 md:bottom-6 md:right-6 px-5 py-3 md:px-8 md:py-5 bg-white rounded-full text-black text-base md:text-xl font-bold z-10 hover:scale-105 transition-transform"
          >
            Llámanos
          </NuxtLink>
        </MaskedCard>

        <!-- Card 2 -->
        <MaskedCard
          ref="s2CardRefs"
          :bg-image="SECTION2_IMAGE"
          :position="s2Positions[2]"
          :image-width="s2ImageWidth"
          :focal-x="s2FocalX"
          className="rounded-xl md:rounded-2xl overflow-hidden relative min-h-[160px] md:min-h-0"
          :style="s2Reveal.getAnimStyle(2)"
        >
          <h2 class="absolute top-4 left-5 md:top-6 md:left-7 text-white md:text-black text-[clamp(3rem,7vw,6rem)] font-bold leading-[0.9] z-10 uppercase">
            Cambio de<br>Sonrisa
          </h2>
        </MaskedCard>

        <!-- Card 3 -->
        <MaskedCard
          ref="s2CardRefs"
          :bg-image="SECTION2_IMAGE"
          :position="s2Positions[3]"
          :image-width="s2ImageWidth"
          :focal-x="s2FocalX"
          className="col-span-1 md:col-span-2 rounded-xl md:rounded-2xl overflow-hidden relative min-h-[200px] md:min-h-0"
          :style="s2Reveal.getAnimStyle(3)"
        >
          <div class="absolute inset-0 z-10 flex flex-wrap md:flex-nowrap gap-1.5 md:gap-2 p-2 md:p-3">
            <div
              v-for="svc in services"
              :key="svc.name"
              class="flex-1 min-w-[calc(50%-4px)] md:min-w-0 rounded-xl md:rounded-2xl p-3 md:p-5 flex flex-col justify-between"
              :class="svc.active ? 'bg-white/90 backdrop-blur-md' : 'bg-white/20 backdrop-blur-xl'"
            >
              <h3
                class="text-xl md:text-4xl font-bold leading-[1.05] whitespace-pre-line"
                :class="svc.active ? 'text-black' : 'text-white'"
              >
                {{ svc.name }}
              </h3>
              <div
                v-if="svc.num"
                class="self-end w-8 h-8 md:w-12 md:h-12 rounded-full border flex items-center justify-center text-xs md:text-sm font-semibold"
                :class="svc.active ? 'border-black text-black' : 'border-white text-white'"
              >
                {{ svc.num }}
              </div>
            </div>
          </div>
        </MaskedCard>
      </div>
    </section>

    <!-- SECTION 3 - IMPLANT DENTISTRY -->
    <section
      ref="s3Reveal.containerRef"
      class="min-h-screen md:h-screen w-full overflow-hidden flex flex-col pt-1.5 md:pt-2 px-3 md:px-5 pb-1.5 md:pb-2 gap-1.5 md:gap-2"
    >
      <div class="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-2 gap-1.5 md:gap-2">
        <!-- LEFT COLUMN -->
        <div class="flex flex-col gap-1.5 md:gap-2">
          <div
            class="rounded-xl md:rounded-2xl bg-stone-50 p-5 md:p-7 flex flex-col justify-between flex-[1.2] min-h-[180px] md:min-h-0"
            :style="s3Reveal.getAnimStyle(0)"
          >
            <h2 class="text-[clamp(3rem,7vw,6.5rem)] font-bold leading-[0.95] text-black uppercase">
              Implantología<br>Dental
            </h2>
            <p class="text-xs md:text-sm font-semibold text-black">
              Restaura tus piezas dentales
            </p>
          </div>

          <div
            class="flex gap-1.5 md:gap-2 flex-1 min-h-[140px] md:min-h-0"
            :style="s3Reveal.getAnimStyle(1)"
          >
            <div class="flex-1 rounded-xl md:rounded-2xl overflow-hidden">
              <img
                :src="SECTION3_IMG1"
                alt="Procedimiento de implante dental"
                class="w-full h-full object-cover"
              >
            </div>
            <div class="flex-1 rounded-xl md:rounded-2xl overflow-hidden">
              <img
                :src="SECTION3_IMG2"
                alt="Restauración dental"
                class="w-full h-full object-cover"
              >
            </div>
          </div>

          <div
            class="rounded-xl md:rounded-2xl bg-zinc-200 p-5 md:p-7 flex items-end justify-between flex-[0.8] min-h-[160px] md:min-h-0"
            :style="s3Reveal.getAnimStyle(2)"
          >
            <div>
              <p class="text-xs md:text-sm font-semibold text-black mb-2 md:mb-3">
                Consultoría
              </p>
              <h3 class="text-xl md:text-3xl font-bold text-black leading-6 md:leading-8 uppercase">
                Servicios de<br>Restauración<br>Dental
              </h3>
            </div>
            <NuxtLink
              to="/login"
              class="px-5 py-3 md:px-8 md:py-5 bg-white rounded-full text-black text-base md:text-xl font-bold hover:scale-105 transition-transform"
            >
              Reservar Cita
            </NuxtLink>
          </div>
        </div>

        <!-- RIGHT COLUMN -->
        <div
          class="rounded-xl md:rounded-2xl overflow-hidden relative min-h-[350px] md:min-h-0"
          :style="s3Reveal.getAnimStyle(3)"
        >
          <img
            :src="SECTION3_BG"
            alt="Paciente sonriendo"
            class="w-full h-full object-cover"
          >
          <div class="absolute bottom-3 left-3 right-3 md:bottom-5 md:left-5 md:right-5 flex gap-1.5 md:gap-2">
            <!-- Overlay Card 1 -->
            <div class="flex-1 bg-white rounded-xl md:rounded-2xl p-3 md:p-5 flex flex-col justify-between h-36 md:h-52">
              <h4 class="text-lg md:text-2xl font-bold text-black leading-5 md:leading-7 uppercase">
                El Proceso de<br>Instalación de<br>Implantes
              </h4>
              <div class="self-end w-9 h-9 md:w-12 md:h-12 rounded-full border border-black flex items-center justify-center">
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  class="rotate-[-45deg]"
                >
                  <path
                    d="M1 7h12m0 0L8 2m5 5L8 12"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </div>
            </div>
            <!-- Overlay Card 2 -->
            <div class="flex-1 bg-white/20 backdrop-blur-xl rounded-xl md:rounded-2xl p-3 md:p-5 flex flex-col justify-between h-36 md:h-52">
              <h4 class="text-lg md:text-2xl font-bold text-white leading-5 md:leading-7 uppercase">
                Cuidados para<br>tus Implantes<br>Dentales
              </h4>
              <div class="self-end w-9 h-9 md:w-12 md:h-12 rounded-full border border-white flex items-center justify-center text-white">
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  class="rotate-[-45deg]"
                >
                  <path
                    d="M1 7h12m0 0L8 2m5 5L8 12"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
