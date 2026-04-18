# Runtime accessibility baseline

Use this file as the manual baseline checklist alongside the automated Playwright plus Axe coverage.

Current proven scope:

- focus order reaches every interactive control in `apps/web/index.html`
- focus order reaches every interactive control in `apps/extension/popup.html`
- color contrast stays readable against the dark shell surfaces
- signed-out and signed-in states remain understandable without color alone
- automated Axe scans now cover the signed-in web shell and the packaged extension panel document

Not yet proven here:

- browser-controlled extension side-panel open and attach behavior in Chromium
- screen-reader walkthrough evidence across both browser surfaces
