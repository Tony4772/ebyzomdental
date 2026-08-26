<script setup lang="ts">
import { fr, es, en, pt } from '@nuxt/ui/locale'

const { t, locale } = useI18n()

// @nuxt/ui does not ship a Tamil locale yet; fall back to English for
// built-in UI labels while vue-i18n still serves the app's ta messages.
const nuxtUILocales: Record<string, typeof en> = { en, fr, es, pt, ta: en }
const nuxtUILocale = computed(() => nuxtUILocales[locale.value] || en)

useHead(() => ({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: locale.value
  }
}))

useSeoMeta({
  title: () => t('seo.title'),
  description: () => t('seo.description'),
  ogTitle: () => t('seo.title'),
  ogDescription: () => t('seo.description'),
  ogImage: 'https://dental.ebyzom.com/og-image.png?v=3',
  ogImageAlt: () => t('seo.ogImageAlt'),
  ogType: 'website',
  ogSiteName: 'EBYZOM Dental',
  twitterCard: 'summary_large_image',
  twitterTitle: () => t('seo.title'),
  twitterDescription: () => t('seo.description'),
  twitterImage: 'https://dental.ebyzom.com/og-image.png?v=3'
})
</script>

<template>
  <UApp :locale="nuxtUILocale">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
