// Author independently expected routes from this service's contract and observed UI.
// Each step: {screen, heading or check, expectedButtons?, effect?: 'sign'|'send', run}.
// Hidden redirects: use plan.observedScreens instead of visible steps.
// outcome: {kind: 'sent'|'refused'|'probe'|'signing-only', heading or check, absentButtons?}.
export const cases = [];
