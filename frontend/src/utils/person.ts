/** Anything with a name: users, customers, nested API objects. */
export interface NamedPerson {
  vorname?: string | null
  nachname?: string | null
  username?: string | null
}

/**
 * "Vorname Nachname", falling back to the username, then "–" (docs/STYLEGUIDE.md).
 * The only place names are put together.
 */
export function personName(person: NamedPerson | null | undefined): string {
  if (!person) return '–'
  const full = [person.vorname, person.nachname].filter(Boolean).join(' ')
  return full || person.username || '–'
}
