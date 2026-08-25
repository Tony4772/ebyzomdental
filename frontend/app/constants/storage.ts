export const STORAGE_KEYS = {
  // v2: product default is Spanish; bump ignores stale `en` from early demos.
  LOCALE: 'dentalpin:locale:v2',
  DENSITY: 'ui:density',
  onboardingDismissed: (clinicId: string) =>
    `dentalpin.settings.onboarding.dismissed:${clinicId}`
} as const
