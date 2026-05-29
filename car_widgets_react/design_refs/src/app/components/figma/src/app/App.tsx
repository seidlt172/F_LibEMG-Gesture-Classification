import { useState } from "react";
import Widget1Voice from "@/imports/Widget1Voice/Widget1Voice";
import Widget2Voice from "@/imports/Widget2Voice/Widget2Voice";
import Widget3Voice from "@/imports/Widget3Voice/Widget3Voice";
import Widget4Voice from "@/imports/Widget4Voice/Widget4Voice";
import Widget5Gesture from "@/imports/Widget5Gesture/Widget5Gesture";
import Widget6Gesture from "@/imports/Widget6Gesture/Widget6Gesture";
import Widget7Gesture from "@/imports/Widget7Gesture/Widget7Gesture";
import Widget8Gesture from "@/imports/Widget8Gesture/Widget8Gesture";
import Widget9VoiceAndGesture from "@/imports/Widget9VoiceAndGesture/Widget9VoiceAndGesture";
import Widget10VoiceAndGesture from "@/imports/Widget10VoiceAndGesture/Widget10VoiceAndGesture";
import Widget11VoiceAndGesture from "@/imports/Widget11VoiceAndGesture/Widget11VoiceAndGesture";
import Widget12VoiceAndGesture from "@/imports/Widget12VoiceAndGesture/Widget12VoiceAndGesture";

type Category = "all" | "voice" | "gesture" | "combined";

const CATEGORIES: { id: Category; label: string; accent: string }[] = [
  { id: "all", label: "All Widgets", accent: "#6b7280" },
  { id: "voice", label: "Voice", accent: "#3b82f6" },
  { id: "gesture", label: "Gesture", accent: "#7c3aed" },
  { id: "combined", label: "Voice + Gesture", accent: "#5b6fd4" },
];

interface WidgetEntry {
  id: string;
  label: string;
  category: Exclude<Category, "all">;
  component: React.ReactNode;
}

const WIDGETS: WidgetEntry[] = [
  {
    id: "w1",
    label: "Widget 1 · Musik",
    category: "voice",
    component: <Widget1Voice />,
  },
  {
    id: "w2",
    label: "Widget 2 · Anruf",
    category: "voice",
    component: <Widget2Voice />,
  },
  {
    id: "w3",
    label: "Widget 3 · Nachrichten",
    category: "voice",
    component: <Widget3Voice />,
  },
  {
    id: "w4",
    label: "Widget 4 · Navigation",
    category: "voice",
    component: <Widget4Voice />,
  },
  {
    id: "w5",
    label: "Widget 5 · Musik",
    category: "gesture",
    component: <Widget5Gesture />,
  },
  {
    id: "w6",
    label: "Widget 6 · Klima",
    category: "gesture",
    component: <Widget6Gesture />,
  },
  {
    id: "w7",
    label: "Widget 7 · Navigation",
    category: "gesture",
    component: <Widget7Gesture />,
  },
  {
    id: "w8",
    label: "Widget 8 · Ambiente",
    category: "gesture",
    component: <Widget8Gesture />,
  },
  {
    id: "w9",
    label: "Widget 9 · Navigation",
    category: "combined",
    component: <Widget9VoiceAndGesture />,
  },
  {
    id: "w10",
    label: "Widget 10 · Ambiente",
    category: "combined",
    component: <Widget10VoiceAndGesture />,
  },
  {
    id: "w11",
    label: "Widget 11 · Musik",
    category: "combined",
    component: <Widget11VoiceAndGesture />,
  },
  {
    id: "w12",
    label: "Widget 12 · Anruf",
    category: "combined",
    component: <Widget12VoiceAndGesture />,
  },
];

const CATEGORY_DOT: Record<Exclude<Category, "all">, string> = {
  voice: "#3b82f6",
  gesture: "#7c3aed",
  combined: "#5b6fd4",
};

function CategoryBadge({ cat }: { cat: Exclude<Category, "all"> }) {
  const labels: Record<typeof cat, string> = {
    voice: "Voice",
    gesture: "Gesture",
    combined: "Voice + Gesture",
  };
  return (
    <span
      className="inline-flex items-center gap-[4px] text-[9px] font-semibold uppercase tracking-[0.25px] px-[6px] py-[2px] rounded-full"
      style={{ background: CATEGORY_DOT[cat] + "22", color: CATEGORY_DOT[cat] }}
    >
      <span
        className="inline-block size-[5px] rounded-full"
        style={{ background: CATEGORY_DOT[cat] }}
      />
      {labels[cat]}
    </span>
  );
}

export default function App() {
  const [active, setActive] = useState<Category>("all");

  const visible =
    active === "all" ? WIDGETS : WIDGETS.filter((w) => w.category === active);

  return (
    <div className="min-h-screen w-full" style={{ background: "#181818", fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <div className="px-8 pt-8 pb-6 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <p
          className="text-[10px] font-semibold uppercase tracking-[0.25px] mb-1"
          style={{ color: "#6b7280" }}
        >
          HMI Research Prototype
        </p>
        <h1 className="text-[18px] font-bold text-white leading-tight">
          Automotive Widget System
        </h1>

        {/* Category tabs */}
        <div className="flex gap-2 mt-5">
          {CATEGORIES.map((cat) => {
            const isActive = active === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setActive(cat.id)}
                className="px-4 py-[6px] rounded-full text-[10px] font-semibold uppercase tracking-[0.25px] transition-colors"
                style={{
                  background: isActive ? cat.accent : "rgba(255,255,255,0.05)",
                  color: isActive ? "#fff" : "#6b7280",
                  border: "1px solid",
                  borderColor: isActive ? cat.accent : "rgba(255,255,255,0.08)",
                }}
              >
                {cat.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Widget grid */}
      <div className="p-8">
        <div
          className="grid gap-4"
          style={{
            gridTemplateColumns: "repeat(auto-fill, minmax(178px, 178px))",
          }}
        >
          {visible.map((widget) => (
            <div key={widget.id} className="flex flex-col gap-2">
              {/* Widget card — fixed size to preserve automotive proportions */}
              <div
                className="rounded-2xl overflow-hidden"
                style={{ width: 178, height: 204 }}
              >
                <div className="size-full">
                  {widget.component}
                </div>
              </div>

              {/* Meta row */}
              <div className="flex items-center justify-between px-1">
                <span
                  className="text-[9px] font-medium"
                  style={{ color: "#4b5563" }}
                >
                  {widget.label}
                </span>
                <CategoryBadge cat={widget.category} />
              </div>
            </div>
          ))}
        </div>

        {visible.length === 0 && (
          <p className="text-[11px] text-[#4b5563] mt-4">No widgets in this category.</p>
        )}
      </div>
    </div>
  );
}
