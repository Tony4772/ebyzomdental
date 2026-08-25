import { STORAGE_KEYS } from '~/constants/storage'
import type { Composer } from 'vue-i18n'
import type { CodeLang } from '~/types'
import { DEFAULT_LOCALE, SUPPORTED_LOCALES } from '~/constants/languages'

export default defineNuxtPlugin(async (nuxtApp) => {
  const i18n = nuxtApp.$i18n as Composer

  const savedLocale = localStorage.getItem(STORAGE_KEYS.LOCALE) as CodeLang | null

  if (savedLocale && SUPPORTED_LOCALES.includes(savedLocale)) {
    if (savedLocale !== i18n.locale.value) {
      await i18n.setLocale(savedLocale)
    }
    return
  }

  // No preference yet — Spanish is the product default for every clinic.
  if (i18n.locale.value !== DEFAULT_LOCALE) {
    await i18n.setLocale(DEFAULT_LOCALE)
  }
  localStorage.setItem(STORAGE_KEYS.LOCALE, DEFAULT_LOCALE)
})
