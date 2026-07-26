/**
 * Grounding catalogue for the Cart-Completion Interceptor (edge case M4).
 *
 * The model may ONLY suggest an id that exists here. Any id it invents is
 * rejected server-side and replaced by a rules-based pick, so a hallucinated
 * product name can never reach the UI.
 *
 * Mirrors mvp/data/catalog.json — keep the two in sync.
 */

export interface CatalogItem {
  id: string;
  name: string;
  category: string;
  price_inr: number;
  tags: string[];
}

export const CATALOG: CatalogItem[] = [
  {
    id: "item_101",
    name: "Sony WH-1000XM5 Wireless Headphones",
    category: "Electronics",
    price_inr: 29990,
    tags: ["audio", "premium", "gift", "travel", "noise-cancelling"],
  },
  {
    id: "item_102",
    name: "Apple 20W USB-C Power Adapter",
    category: "Electronics",
    price_inr: 1900,
    tags: ["charger", "urgent", "phone", "accessory"],
  },
  {
    id: "item_201",
    name: "L'Oreal Paris Revitalift Hyaluronic Acid Serum",
    category: "Beauty & Personal Care",
    price_inr: 999,
    tags: ["skincare", "premium", "routine", "face"],
  },
  {
    id: "item_202",
    name: "Gillette Mach3 Turbo Razor",
    category: "Beauty & Personal Care",
    price_inr: 350,
    tags: ["grooming", "shaving", "routine", "men"],
  },
  {
    id: "item_301",
    name: "Pedigree Adult Dry Dog Food (Meat & Rice) 3kg",
    category: "Pet Care",
    price_inr: 700,
    tags: ["dog", "food", "routine", "pet"],
  },
  {
    id: "item_401",
    name: "UNO Card Game",
    category: "Toys & Games",
    price_inr: 149,
    tags: ["party", "game", "weekend", "kids", "friends"],
  },
  {
    id: "item_402",
    name: "Hot Wheels Diecast Car (Assorted)",
    category: "Toys & Games",
    price_inr: 179,
    tags: ["kids", "toy", "gift"],
  },
  {
    id: "item_501",
    name: "Duracell Ultra AA Alkaline Batteries (Pack of 4)",
    category: "Electronics",
    price_inr: 170,
    tags: ["urgent", "utility", "power", "household"],
  },
  {
    id: "item_601",
    name: "Durex Mutual Climax Condoms (Pack of 10)",
    category: "Pharmacy",
    price_inr: 350,
    tags: ["intimate", "night", "weekend", "urgent"],
  },
];

export const CATALOG_IDS = new Set(CATALOG.map((i) => i.id));

/** Compact catalogue block for the prompt — ids, names, categories, tags only. */
export const CATALOG_PROMPT_BLOCK = JSON.stringify(
  CATALOG.map(({ id, name, category, tags }) => ({ id, name, category, tags })),
);

/**
 * Deterministic fallback used when the model is unavailable or returns an id
 * that is not in the catalogue. Picks by time-of-day / weekend affinity so the
 * suggestion still feels contextual rather than random.
 */
export function rulesBasedPick(timeOfDay: string, dayOfWeek: string): CatalogItem {
  const hour = parseInt(timeOfDay.split(":")[0] ?? "12", 10);
  const isWeekend = /saturday|sunday/i.test(dayOfWeek);

  if (isWeekend && hour >= 17) {
    return CATALOG.find((i) => i.id === "item_401")!; // UNO — weekend evening
  }
  if (hour >= 21 || hour < 6) {
    return CATALOG.find((i) => i.id === "item_501")!; // Batteries — late-night utility
  }
  if (hour >= 6 && hour < 11) {
    return CATALOG.find((i) => i.id === "item_202")!; // Razor — morning routine
  }
  return CATALOG.find((i) => i.id === "item_201")!; // Serum — default self-care
}
