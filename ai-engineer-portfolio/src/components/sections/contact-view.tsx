"use client";

import { motion } from "framer-motion";
import { LaunchLoader } from "@/components/layout/launch-loader";
import { Navbar } from "@/components/layout/navbar";
import { SiteFooter } from "@/components/layout/site-footer";
import { ContactInquiryForm } from "@/components/sections/contact-inquiry-form";
import { site } from "@/data/site";

export function ContactView() {
  return (
    <main className="contact-page" id="main">
      <LaunchLoader words={["Contact"]} hold={900} />
      <Navbar variant="dark" />

      <div className="contact-page-shell">
        <motion.h1
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.85, delay: 0.75, ease: [0.22, 1, 0.36, 1] }}
        >
          Let&apos;s build something that holds up in production.
        </motion.h1>

        <div className="contact-page-grid">
          <ContactInquiryForm />
          <aside>
            <div>
              <p>Email</p>
              <a href={`mailto:${site.email}`}>{site.email}</a>
            </div>
            <div>
              <p>Location</p>
              <span>India · Remote worldwide</span>
            </div>
            <div>
              <p>Social</p>
              <a className="contact-social-link" href={site.github} target="_blank" rel="noopener noreferrer">
                GitHub
              </a>
              <a className="contact-social-link" href={site.linkedin} target="_blank" rel="noopener noreferrer">
                LinkedIn
              </a>
            </div>
            <div style={{ marginTop: 32 }}>
              <a className="btn-outline-light" href={site.resume}>
                Download resume
              </a>
            </div>
          </aside>
        </div>
        <SiteFooter />
      </div>
    </main>
  );
}
