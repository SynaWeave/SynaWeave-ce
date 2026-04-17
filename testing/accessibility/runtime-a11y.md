# Runtime accessibility baseline

Use this file as the manual baseline checklist until the repo wires automated browser accessibility coverage.

Current proven scope:

- focus order reaches every interactive control in `apps/web/index.html`
- focus order reaches every interactive control in `apps/extension/popup.html`
- color contrast stays readable against the dark shell surfaces
- signed-out and signed-in states remain understandable without color alone

Not yet proven here:

- automated Playwright plus Axe coverage
- screen-reader walkthrough evidence across both browser surfaces
