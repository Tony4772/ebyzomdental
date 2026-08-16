export const STORAGE_KEYS = {
  LOCALE: 'ebyzomdental:locale',
  DENSITY: 'ui:density',
  onboardingDismissed: (clinicId: string) =>
    `ebyzomdental.settings.onboarding.dismissed:${clinicId}`
} as const
