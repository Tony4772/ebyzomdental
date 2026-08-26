<script setup lang="ts">
/**
 * Clinic admin: pay SaaS subscription via Culqi (card / Yape).
 */
import type { ApiResponse } from '~/types'

definePageMeta({
  layout: 'default'
})

interface ClinicSubscriptionStatus {
  clinic_id: string
  clinic_name: string
  price_cents: number | null
  currency: string
  period_ends_at: string | null
  access_state: string
  grace_days: number
  period_days: number
  culqi_public_key: string
}

const { t } = useI18n()
const api = useApi()
const toast = useToast()
const auth = useAuth()

const status = ref<ClinicSubscriptionStatus | null>(null)
const isLoading = ref(true)
const loadError = ref(false)
const isPaying = ref(false)
const payError = ref('')

function soles(cents: number | null | undefined): string {
  return new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' }).format((cents ?? 0) / 100)
}

async function load() {
  isLoading.value = true
  loadError.value = false
  try {
    const res = await api.get<ApiResponse<ClinicSubscriptionStatus>>('/api/v1/subscriptions/me')
    status.value = res.data
  } catch {
    loadError.value = true
  } finally {
    isLoading.value = false
  }
}

function loadCulqiScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof window !== 'undefined' && (window as unknown as { CulqiCheckout?: unknown }).CulqiCheckout) {
      resolve()
      return
    }
    const existing = document.querySelector('script[data-culqi-checkout]')
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('Culqi script failed')))
      return
    }
    const script = document.createElement('script')
    script.src = 'https://js.culqi.com/checkout-js'
    script.async = true
    script.dataset.culqiCheckout = '1'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Culqi script failed'))
    document.head.appendChild(script)
  })
}

async function startPayment() {
  if (!status.value?.price_cents || !status.value.culqi_public_key) {
    payError.value = t('platform.subscription.payNotConfigured')
    return
  }
  payError.value = ''
  isPaying.value = true
  try {
    await loadCulqiScript()
    const CulqiCheckout = (window as unknown as {
      CulqiCheckout: new (opts: Record<string, unknown>) => {
        open: () => void
        on: (event: string, cb: (payload: { id?: string; token?: string }) => void) => void
      }
    }).CulqiCheckout

    const email = auth.user.value?.email || ''
    const culqi = new CulqiCheckout({
      settings: {
        title: 'EBYZOM Dental',
        currency: status.value.currency || 'PEN',
        amount: status.value.price_cents
      },
      client: { email },
      options: {
        paymentMethods: {
          tarjeta: true,
          yape: true,
          billetera: false,
          bancaMovil: false,
          agente: false,
          cuotealo: false
        }
      },
      appearance: { theme: 'default' },
      publicKey: status.value.culqi_public_key
    })

    culqi.on('payment', async (payload) => {
      const sourceId = payload.id || payload.token
      if (!sourceId) {
        payError.value = t('platform.subscription.payFailed')
        isPaying.value = false
        return
      }
      try {
        const method = String(sourceId).startsWith('ype_') ? 'yape' : 'card'
        await api.post('/api/v1/subscriptions/me/pay', {
          source_id: sourceId,
          email,
          method
        })
        toast.add({ title: t('platform.subscription.paySuccess'), color: 'success' })
        await load()
        await navigateTo('/')
      } catch (err: unknown) {
        const detail = (err as { data?: { detail?: string }, message?: string }).data?.detail
          || (err as { message?: string }).message
        payError.value = detail || t('platform.subscription.payFailed')
      } finally {
        isPaying.value = false
      }
    })

    culqi.on('close', () => {
      isPaying.value = false
    })

    culqi.open()
  } catch {
    payError.value = t('platform.subscription.payFailed')
    isPaying.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="max-w-lg mx-auto space-y-6 py-6">
    <div>
      <h1 class="text-h1 text-default">
        {{ t('platform.subscription.payTitle') }}
      </h1>
      <p class="text-body text-muted mt-1">
        {{ t('platform.subscription.payDescription') }}
      </p>
    </div>

    <USkeleton
      v-if="isLoading"
      class="h-40 w-full"
    />

    <EmptyState
      v-else-if="loadError"
      icon="i-lucide-alert-circle"
      :title="t('platform.subscription.loadError')"
      :description="t('settings.loadError.description')"
    />

    <UCard v-else-if="status">
      <div class="space-y-3">
        <p class="text-body font-medium text-default">
          {{ status.clinic_name }}
        </p>
        <p class="text-caption text-muted">
          {{ t('platform.subscription.accessLabel') }}:
          {{ t(`platform.subscription.access.${status.access_state}`) }}
        </p>
        <p class="text-caption text-muted">
          {{ t('platform.subscription.periodEnds') }}:
          {{ status.period_ends_at
            ? new Date(status.period_ends_at).toLocaleDateString('es-PE')
            : '—' }}
        </p>
        <p class="text-h2 text-default">
          {{ status.price_cents != null ? soles(status.price_cents) : '—' }}
          <span class="text-caption text-muted font-normal">
            / {{ status.period_days }} {{ t('platform.subscription.days') }}
          </span>
        </p>
        <p class="text-caption text-subtle">
          {{ t('platform.subscription.graceHint', { days: status.grace_days }) }}
        </p>

        <div
          v-if="payError"
          class="alert-surface-danger rounded-token-md px-3 py-2 text-body"
          role="alert"
        >
          {{ payError }}
        </div>

        <UButton
          color="primary"
          block
          icon="i-lucide-credit-card"
          :loading="isPaying"
          :disabled="isPaying || !status.price_cents || !status.culqi_public_key"
          @click="startPayment"
        >
          {{ t('platform.subscription.payButton') }}
        </UButton>
        <p class="text-caption text-subtle text-center">
          {{ t('platform.subscription.payMethods') }}
        </p>
      </div>
    </UCard>
  </div>
</template>
