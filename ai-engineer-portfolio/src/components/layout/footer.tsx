export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="site-footer">
      <a className="monogram" href="#top">
        DS<span>.</span>
      </a>
      <p>AI Engineer · India</p>
      <p>© {year} · Built with Next.js + TypeScript</p>
      <a href="#top">
        Back to top
      </a>
    </footer>
  );
}
