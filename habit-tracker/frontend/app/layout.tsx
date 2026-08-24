import type { Metadata } from "next";
import { IBM_Plex_Mono, Outfit } from "next/font/google";
import { HabitStoreProvider } from "@/context/habit-store";
import "./globals.css";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-ibm-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Habit Tracker",
  description: "Track daily habits with a minimal, focused dashboard.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${outfit.variable} ${ibmPlexMono.variable} h-full dark`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground antialiased">
        <HabitStoreProvider>{children}</HabitStoreProvider>
      </body>
    </html>
  );
}
