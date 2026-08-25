<script setup lang="ts">
/**
 * Platform operator: list clinics and provision a new customer clinic
 * (clinic + first admin). Visible only with platform.clinics.provision.
 */
import type { ApiResponse, PaginatedResponse } from '~/types'
import { PERMISSIONS } from '~/config/permissions'

interface PlatformClinic {
  id: string
  name: string
  tax_id: string
  timezone: string
  currency: string
  created_at: string
}

interface ProvisionResult {
  clinic: PlatformClinic
  admin: {
    id: string
    email: string
    first_name: string
    last_name: string
  }
}

const { t } = useI18n()
const api = useApi()
const toast = useToast()
const { can } = usePermissions()

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const clinics = ref<PlatformClinic[]>([])
const isLoading = ref(false)
const loadError = ref(false)

const showCreate = ref(false)
const isCreating = ref(false)
const formError = ref('')
const form = reactive({
  clinicName: '',
  taxId: '',
  timezone: 'Europe/Madrid',
  currency: 'EUR',
  adminFirstName: '',
  adminLastName: '',
  adminEmail: '',
  adminPassword: ''
})
const fieldErrors = reactive<Record<string, string>>({})

const lastProvisioned = ref<ProvisionResult | null>(null)

async function fetchClinics() {
  if (!can(PERMISSIONS.platform.clinicsProvision)) return
  isLoading.value = true
  loadError.value = false
  try {
    const res = await api.get<PaginatedResponse<PlatformClinic>>('/api/v1/auth/platform/clinics')
    clinics.value = res.data ?? []
  } catch {
    loadError.value = true
  } finally {
    isLoading.value = false
  }
}

function resetForm() {
  form.clinicName = ''
  form.taxId = ''
  form.timezone = 'Europe/Madrid'
  form.currency = 'EUR'
  form.adminFirstName = ''
  form.adminLastName = ''
  form.adminEmail = ''
  form.adminPassword = ''
  formError.value = ''
  for (const k of Object.keys(fieldErrors)) fieldErrors[k] = ''
}

function openCreate() {
  resetForm()
  lastProvisioned.value = null
  showCreate.value = true
}

function validate(): boolean {
  for (const k of Object.keys(fieldErrors)) fieldErrors[k] = ''

  if (!form.clinicName.trim()) fieldErrors.clinicName = t('settings.platform.clinicNameRequired')
  if (!form.taxId.trim()) fieldErrors.taxId = t('settings.platform.taxIdRequired')
  if (!form.adminFirstName.trim()) fieldErrors.adminFirstName = t('settings.platform.firstNameRequired')
  if (!form.adminLastName.trim()) fieldErrors.adminLastName = t('settings.platform.lastNameRequired')

  const email = form.adminEmail.trim()
  if (!email) fieldErrors.adminEmail = t('settings.platform.emailRequired')
  else if (!EMAIL_RE.test(email)) fieldErrors.adminEmail = t('settings.platform.emailInvalid')

  if (!form.adminPassword) fieldErrors.adminPassword = t('settings.platform.passwordRequired')
  else if (form.adminPassword.length < 8) fieldErrors.adminPassword = t('settings.platform.passwordTooShort')
  else if (!/[a-zA-Z]/.test(form.adminPassword) || !/\d/.test(form.adminPassword)) {
    fieldErrors.adminPassword = t('settings.platform.passwordWeak')
  }

  return Object.values(fieldErrors).every(v => !v)
}

async function onSubmit() {
  formError.value = ''
  if (!validate()) return

  isCreating.value = true
  try {
    const res = await api.post<ApiResponse<ProvisionResult>>('/api/v1/auth/platform/clinics', {
      clinic_name: form.clinicName.trim(),
      clinic_tax_id: form.taxId.trim(),
      timezone: form.timezone,
      currency: form.currency,
      admin_first_name: form.adminFirstName.trim(),
      admin_last_name: form.adminLastName.trim(),
      admin_email: form.adminEmail.trim(),
      admin_password: form.adminPassword
    })
    lastProvisioned.value = res.data
    showCreate.value = false
    toast.add({ title: t('settings.platform.created'), color: 'success' })
    await fetchClinics()
  } catch (err: unknown) {
    const status = (err as { statusCode?: number }).statusCode
    if (status === 409) formError.value = t('settings.platform.emailTaken')
    else if (status === 422) formError.value = t('settings.platform.passwordWeak')
    else formError.value = t('settings.platform.createError')
  } finally {
    isCreating.value = false
  }
}

onMounted(() => {
  fetchClinics()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
      <div>
        <h2 class="text-h2 text-default">
          {{ t('settings.platform.title') }}
        </h2>
        <p class="text-body text-muted mt-1">
          {{ t('settings.platform.description') }}
        </p>
      </div>
      <UButton
        color="primary"
        variant="soft"
        icon="i-lucide-building-2"
        @click="openCreate"
      >
        {{ t('settings.platform.create') }}
      </UButton>
    </div>

    <UAlert
      v-if="lastProvisioned"
      color="success"
      variant="subtle"
      icon="i-lucide-check-circle"
      :title="t('settings.platform.successTitle')"
      :description="t('settings.platform.successBody', {
        clinic: lastProvisioned.clinic.name,
        email: lastProvisioned.admin.email
      })"
    />

    <UCard>
      <div
        v-if="isLoading"
        class="space-y-3"
      >
        <USkeleton class="h-10 w-full" />
        <USkeleton class="h-10 w-full" />
      </div>

      <EmptyState
        v-else-if="loadError"
        icon="i-lucide-alert-circle"
        :title="t('settings.platform.loadError')"
        :description="t('settings.loadError.description')"
      />

      <EmptyState
        v-else-if="clinics.length === 0"
        icon="i-lucide-building"
        :title="t('settings.platform.empty')"
        :description="t('settings.platform.emptyHint')"
      />

      <ul
        v-else
        class="divide-y divide-default"
      >
        <li
          v-for="clinic in clinics"
          :key="clinic.id"
          class="py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1"
        >
          <div>
            <p class="text-body font-medium text-default">
              {{ clinic.name }}
            </p>
            <p class="text-caption text-muted">
              {{ clinic.tax_id }} · {{ clinic.timezone }} · {{ clinic.currency }}
            </p>
          </div>
          <p
            v-if="clinic.created_at"
            class="text-caption text-subtle"
          >
            {{ new Date(clinic.created_at).toLocaleDateString() }}
          </p>
        </li>
      </ul>
    </UCard>

    <UModal v-model:open="showCreate">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-building-2"
                class="w-5 h-5 text-primary-accent"
              />
              <h3 class="font-semibold text-default">
                {{ t('settings.platform.createTitle') }}
              </h3>
            </div>
          </template>

          <form
            class="space-y-4"
            @submit.prevent="onSubmit"
          >
            <div
              v-if="formError"
              class="alert-surface-danger rounded-token-md px-3 py-2 text-body"
              role="alert"
            >
              {{ formError }}
            </div>

            <p class="text-caption text-muted">
              {{ t('settings.platform.createHint') }}
            </p>

            <UFormField
              :label="t('settings.platform.clinicName')"
              :error="fieldErrors.clinicName || undefined"
            >
              <UInput
                v-model="form.clinicName"
                class="w-full"
                :disabled="isCreating"
              />
            </UFormField>

            <UFormField
              :label="t('settings.platform.taxId')"
              :error="fieldErrors.taxId || undefined"
            >
              <UInput
                v-model="form.taxId"
                class="w-full"
                :disabled="isCreating"
              />
            </UFormField>

            <div class="border-t border-default pt-4">
              <p class="text-caption font-medium text-default mb-3">
                {{ t('settings.platform.adminSection') }}
              </p>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField
                  :label="t('settings.platform.firstName')"
                  :error="fieldErrors.adminFirstName || undefined"
                >
                  <UInput
                    v-model="form.adminFirstName"
                    class="w-full"
                    :disabled="isCreating"
                  />
                </UFormField>
                <UFormField
                  :label="t('settings.platform.lastName')"
                  :error="fieldErrors.adminLastName || undefined"
                >
                  <UInput
                    v-model="form.adminLastName"
                    class="w-full"
                    :disabled="isCreating"
                  />
                </UFormField>
              </div>
              <UFormField
                class="mt-4"
                :label="t('settings.platform.email')"
                :error="fieldErrors.adminEmail || undefined"
              >
                <UInput
                  v-model="form.adminEmail"
                  type="email"
                  class="w-full"
                  :disabled="isCreating"
                />
              </UFormField>
              <UFormField
                class="mt-4"
                :label="t('settings.platform.password')"
                :error="fieldErrors.adminPassword || undefined"
                :help="t('settings.platform.passwordHint')"
              >
                <UInput
                  v-model="form.adminPassword"
                  type="password"
                  class="w-full"
                  autocomplete="new-password"
                  :disabled="isCreating"
                />
              </UFormField>
            </div>

            <div class="flex justify-end gap-2 pt-2">
              <UButton
                color="neutral"
                variant="ghost"
                :disabled="isCreating"
                @click="showCreate = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                type="submit"
                color="primary"
                variant="soft"
                :loading="isCreating"
                :disabled="isCreating"
              >
                {{ t('settings.platform.submit') }}
              </UButton>
            </div>
          </form>
        </UCard>
      </template>
    </UModal>
  </div>
</template>
