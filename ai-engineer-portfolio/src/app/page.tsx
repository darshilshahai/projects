import { Navbar } from "@/components/layout/navbar";
import { LaunchLoader } from "@/components/layout/launch-loader";
import { Hero } from "@/components/sections/hero";
import { Statement } from "@/components/sections/about";
import { ExperienceSection } from "@/components/sections/experience";
import { ProjectsSection } from "@/components/sections/projects";
import { AiFocus } from "@/components/sections/ai-focus";
import { Principles } from "@/components/sections/principles";
import { ContactSection } from "@/components/sections/contact";

export default function HomePage() {
  return (
    <main id="main">
      <LaunchLoader home />
      <Navbar />
      <Hero />
      <Statement />
      <ProjectsSection />
      <ExperienceSection />
      <AiFocus />
      <Principles />
      <ContactSection />
    </main>
  );
}
