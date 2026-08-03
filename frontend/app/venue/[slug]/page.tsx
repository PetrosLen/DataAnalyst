import Link from "next/link";
import { notFound } from "next/navigation";
import { getVenue } from "@/lib/api";
import FeedbackWidget from "@/components/FeedbackWidget";

export default async function VenuePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const venue = await getVenue(slug);

  if (!venue) {
    notFound();
  }

  const mapsQuery = venue.address ?? venue.name;
  const directionsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    mapsQuery
  )}`;

  return (
    <main className="flex-1 flex flex-col mx-auto w-full max-w-md px-5 pt-6 pb-10 gap-5">
      <Link href="/results" className="text-sm text-neutral-400 hover:text-neutral-200">
        ← Πίσω στα αποτελέσματα
      </Link>

      <header>
        <h1 className="text-2xl font-bold text-neutral-50">{venue.name}</h1>
        {venue.description_short && (
          <p className="mt-1 text-sm text-neutral-400">{venue.description_short}</p>
        )}
      </header>

      <div className="flex flex-wrap gap-2">
        {venue.tags.map((tag) => (
          <span
            key={tag.slug}
            className="text-xs rounded-full border border-neutral-700 px-3 py-1 text-neutral-300"
          >
            {tag.name}
          </span>
        ))}
      </div>

      <dl className="grid grid-cols-1 gap-2 text-sm border-t border-neutral-800 pt-4">
        {venue.address && (
          <Row label="Διεύθυνση" value={venue.address} />
        )}
        {venue.phone && <Row label="Τηλέφωνο" value={venue.phone} />}
        {venue.price_level && <Row label="Budget" value={"€".repeat(venue.price_level)} />}
        <Row
          label="Confidence δεδομένων"
          value={`${Math.round(venue.overall_confidence * 100)}%`}
        />
      </dl>

      <a
        href={directionsUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="w-full text-center rounded-2xl bg-accent text-neutral-950 font-semibold py-4 text-base"
      >
        Οδηγίες
      </a>

      <FeedbackWidget venueSlug={venue.slug} />
    </main>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-neutral-500">{label}</dt>
      <dd className="text-neutral-200 text-right">{value}</dd>
    </div>
  );
}
