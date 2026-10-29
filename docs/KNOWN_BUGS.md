# Known Bugs

## [Resolved] Cancellation signature is discarded
**Found:** 2026-10-18 | **Resolved:** 2026-10-29

When a repair is set to "Nicht Repariert" with detail "Abbruch", the customer signature from `AbbruchSignatureDialog.vue` is now sent to `POST /api/repairs/<id>/cancellation`, stamped onto the active cancellation PDF template (`data/cancellation.pdf` or `config/Cancellation_sample.pdf`) via `PDFSigner`, stored in `data/signed_cancellations/<id>.pdf`, and downloadable via `GET /api/repairs/<id>/cancellation`.
