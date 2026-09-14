import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Metis — Study with your documents",
    short_name: "Metis",
    description:
      "Turn your documents into a study workspace — ask questions, get tutor-style explanations, and prepare for exams with retrieval-augmented AI.",
    start_url: "/",
    display: "standalone",
    background_color: "#f5f6f8",
    theme_color: "#2563eb",
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
      },
    ],
  };
}
