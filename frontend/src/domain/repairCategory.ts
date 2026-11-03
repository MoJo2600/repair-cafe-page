/*
 * Repair categories are settings (admins can add any); the placeholder image picks an
 * icon by keyword in the name and falls back to a generic toolbox.
 */
const CATEGORY_ICONS: Array<[RegExp, string]> = [
  [/audio|hifi|radio|musik|lautsprech/, 'mdi-speaker'],
  [/video|tv|fernseh|kamera/, 'mdi-television'],
  [/pc|computer|laptop|notebook|drucker|\bit\b/, 'mdi-laptop'],
  [/telekom|telefon|handy|smartphone|tablet/, 'mdi-cellphone'],
  [/fahrrad|bike|rad\b/, 'mdi-bicycle'],
  [/möbel|moebel|holz|stuhl|tisch/, 'mdi-sofa-outline'],
  [/textil|näh|naeh|kleid|stoff/, 'mdi-tshirt-crew-outline'],
  [/spielzeug|spiel/, 'mdi-teddy-bear'],
  [/schleif|schärf|schaerf|messer|werkzeug/, 'mdi-knife'],
  [/elektro|haushalt|küche|kueche|lampe|strom/, 'mdi-power-plug-outline'],
]

export const DEFAULT_CATEGORY_ICON = 'mdi-toolbox-outline'

export function categoryIcon(category: string | null | undefined): string {
  const name = (category ?? '').toLowerCase()
  return CATEGORY_ICONS.find(([pattern]) => pattern.test(name))?.[1] ?? DEFAULT_CATEGORY_ICON
}
