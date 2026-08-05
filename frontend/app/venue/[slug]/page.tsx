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
      <Link href="/results" className="text-sm text-muted hover:text-accent font-medium">
        ← Πίσω στα αποτελέσματα
      </Link>

      {venue.photos.length > 0 ? (
        <div className="relative">
          {/* eslint-disable-next-line @next/next/no-img-element -- external, unpredictable domains; not worth configuring next/image remotePatterns for */}
          <img
            src={venue.photos[0].url}
            alt={venue.name}
            className="w-full h-48 object-cover rounded-3xl border border-border"
          />
          {venue.photos[0].attribution && (
            <span className="absolute bottom-1.5 right-2.5 text-[10px] text-white/90 bg-black/40 rounded-full px-2 py-0.5">
              {venue.photos[0].attribution}
            </span>
          )}
        </div>
      ) : (
        <div className="w-full h-28 rounded-3xl bg-gradient-to-br from-accent/15 to-accent-2/25 border border-border flex items-center justify-center text-3xl">
          📍
        </div>
      )}

      <header>
        <h1 className="text-2xl font-extrabold text-foreground">{venue.name}</h1>
        {venue.description_short && (
          <p className="mt-1 text-sm text-muted">{venue.description_short}</p>
        )}
      </header>

      <div className="flex flex-wrap gap-2">
        {venue.tags.map((tag) => (
          <span
            key={tag.slug}
            className="text-xs font-semibold rounded-full border-2 border-border bg-card px-3 py-1 text-foreground"
          >
            {tag.name}
          </span>
        ))}
      </div>

      <dl className="grid grid-cols-1 gap-2 text-sm border-t border-border pt-4">
        {venue.address && <Row label="Διεύθυνση" value={venue.address} />}
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
        className="w-full text-center rounded-full bg-accent text-accent-foreground font-bold py-4 text-base shadow-xl shadow-accent/30"
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
      <dt className="text-muted">{label}</dt>
      <dd className="text-foreground text-right font-medium">{value}</dd>
    </div>
  );
}
