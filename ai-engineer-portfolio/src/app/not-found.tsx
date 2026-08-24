import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { ContactBand } from "@/components/layout/contact-band";

export default function NotFound() {
  return (
    <main id="main" className="writing-page">
      <Navbar />
      <div className="shell lost-shell">
        <p className="section-tag">
          <em>404</em> — Not found
        </p>
        <h1 className="display">This page doesn&apos;t exist.</h1>
        <p className="writing-lede">The route returned zero results. Try the homepage or reach out directly.</p>
        <Link className="btn-signal" href="/">
          Back home
        </Link>
      </div>
      <ContactBand />
    </main>
  );
}
