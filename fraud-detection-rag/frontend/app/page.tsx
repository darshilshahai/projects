import {
  CtaSection,
  FeaturesSection,
  HeroSection,
  LandingFooter,
  SecuritySection,
  WorkflowSection,
} from "@/components/landing/landing-sections";
import { LandingNav } from "@/components/landing/landing-nav";

export default function HomePage() {
  return (
    <>
      <LandingNav />
      <main>
        <HeroSection />
        <FeaturesSection />
        <WorkflowSection />
        <SecuritySection />
        <CtaSection />
      </main>
      <LandingFooter />
    </>
  );
}
