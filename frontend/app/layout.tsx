import type { Metadata } from "next";
import "./globals.css";
import GenderThemeInit from "@/components/GenderThemeInit";

export const metadata: Metadata = {
  title: "Where to?",
  description: "Πού να πας τώρα στη Θεσσαλονίκη — γρήγορες, εξηγήσιμες προτάσεις βάσει context.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="el" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <GenderThemeInit />
        {children}
      </body>
    </html>
  );
}
