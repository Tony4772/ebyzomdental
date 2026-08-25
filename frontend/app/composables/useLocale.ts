import { STORAGE_KEYS } from '~/constants/storage'
import type { CodeLang } from '~/types'

export function useLocale() {
  const { locale, setLocale, locales } = useI18n()

  // Español first — product default; other languages remain available.
  const availableLocales = computed(() => {
    const list = (locales.value as Array<{ code: CodeLang, name: string }>).map(l => ({
      code: l.code,
      name: l.name
    }))
    return [...list].sort((a, b) => {
      if (a.code === 'es') return -1
      if (b.code === 'es') return 1
      return a.name.localeCompare(b.name)
    })
  })

  async function changeLocale(code: CodeLang): Promise<void> {
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEYS.LOCALE, code)
    }
    await setLocale(code)
  }

  return {
    locale,
    currentLocale: computed(() => locale.value),
    availableLocales,
    changeLocale
  }
}
