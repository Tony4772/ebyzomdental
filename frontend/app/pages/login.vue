<script setup lang="ts">
import { PERMISSIONS } from '~/config/permissions'

definePageMeta({
  layout: 'auth'
})

const { t } = useI18n()
const auth = useAuth()
const toast = useToast()
const { can } = usePermissions()
const config = useRuntimeConfig()

const siteOrigin = computed(() => {
  const fromApi = String(config.public.apiBaseUrl || '').replace(/\/$/, '')
  if (fromApi && !fromApi.includes('localhost') && !fromApi.includes('onrender')) {
    return fromApi
  }
  if (import.meta.client) return window.location.origin
  return 'https://dental.ebyzom.com'
})

const ogImage = computed(() => `${siteOrigin.value}/og-image.png?v=2`)

useSeoMeta({
  title: () => t('seo.title'),
  description: () => t('seo.description'),
  ogTitle: () => t('seo.title'),
  ogDescription: () => t('seo.description'),
  ogImage: () => ogImage.value,
  ogImageAlt: () => t('seo.ogImageAlt'),
  ogType: 'website',
  ogUrl: () => `${siteOrigin.value}/login`,
  ogLocale: 'es_PE',
  twitterCard: 'summary_large_image',
  twitterTitle: () => t('seo.title'),
  twitterDescription: () => t('seo.description'),
  twitterImage: () => ogImage.value,
  robots: 'index, follow'
})

useHead({
  link: [
    { rel: 'canonical', href: () => `${siteOrigin.value}/login` }
  ]
})

const WHATSAPP_DISPLAY = '906 591 037'
const WHATSAPP_HREF = 'https://wa.me/51906591037'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const isLoading = ref(false)
const formState = reactive({
  email: '',
  password: ''
})
const errorMessage = ref('')
const emailError = ref('')
const passwordError = ref('')

function validate(): boolean {
  emailError.value = ''
  passwordError.value = ''

  const email = formState.email.trim()
  if (!email) {
    emailError.value = t('auth.emailRequired')
  } else if (!EMAIL_RE.test(email)) {
    emailError.value = t('auth.emailInvalid')
  }

  if (!formState.password) {
    passwordError.value = t('auth.passwordRequired')
  }

  return !emailError.value && !passwordError.value
}

function mapError(err: unknown): string {
  const e = err as {
    statusCode?: number
    status?: number
    message?: string
    data?: { message?: string }
  }
  const status = e.statusCode ?? e.status

  switch (status) {
    case 400:
    case 401:
      return t('auth.invalidCredentials')
    case 403:
      return t('auth.accountInactive')
    case 422:
      return t('auth.invalidCredentials')
    case 429:
      return t('auth.tooManyAttempts')
  }

  if (!status || status === 0 || (e.message && /network|fetch|failed/i.test(e.message))) {
    return t('auth.networkError')
  }
  if (status >= 500) {
    return t('auth.serverError')
  }
  return t('auth.unknownError')
}

async function onSubmit() {
  errorMessage.value = ''
  if (!validate()) return

  isLoading.value = true
  try {
    await auth.login({
      email: formState.email.trim(),
      password: formState.password
    })

    toast.add({
      title: t('auth.loginSuccess'),
      color: 'success'
    })

    const home = can(PERMISSIONS.platform.clinicsProvision)
      ? '/platform/clinics'
      : '/'
    await navigateTo(home)
  } catch (error: unknown) {
    console.error('Login error:', error)
    errorMessage.value = mapError(error)
  } finally {
    isLoading.value = false
  }
}

watch(() => formState.email, () => {
  if (emailError.value) emailError.value = ''
  if (errorMessage.value) errorMessage.value = ''
})
watch(() => formState.password, () => {
  if (passwordError.value) passwordError.value = ''
  if (errorMessage.value) errorMessage.value = ''
})
</script>

<template>
  <div class="min-h-[calc(100vh-0px)] grid lg:grid-cols-2">
    <!-- Left: brand hero -->
    <aside
      class="relative hidden lg:block min-h-screen overflow-hidden bg-[var(--color-primary)]"
      aria-hidden="true"
    >
      <img
        src="/login-hero.png"
        alt=""
        class="absolute inset-0 h-full w-full object-cover object-center"
        width="1200"
        height="1200"
      >
      <div class="absolute inset-0 bg-gradient-to-t from-black/35 via-transparent to-black/10" />
    </aside>

    <!-- Right: login form -->
    <section class="flex flex-col justify-center px-6 py-10 sm:px-10 lg:px-14 xl:px-20">
      <!-- Mobile hero strip -->
      <div class="lg:hidden mb-6 -mx-6 -mt-10 sm:-mx-10 bg-[var(--color-primary)]/5">
        <img
          src="/og-image.png"
          :alt="t('seo.ogImageAlt')"
          class="w-full h-auto max-h-44 object-contain object-center"
          width="1200"
          height="630"
        >
      </div>

      <div class="w-full max-w-[420px] mx-auto">
        <div class="mb-6">
          <img
            src="/logo-icon.svg"
            alt="EBYZOM Dental"
            width="48"
            height="48"
            class="mb-3"
          >
          <h1 class="text-h1 text-default">
            EBYZOM Dental
          </h1>
          <p class="text-body text-muted mt-1">
            {{ t('app.tagline') }}
          </p>
        </div>

        <UCard>
          <form
            class="space-y-4"
            @submit.prevent="onSubmit"
          >
            <div
              v-if="errorMessage"
              class="alert-surface-danger rounded-token-md px-3 py-2 flex items-start gap-2"
              role="alert"
            >
              <UIcon
                name="i-lucide-alert-circle"
                class="w-4 h-4 mt-0.5 shrink-0"
                :style="{ color: 'var(--color-danger-accent)' }"
              />
              <span class="text-body">
                {{ errorMessage }}
              </span>
            </div>

            <UFormField
              :label="t('auth.email')"
              name="email"
              :error="emailError || undefined"
            >
              <UInput
                v-model="formState.email"
                type="email"
                class="w-full"
                :placeholder="t('auth.email')"
                icon="i-lucide-mail"
                autocomplete="email"
                :disabled="isLoading"
              />
            </UFormField>

            <UFormField
              :label="t('auth.password')"
              name="password"
              :error="passwordError || undefined"
            >
              <UInput
                v-model="formState.password"
                type="password"
                class="w-full"
                :placeholder="t('auth.password')"
                icon="i-lucide-lock"
                autocomplete="current-password"
                :disabled="isLoading"
              />
            </UFormField>

            <UButton
              type="submit"
              color="primary"
              variant="soft"
              block
              :loading="isLoading"
              :disabled="isLoading"
            >
              {{ t('auth.loginButton') }}
            </UButton>
          </form>
        </UCard>

        <DemoCredentialsHint />

        <a
          :href="WHATSAPP_HREF"
          target="_blank"
          rel="noopener noreferrer"
          class="mt-5 flex items-center justify-center gap-2 text-body text-muted hover:text-default transition-colors"
        >
          <UIcon
            name="i-lucide-message-circle"
            class="w-4 h-4 shrink-0 text-[var(--color-primary-accent)]"
          />
          <span>
            {{ t('auth.whatsappContact', { phone: WHATSAPP_DISPLAY }) }}
          </span>
        </a>

        <p class="text-center text-caption text-subtle mt-6">
          &copy; {{ new Date().getFullYear() }} EBYZOM Dental
        </p>
      </div>
    </section>
  </div>
</template>
