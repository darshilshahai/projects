"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { site } from "@/data/site";
import { useLocalTime } from "@/hooks/use-local-time";
import { magneticSpring, useMagnetic } from "@/hooks/use-magnetic";

const navLinks = [
  { href: "/work", label: "Work", match: ["/work", "/projects"] },
  { href: "/about", label: "About", match: ["/about"] },
  { href: "/contact", label: "Contact", match: ["/contact"] },
];

function NavLink({ href, label, active }: { href: string; label: string; active: boolean }) {
  const { offset, onPointerMove, onPointerLeave, reduceMotion } = useMagnetic(6);
  const [hovered, setHovered] = useState(false);

  return (
    <Link
      className={`magnetic-nav-link${active ? " is-active" : ""}`}
      href={href}
      aria-current={active ? "page" : undefined}
      onPointerEnter={() => setHovered(true)}
      onPointerMove={onPointerMove}
      onPointerLeave={() => {
        setHovered(false);
        onPointerLeave();
      }}
    >
      <motion.span animate={{ x: offset.x, y: offset.y }} transition={magneticSpring}>
        {label}
        {(active || hovered) && (
          <motion.i
            aria-hidden
            initial={reduceMotion ? false : { opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
          />
        )}
      </motion.span>
    </Link>
  );
}

export function Navbar({ variant = "light" }: { variant?: "light" | "dark" }) {
  const pathname = usePathname();
  const reduceMotion = useReducedMotion();
  const [scrolled, setScrolled] = useState(false);
  const [mobile, setMobile] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [menuHovered, setMenuHovered] = useState(false);
  const menuMagnet = useMagnetic(14);
  const closeMagnet = useMagnetic(14);

  useEffect(() => {
    const update = () => {
      setScrolled(window.scrollY > 48);
      setMobile(window.innerWidth < 900);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setMenuOpen(false);
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  const showFab = !menuOpen && mobile;
  const fabAtBottom = mobile && pathname === "/" && !scrolled;

  return (
    <>
      <header
        className={`nav-shell${scrolled ? " is-scrolled" : ""}${variant === "dark" ? " on-dark" : ""}`}
      >
        <a className="site-credit" href="/" aria-label="Darshil Shah home">
          <span className="site-credit-mark">●</span>
          <span className="site-credit-window" aria-hidden>
            <span className="site-credit-track">
              <span>Code by Darshil</span>
              <span>Darshil Shah</span>
            </span>
          </span>
        </a>
        <nav aria-label="Primary">
          {navLinks.map((link) => (
            <NavLink
              key={link.href}
              href={link.href}
              label={link.label}
              active={link.match.some((p) =>
                p === "/projects" ? pathname.startsWith("/projects") : pathname === p,
              )}
            />
          ))}
        </nav>
      </header>

      <AnimatePresence>
        {showFab ? (
          <motion.button
            className={`floating-menu-button${fabAtBottom ? " is-bottom" : ""}`}
            type="button"
            aria-label="Open menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen(true)}
            onPointerEnter={() => setMenuHovered(true)}
            onPointerMove={menuMagnet.onPointerMove}
            onPointerLeave={() => {
              setMenuHovered(false);
              menuMagnet.onPointerLeave();
            }}
            initial={reduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.5 }}
            animate={{
              opacity: 1,
              scale: 1,
              x: menuMagnet.offset.x,
              y: menuMagnet.offset.y,
              backgroundColor: menuHovered ? "#ff3d00" : "#0f0e0d",
            }}
            exit={{ opacity: 0, scale: 0.5 }}
            transition={{ x: magneticSpring, y: magneticSpring }}
          >
            <span className="menu-glyph" aria-hidden>
              <i /><i />
            </span>
          </motion.button>
        ) : null}
      </AnimatePresence>

      <AnimatePresence>
        {menuOpen ? (
          <motion.div
            className="drawer-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMenuOpen(false)}
          >
            <motion.aside
              className="menu-drawer"
              role="dialog"
              aria-modal
              aria-label="Menu"
              initial={reduceMotion ? { opacity: 0 } : { x: "100%" }}
              animate={{ x: 0, opacity: 1 }}
              exit={reduceMotion ? { opacity: 0 } : { x: "100%" }}
              transition={{ duration: 0.5, ease: [0.76, 0, 0.24, 1] }}
              onClick={(e) => e.stopPropagation()}
            >
              <motion.button
                className="drawer-close"
                type="button"
                aria-label="Close menu"
                onClick={() => setMenuOpen(false)}
                animate={{ x: closeMagnet.offset.x, y: closeMagnet.offset.y }}
                transition={magneticSpring}
                onPointerMove={closeMagnet.onPointerMove}
                onPointerLeave={closeMagnet.onPointerLeave}
              >
                <span /><span />
              </motion.button>
              <div className="drawer-nav-wrap">
                <p>Navigate</p>
                <nav>
                  <Link href="/" onClick={() => setMenuOpen(false)}>Home</Link>
                  {navLinks.map((l) => (
                    <Link key={l.href} href={l.href} onClick={() => setMenuOpen(false)}>
                      {l.label}
                    </Link>
                  ))}
                </nav>
              </div>
              <div className="drawer-socials">
                <p>Connect</p>
                <div className="drawer-social-links">
                  <a href={site.github} target="_blank" rel="noopener noreferrer">GitHub</a>
                  <a href={site.linkedin} target="_blank" rel="noopener noreferrer">LinkedIn</a>
                </div>
              </div>
            </motion.aside>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}

export function HeroStatus() {
  const time = useLocalTime();
  const ready = time !== "—";

  return (
    <div className="hero-status">
      {ready ? <strong suppressHydrationWarning>{time} IST</strong> : null}
      <span>{site.location}</span>
    </div>
  );
}
