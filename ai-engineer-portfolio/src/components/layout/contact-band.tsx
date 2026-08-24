"use client";

import Link from "next/link";
import { site } from "@/data/site";
import { SiteFooter } from "@/components/layout/site-footer";
import { Reveal } from "@/components/motion/reveal";

export function ContactBand({ id = "contact" }: { id?: string }) {
  return (
    <section className="contact-band" id={id}>
      <div className="shell">
        <Reveal>
          <h2>Have a project in mind?</h2>
        </Reveal>
        <div className="contact-band-actions">
          <Link className="btn-ink" href="/contact">
            Start a conversation
          </Link>
          <a className="btn-outline-light" href={`mailto:${site.email}`}>
            {site.email}
          </a>
          <a className="btn-outline-light" href={site.linkedin} target="_blank" rel="noopener noreferrer">
            LinkedIn
          </a>
        </div>
        <SiteFooter />
      </div>
    </section>
  );
}
