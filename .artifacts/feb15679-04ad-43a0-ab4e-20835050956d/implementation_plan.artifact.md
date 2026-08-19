# Implementation Plan - Modern Landing Page

Add a modern, eye-catching landing page to the EBYZOM Dental project based on the provided design specifications. Although the specifications were written for React, I will translate them to Vue/Nuxt 3 to maintain consistency with the existing project architecture.

## User Review Required

> [!IMPORTANT]
> **Route Changes:** The current dashboard (Home) will be moved from `/` to `/dashboard`. All staff members will need to use `/dashboard` or the sidebar links. The landing page will now occupy the root `/` URL.
> **Public Access:** The landing page will be publicly accessible without login.

## Proposed Changes

### Infrastructure & Integration

#### [MODIFY] [auth.global.ts](file:///D:/AndroidStudioProjects/EBYZOM Dental/frontend/app/middleware/auth.global.ts)
- Add `/` to `publicRoutes` to allow unauthenticated access to the landing page.
- Update redirects for authenticated users to point to `/dashboard` instead of `/`.

#### [MODIFY] [useModules.ts](file:///D:/AndroidStudioProjects/EBYZOM Dental/frontend/app/composables/useModules.ts)
- Update `HOST_NAV` to point the Dashboard entry to `/dashboard`.

#### [MODIFY] [app.vue](file:///D:/AndroidStudioProjects/EBYZOM Dental/frontend/app/app.vue)
- Add the "Open Sauce One" font links to the `<head>` section.

---

### New Landing Page Components

#### [NEW] [useMaskPositions.ts](file:///D:/AndroidStudioProjects/EBYZOM Dental/frontend/app/composables/useMaskPositions.ts)
- Composable to handle shared background image masking logic using `ResizeObserver`.

#### [NEW] [useImageWidth.ts](file:///D:/AndroidStudioProjects/EBYZOM Dental/frontend/app/composables/useImageWidth.ts)
- Composable to calculate the rendered width of images for the masking effect.

#### [NEW] [useStaggeredReveal.ts](file:///D:/AndroidStudioProjects/EBYZOM Dental/frontend/app/composables/useStaggeredReveal.ts)
- Composable for scroll-triggered staggered animations using `IntersectionObserver`.

#### [NEW] [MaskedCard.vue](file:///D:/AndroidStudioProjects/EBYZOM Dental/frontend/app/components/landing/MaskedCard.vue)
- Component for the windowed background image effect.

#### [NEW] [SplashScreen.vue](file:///D:/AndroidStudioProjects/EBYZOM Dental/frontend/app/components/landing/SplashScreen.vue)
- Initial loading screen with a counter.

#### [NEW] [LandingNavbar.vue](file:///D:/AndroidStudioProjects/EBYZOM Dental/frontend/app/components/landing/LandingNavbar.vue)
- Custom navigation bar for the landing page.

---

### Pages

#### [MODIFY] [index.vue](file:///D:/AndroidStudioProjects/EBYZOM Dental/frontend/app/pages/index.vue)
- Move the current dashboard code to `dashboard.vue`.
- Implement the three-section landing page design in `index.vue` using the new components.
- Use `definePageMeta({ layout: false })` to ensure the landing page has a custom full-screen design independent of the app's default layout.

#### [NEW] [dashboard.vue](file:///D:/AndroidStudioProjects/EBYZOM Dental/frontend/app/pages/dashboard.vue)
- The new home for the clinic management dashboard.

## Verification Plan

### Automated Tests
- Run `npm run typecheck` in the frontend to ensure no TS errors.
- (Optional) Add a basic E2E smoke test for the landing page.

### Manual Verification
1. Open the app at `/` and verify the splash screen appears and the landing page loads.
2. Verify the "DentalCare" hero and "Smile Gallery" effects work (masking).
3. Log in and verify redirection to `/dashboard`.
4. Check responsiveness on mobile and desktop widths.
