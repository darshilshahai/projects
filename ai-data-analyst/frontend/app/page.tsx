import {
  FinalCta,
  Hero,
  Navbar,
  ProductPreview,
  ProofSection,
  SystemFlow,
  TrustSection,
} from "@/components/landing";

export default function LandingPage() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <TrustSection />
        <SystemFlow />
        <ProofSection />
        <ProductPreview />
        <FinalCta />
      </main>
    </>
  );
}
