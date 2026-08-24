import { ImageResponse } from "next/og";
import { site } from "@/data/site";

export const alt = `${site.name} — ${site.role}`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#e4dfd6",
          padding: 72,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", color: "#6e6862", fontSize: 20 }}>
          <span>AI ENGINEER</span>
          <span style={{ color: "#ff3d00" }}>●</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", color: "#0f0e0d", fontSize: 72, letterSpacing: -3, lineHeight: 0.95 }}>
          <span>Darshil Shah</span>
          <span style={{ color: "#ff3d00" }}>Signal Studio</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", color: "#6e6862", fontSize: 22 }}>
          <span>{site.email}</span>
          <span>RAG · Agents · Backend</span>
        </div>
      </div>
    ),
    { ...size },
  );
}
