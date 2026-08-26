<script setup lang="ts">
/**
 * Platform operator SaaS subscription dashboard (Culqi settlements).
 */
import type { ApiResponse } from '~/types'
import { PERMISSIONS } from '~/config/permissions'

definePageMeta({
  layout: 'platform'
})

interface FeeDefaults {
  fee_percent: number
  fee_fixed_cents: number
  igv_percent: number
  period_days: number
  grace_days: number
}

interface ClinicRow {
  clinic_id: string
  clinic_name: string
  status: string
  subscription_price_cents: number | null
  subscription_period_ends_at: string | null
  access_state: string
  payments_count: number
  paid_total_cents: number
  net_total_cents: number
  currency: string
}

interface RecentPayment {
  id: string
  clinic_id: string
  amount_cents: number
  currency: string
  method: string
  culqi_fee_cents: number
  sunat_igv_cents: number
  net_cents: number
  paid_at: string | null
  period_end: string | null
}

interface DashboardData {
  totals: {
    payments_count: number
    amount_cents: number
    culqi_fee_cents: number
    sunat_igv_cents: number
    net_cents: number
    currency: string
  }
  clinics: ClinicRow[]
  recent_payments: RecentPayment[]
  fee_defaults: FeeDefaults
}

const { t } = useI18n()
const api = useApi()
const { can } = usePermissions()

const data = ref<DashboardData | null>(null)
const isLoading = ref(false)
const loadError = ref(false)

function soles(cents: number | null | undefined): string {
  const v = (cents ?? 0) / 100
  return new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' }).format(v)
}

function accessLabel(state: string): string {
  return t(`platform.subscription.access.${state}`, state)
}

async function load() {
  if (!can(PERMISSIONS.platform.clinicsProvision)) return
  isLoading.value = true
  loadError.value = false
  try {
    const res = await api.get<ApiResponse<DashboardData>>('/api/v1/subscriptions/dashboard')
    data.value = res.data
  } catch {
    loadError.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-h1 text-default">
        {{ t('platform.subscription.dashboardTitle') }}
      </h1>
      <p class="text-body text-muted mt-1">
        {{ t('platform.subscription.dashboardDescription') }}
      </p>
    </div>

    <div
      v-if="isLoading"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"
    >
      <USkeleton
        v-for="i in 4"
        :key="i"
        class="h-24 w-full"
      />
    </div>

    <EmptyState
      v-else-if="loadError"
      icon="i-lucide-alert-circle"
      :title="t('platform.subscription.loadError')"
      :description="t('settings.loadError.description')"
    />

    <template v-else-if="data">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <UCard>
          <p class="text-caption text-muted">
            {{ t('platform.subscription.totalCollected') }}
          </p>
          <p class="text-h2 text-default mt-1">
            {{ soles(data.totals.amount_cents) }}
          </p>
          <p class="text-caption text-subtle">
            {{ data.totals.payments_count }} {{ t('platform.subscription.payments') }}
          </p>
        </UCard>
        <UCard>
          <p class="text-caption text-muted">
            {{ t('platform.subscription.totalCulqi') }}
          </p>
          <p class="text-h2 text-default mt-1">
            {{ soles(data.totals.culqi_fee_cents) }}
          </p>
        </UCard>
        <UCard>
          <p class="text-caption text-muted">
            {{ t('platform.subscription.totalSunat') }}
          </p>
          <p class="text-h2 text-default mt-1">
            {{ soles(data.totals.sunat_igv_cents) }}
          </p>
        </UCard>
        <UCard>
          <p class="text-caption text-muted">
            {{ t('platform.subscription.totalNet') }}
          </p>
          <p class="text-h2 text-success mt-1">
            {{ soles(data.totals.net_cents) }}
          </p>
        </UCard>
      </div>

      <UCard>
        <h2 class="text-h2 text-default mb-4">
          {{ t('platform.subscription.byClinic') }}
        </h2>
        <ul class="divide-y divide-default">
          <li
            v-for="row in data.clinics"
            :key="row.clinic_id"
            class="py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
          >
            <div>
              <p class="text-body font-medium text-default">
                {{ row.clinic_name }}
              </p>
              <p class="text-caption text-muted">
                {{ t('platform.subscription.price') }}:
                {{ row.subscription_price_cents != null ? soles(row.subscription_price_cents) : '—' }}
                · {{ accessLabel(row.access_state) }}
              </p>
              <p
                v-if="row.subscription_period_ends_at"
                class="text-caption text-subtle"
              >
                {{ t('platform.subscription.periodEnds') }}:
                {{ new Date(row.subscription_period_ends_at).toLocaleDateString('es-PE') }}
              </p>
            </div>
            <div class="text-right">
              <p class="text-body text-default">
                {{ soles(row.paid_total_cents) }}
              </p>
              <p class="text-caption text-muted">
                {{ t('platform.subscription.net') }}: {{ soles(row.net_total_cents) }}
              </p>
            </div>
          </li>
        </ul>
      </UCard>

      <UCard>
        <h2 class="text-h2 text-default mb-4">
          {{ t('platform.subscription.recent') }}
        </h2>
        <EmptyState
          v-if="data.recent_payments.length === 0"
          icon="i-lucide-wallet"
          :title="t('platform.subscription.noPayments')"
          :description="t('platform.subscription.noPaymentsHint')"
        />
        <ul
          v-else
          class="divide-y divide-default"
        >
          <li
            v-for="p in data.recent_payments"
            :key="p.id"
            class="py-3 flex flex-col sm:flex-row sm:justify-between gap-1"
          >
            <div>
              <p class="text-body text-default">
                {{ soles(p.amount_cents) }} · {{ p.method }}
              </p>
              <p class="text-caption text-muted">
                Culqi {{ soles(p.culqi_fee_cents) }} · SUNAT {{ soles(p.sunat_igv_cents) }} ·
                {{ t('platform.subscription.net') }} {{ soles(p.net_cents) }}
              </p>
            </div>
            <p class="text-caption text-subtle">
              {{ p.paid_at ? new Date(p.paid_at).toLocaleString('es-PE') : '' }}
            </p>
          </li>
        </ul>
      </UCard>
    </template>
  </div>
</template>
