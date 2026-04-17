/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  export the shared auth contract seam from one stable package entrypoint

- Later Extension Points:
  --> add new barrel exports only when governed auth contract files become public shared surfaces

- Role:
  --> centralizes auth contract exports under one package boundary
  --> keeps future auth consumers from importing deep file paths by default

- Exports:
  --> auth contract barrel exports

- Consumed By:
  --> future web extension and API auth code consuming shared contract types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- auth contract exports ----------
// Purpose: expose the provider-neutral auth contract surface from one stable package entrypoint.
export * from "./adapters.js";
export * from "./errors.js";
export * from "./identity.js";
export * from "./methods.js";
export * from "./requests.js";
export * from "./session.js";
