import { ImageResponse } from "next/og";

export const alt = "Metis — Study with your documents";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          background: "linear-gradient(160deg, #0d0f12 0%, #16181d 55%, #0d0f12 100%)",
          color: "#ededed",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div
            style={{
              display: "flex",
              width: 76,
              height: 76,
              borderRadius: 18,
              background: "#2563eb",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg width="44" height="44" viewBox="0 0 32 32" fill="none">
              <path
                d="M8 23V9.5L16 17l8-7.5V23"
                stroke="#ffffff"
                strokeWidth="2.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div style={{ display: "flex", fontSize: 76, fontWeight: 700, letterSpacing: -2 }}>
            Metis
          </div>
        </div>
        <div style={{ display: "flex", marginTop: 28, fontSize: 32, color: "#9ca3af", maxWidth: 900 }}>
          Study with your documents — ask questions, get tutor-style
          explanations, and prepare for exams with retrieval-augmented AI.
        </div>
      </div>
    ),
    { ...size }
  );
}
