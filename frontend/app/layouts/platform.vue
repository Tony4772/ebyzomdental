<script setup lang="ts">
/**
 * Layout for EBYZOM platform operators (system owners).
 * No clinic navigation, no clinic context — only platform administration.
 */
const { t } = useI18n()
const auth = useAuth()
const route = useRoute()

const navItems = [
  {
    to: '/platform/clinics',
    icon: 'i-lucide-building-2',
    labelKey: 'platform.nav.clinics'
  }
] as const

function isActive(to: string): boolean {
  return route.path === to || route.path.startsWith(`${to}/`)
}

async function handleLogout() {
  await auth.logout()
}
</script>

<template>
  <div class="min-h-screen flex bg-canvas">
    <aside class="hidden md:flex fixed inset-y-0 left-0 z-50 w-60 flex-col bg-surface-muted">
      <div class="flex items-center h-14 px-4 border-b border-subtle">
        <NuxtLink
          to="/platform/clinics"
          class="flex items-center gap-2 overflow-hidden"
          aria-label="EBYZOM Dental"
        >
          <img
            src="/logo-icon.svg"
            alt=""
            width="32"
            height="32"
            class="shrink-0"
          >
          <div class="min-w-0">
            <p class="text-h2 text-default truncate">
              EBYZOM Dental
            </p>
            <p class="text-caption text-subtle truncate">
              {{ t('platform.panelBadge') }}
            </p>
          </div>
        </NuxtLink>
      </div>

      <nav class="flex-1 px-2 py-3 space-y-1">
        <NuxtLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="group flex items-center gap-3 px-3 py-2 rounded-token-md text-ui transition-colors"
          :class="[
            isActive(item.to)
              ? 'bg-[var(--color-primary-soft)] text-[var(--color-primary-soft-text)]'
              : 'text-muted hover:bg-surface hover:text-default'
          ]"
        >
          <UIcon
            :name="item.icon"
            class="w-[18px] h-[18px] shrink-0"
          />
          <span class="truncate">{{ t(item.labelKey) }}</span>
        </NuxtLink>
      </nav>

      <div class="px-3 py-3 border-t border-subtle">
        <div
          v-if="auth.user.value"
          class="flex items-center gap-3"
        >
          <UAvatar
            :alt="auth.user.value.first_name"
            size="sm"
            class="shrink-0"
          />
          <div class="flex-1 min-w-0">
            <p class="text-ui text-default truncate">
              {{ auth.user.value.first_name }} {{ auth.user.value.last_name }}
            </p>
            <p class="text-caption text-subtle truncate">
              {{ auth.user.value.email }}
            </p>
          </div>
          <UButton
            variant="ghost"
            color="neutral"
            size="sm"
            icon="i-lucide-log-out"
            :aria-label="t('auth.logout')"
            @click="handleLogout"
          />
        </div>
      </div>
    </aside>

    <!-- Mobile header -->
    <div class="md:hidden fixed top-0 inset-x-0 z-40 h-14 flex items-center justify-between px-4 bg-surface-muted border-b border-subtle">
      <NuxtLink
        to="/platform/clinics"
        class="flex items-center gap-2"
      >
        <img
          src="/logo-icon.svg"
          alt=""
          width="28"
          height="28"
        >
        <span class="text-ui font-medium text-default">{{ t('platform.panelBadge') }}</span>
      </NuxtLink>
      <UButton
        variant="ghost"
        color="neutral"
        size="sm"
        icon="i-lucide-log-out"
        :aria-label="t('auth.logout')"
        @click="handleLogout"
      />
    </div>

    <main class="flex-1 md:ml-60 pt-14 md:pt-0">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <slot />
      </div>
    </main>
  </div>
</template>
