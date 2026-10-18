# Known Bugs

## Cancellation signature is discarded
**Found:** 2026-10-18

When a repair is set to "Nicht Repariert" with detail "Abbruch", the customer must sign
in `AbbruchSignatureDialog.vue`. `confirmAbbruchSignature` in
`frontend/src/composables/useRepairStatusTransition.ts` receives the signature
(`_signaturePayload`) but never sends it anywhere; the backend has no field or endpoint for it.
The customer signs, but nothing is stored.

**To decide:** store it as a `RepairAttachment` (e.g. a new attachment type) or render it into
a PDF like the liability waiver.
