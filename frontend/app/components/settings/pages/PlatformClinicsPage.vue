<script setup lang="ts">
/**
 * Platform operator: list clinics, provision, edit, pause/block/delete/reactivate.
 */
import type { ApiResponse, PaginatedResponse } from '~/types'
import { PERMISSIONS } from '~/config/permissions'

type ClinicStatus = 'active' | 'paused' | 'blocked' | 'deleted'

interface PlatformClinic {
  id: string
  name: string
  tax_id: string
  timezone: string
  currency: string
  status: ClinicStatus
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
const updatingId = ref<string | null>(null)

const showCreate = ref(false)
const isCreating = ref(false)
const formError = ref('')
const form = reactive({
  clinicName: '',
  taxId: '',
  timezone: 'America/Lima',
  currency: 'PEN',
  adminFirstName: '',
  adminLastName: '',
  adminEmail: '',
  adminPassword: ''
})
const fieldErrors = reactive<Record<string, string>>({})

const showEdit = ref(false)
const isSavingEdit = ref(false)
const editError = ref('')
const editing = ref<PlatformClinic | null>(null)
const editForm = reactive({
  name: '',
  taxId: '',
  timezone: 'America/Lima',
  currency: 'PEN'
})
const editFieldErrors = reactive<Record<string, string>>({})

const showDelete = ref(false)
const isDeleting = ref(false)
const deleting = ref<PlatformClinic | null>(null)

const lastProvisioned = ref<ProvisionResult | null>(null)

function statusColor(status: ClinicStatus): 'success' | 'warning' | 'error' | 'neutral' {
  if (status === 'active') return 'success'
  if (status === 'paused') return 'warning'
  if (status === 'deleted') return 'neutral'
  return 'error'
}

function statusLabel(status: ClinicStatus): string {
  return t(`platform.status.${status}`)
}

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

async function updateStatus(clinic: PlatformClinic, status: ClinicStatus): Promise<boolean> {
  updatingId.value = clinic.id
  try {
    const res = await api.patch<ApiResponse<PlatformClinic>>(
      `/api/v1/auth/platform/clinics/${clinic.id}`,
      { status }
    )
    const idx = clinics.value.findIndex(c => c.id === clinic.id)
    if (idx >= 0 && res.data) {
      clinics.value[idx] = res.data
    }
    toast.add({ title: t('platform.statusUpdated'), color: 'success' })
    return true
  } catch {
    toast.add({ title: t('platform.statusUpdateError'), color: 'error' })
    return false
  } finally {
    updatingId.value = null
  }
}

function resetForm() {
  form.clinicName = ''
  form.taxId = ''
  form.timezone = 'America/Lima'
  form.currency = 'PEN'
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

function openEdit(clinic: PlatformClinic) {
  editing.value = clinic
  editForm.name = clinic.name
  editForm.taxId = clinic.tax_id
  editForm.timezone = clinic.timezone || 'America/Lima'
  editForm.currency = clinic.currency || 'PEN'
  editError.value = ''
  for (const k of Object.keys(editFieldErrors)) editFieldErrors[k] = ''
  showEdit.value = true
}

function validateEdit(): boolean {
  for (const k of Object.keys(editFieldErrors)) editFieldErrors[k] = ''
  if (!editForm.name.trim()) editFieldErrors.name = t('settings.platform.clinicNameRequired')
  if (!editForm.taxId.trim()) editFieldErrors.taxId = t('settings.platform.taxIdRequired')
  return Object.values(editFieldErrors).every(v => !v)
}

async function onSaveEdit() {
  if (!editing.value) return
  editError.value = ''
  if (!validateEdit()) return

  isSavingEdit.value = true
  try {
    const res = await api.patch<ApiResponse<PlatformClinic>>(
      `/api/v1/auth/platform/clinics/${editing.value.id}`,
      {
        name: editForm.name.trim(),
        tax_id: editForm.taxId.trim(),
        timezone: editForm.timezone,
        currency: editForm.currency
      }
    )
    const idx = clinics.value.findIndex(c => c.id === editing.value!.id)
    if (idx >= 0 && res.data) {
      clinics.value[idx] = res.data
    }
    showEdit.value = false
    toast.add({ title: t('platform.editSaved'), color: 'success' })
  } catch {
    editError.value = t('platform.editError')
  } finally {
    isSavingEdit.value = false
  }
}

function openDelete(clinic: PlatformClinic) {
  deleting.value = clinic
  showDelete.value = true
}

async function confirmDelete() {
  if (!deleting.value) return
  isDeleting.value = true
  try {
    const ok = await updateStatus(deleting.value, 'deleted')
    if (ok) {
      showDelete.value = false
      deleting.value = null
    }
  } finally {
    isDeleting.value = false
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
        <h1 class="text-h1 text-default">
          {{ t('platform.panelTitle') }}
        </h1>
        <p class="text-body text-muted mt-1">
          {{ t('platform.panelDescription') }}
        </p>
      </div>
      <UButton
        color="primary"
        icon="i-lucide-plus"
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
          class="py-4 flex flex-col gap-3"
        >
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <p class="text-body font-medium text-default">
                {{ clinic.name }}
              </p>
              <UBadge
                :color="statusColor(clinic.status ?? 'active')"
                variant="subtle"
                size="sm"
              >
                {{ statusLabel(clinic.status ?? 'active') }}
              </UBadge>
            </div>
            <p class="text-caption text-muted mt-0.5">
              {{ clinic.tax_id }} · {{ clinic.timezone }} · {{ clinic.currency }}
            </p>
            <p
              v-if="clinic.created_at"
              class="text-caption text-subtle mt-0.5"
            >
              {{ new Date(clinic.created_at).toLocaleDateString() }}
            </p>
          </div>

          <div class="flex flex-wrap gap-2">
            <UButton
              size="sm"
              color="neutral"
              variant="soft"
              icon="i-lucide-pencil"
              :disabled="updatingId === clinic.id || clinic.status === 'deleted'"
              @click="openEdit(clinic)"
            >
              {{ t('platform.actions.edit') }}
            </UButton>
            <UButton
              v-if="clinic.status === 'active'"
              size="sm"
              color="warning"
              variant="soft"
              icon="i-lucide-pause"
              :loading="updatingId === clinic.id"
              :disabled="updatingId === clinic.id"
              @click="updateStatus(clinic, 'paused')"
            >
              {{ t('platform.actions.pause') }}
            </UButton>
            <UButton
              v-if="clinic.status === 'active' || clinic.status === 'paused'"
              size="sm"
              color="error"
              variant="soft"
              icon="i-lucide-ban"
              :loading="updatingId === clinic.id"
              :disabled="updatingId === clinic.id"
              @click="updateStatus(clinic, 'blocked')"
            >
              {{ t('platform.actions.block') }}
            </UButton>
            <UButton
              v-if="clinic.status === 'paused' || clinic.status === 'blocked' || clinic.status === 'deleted'"
              size="sm"
              color="success"
              variant="soft"
              icon="i-lucide-play"
              :loading="updatingId === clinic.id"
              :disabled="updatingId === clinic.id"
              @click="updateStatus(clinic, 'active')"
            >
              {{ t('platform.actions.reactivate') }}
            </UButton>
            <UButton
              v-if="clinic.status !== 'deleted'"
              size="sm"
              color="error"
              variant="ghost"
              icon="i-lucide-trash-2"
              :disabled="updatingId === clinic.id"
              @click="openDelete(clinic)"
            >
              {{ t('platform.actions.delete') }}
            </UButton>
          </div>
        </li>
      </ul>
    </UCard>

    <!-- Create clinic -->
    <UModal
      v-model:open="showCreate"
      :title="t('settings.platform.createTitle')"
      :description="t('settings.platform.createHint')"
      :ui="{
        content: 'max-h-[90vh] flex flex-col sm:max-w-lg',
        body: 'overflow-y-auto'
      }"
    >
      <template #body>
        <form
          id="platform-create-clinic"
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
        </form>
      </template>

      <template #footer>
        <div class="flex justify-end gap-2 w-full">
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
            form="platform-create-clinic"
            color="primary"
            :loading="isCreating"
            :disabled="isCreating"
          >
            {{ t('settings.platform.submit') }}
          </UButton>
        </div>
      </template>
    </UModal>

    <!-- Edit clinic -->
    <UModal
      v-model:open="showEdit"
      :title="t('platform.editTitle')"
      :ui="{ content: 'sm:max-w-lg' }"
    >
      <template #body>
        <form
          id="platform-edit-clinic"
          class="space-y-4"
          @submit.prevent="onSaveEdit"
        >
          <div
            v-if="editError"
            class="alert-surface-danger rounded-token-md px-3 py-2 text-body"
            role="alert"
          >
            {{ editError }}
          </div>

          <UFormField
            :label="t('settings.platform.clinicName')"
            :error="editFieldErrors.name || undefined"
          >
            <UInput
              v-model="editForm.name"
              class="w-full"
              :disabled="isSavingEdit"
            />
          </UFormField>

          <UFormField
            :label="t('settings.platform.taxId')"
            :error="editFieldErrors.taxId || undefined"
          >
            <UInput
              v-model="editForm.taxId"
              class="w-full"
              :disabled="isSavingEdit"
            />
          </UFormField>

          <UFormField :label="t('platform.timezone')">
            <UInput
              v-model="editForm.timezone"
              class="w-full"
              :disabled="isSavingEdit"
            />
          </UFormField>

          <UFormField :label="t('platform.currency')">
            <UInput
              v-model="editForm.currency"
              class="w-full"
              :disabled="isSavingEdit"
            />
          </UFormField>
        </form>
      </template>

      <template #footer>
        <div class="flex justify-end gap-2 w-full">
          <UButton
            color="neutral"
            variant="ghost"
            :disabled="isSavingEdit"
            @click="showEdit = false"
          >
            {{ t('common.cancel') }}
          </UButton>
          <UButton
            type="submit"
            form="platform-edit-clinic"
            color="primary"
            :loading="isSavingEdit"
            :disabled="isSavingEdit"
          >
            {{ t('common.save') }}
          </UButton>
        </div>
      </template>
    </UModal>

    <!-- Delete (soft) confirmation -->
    <UModal
      v-model:open="showDelete"
      :title="t('platform.deleteTitle')"
      :ui="{ content: 'sm:max-w-md' }"
    >
      <template #body>
        <p class="text-body text-muted">
          {{ t('platform.deleteConfirm', { clinic: deleting?.name ?? '' }) }}
        </p>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2 w-full">
          <UButton
            color="neutral"
            variant="ghost"
            :disabled="isDeleting"
            @click="showDelete = false"
          >
            {{ t('common.cancel') }}
          </UButton>
          <UButton
            color="error"
            :loading="isDeleting"
            :disabled="isDeleting"
            @click="confirmDelete"
          >
            {{ t('platform.actions.delete') }}
          </UButton>
        </div>
      </template>
    </UModal>
  </div>
</template>
