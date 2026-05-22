# Repair Status Model Documentation

This document defines the target status model for repairs and is the specification for the next implementation steps.

## Purpose

The repair flow should use:

1. One primary status field for the high-level state.
2. One secondary detail field for additional context about that state.

This keeps reporting simple while preserving detailed operational information.

## Canonical Fields

## Field 1: Primary Status

Allowed values (only these values are valid):

1. Offen
2. In Bearbeitung
3. Repariert
4. Nicht Repariert

Definition:

| Value | Meaning |
| --- | --- |
| Offen | New intake, not yet actively being worked on. |
| In Bearbeitung | Work in progress. |
| Repariert | Repair finished successfully. |
| Nicht Repariert | Repair process ended without a successful repair. |

## Field 2: Status Detail

The detail field adds structured context to the primary status.

Suggested field name for implementation planning: `status_detail`.

Rules:

1. `status_detail` should be nullable.
2. For `Offen`, `status_detail` should usually be empty.
3. For `In Bearbeitung`, `status_detail` may be empty or hold a progress qualifier.
4. For `Repariert`, `status_detail` may be empty or hold a successful outcome qualifier.
5. For `Nicht Repariert`, `status_detail` should be set and should explain the unsuccessful outcome.

## Initial Allowed Status Detail Values

This section defines the first approved values and can be expanded over time.

| Primary Status | Allowed `status_detail` values |
| --- | --- |
| Offen | (empty) |
| In Bearbeitung | (empty), Ersatzteilbesorgung |
| Repariert | (empty) |
| Nicht Repariert | Nicht moeglich, Abbruch, Wartezeit zu lang |

Note:

1. `Nicht moeglich` is written with `oe` in this document for ASCII safety in technical contexts. UI labels can still render `Nicht möglich`.

## Validation Matrix

Implementation should enforce the following:

| Primary Status | `status_detail` required? | Example |
| --- | --- | --- |
| Offen | No | `status=Offen`, `status_detail=null` |
| In Bearbeitung | No | `status=In Bearbeitung`, `status_detail=null` |
| Repariert | No | `status=Repariert`, `status_detail=null` |
| Nicht Repariert | Yes | `status=Nicht Repariert`, `status_detail=Nicht moeglich` |

## Extension Guide for Future Values

When adding new detail values later, update this document first.

Procedure:

1. Choose which primary status the new detail belongs to.
2. Add the value to the table in "Initial Allowed Status Detail Values".
3. Add one example to "Examples".
4. Update backend validation rules.
5. Update frontend dropdown/options.
6. Add or update tests for valid and invalid combinations.

Template for new detail values:

| Primary Status | New detail value | Description | Added on | Added by |
| --- | --- | --- | --- | --- |
| Nicht Repariert | <new_detail_value> | <short reason/meaning> | YYYY-MM-DD | <name> |

## Examples

1. Successful completion:
	`status=Repariert`, `status_detail=null`
2. Unsuccessful due to technical limitation:
	`status=Nicht Repariert`, `status_detail=Nicht moeglich`
3. Unsuccessful due to cancellation:
	`status=Nicht Repariert`, `status_detail=Abbruch`

## Out of Scope for This Document

This document defines behavior only. It does not implement:

1. Database migrations.
2. API schema changes.
3. UI form updates.
4. Data migration mapping from old values.

Those changes should be implemented in follow-up tasks based on this specification.
