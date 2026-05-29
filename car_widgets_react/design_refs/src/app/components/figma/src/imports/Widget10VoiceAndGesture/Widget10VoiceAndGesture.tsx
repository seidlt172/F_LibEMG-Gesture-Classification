import { Palette, RotateCcw } from "lucide-react";

function WidgetTitle() {
  return (
    <div className="content-stretch flex h-[12.5px] items-start relative shrink-0 w-full">
      <p className="[word-break:break-word] flex-[1_0_0] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[12.5px] min-w-px not-italic relative text-[#99a1af] text-[10px] tracking-[0.25px] uppercase">
        Ambientebeleuchtung
      </p>
    </div>
  );
}

function RGBSlider() {
  return (
    <div className="content-stretch flex gap-[7.995px] items-center relative shrink-0 w-full">
      <Palette size={10} color="#99a1af" strokeWidth={1.5} className="shrink-0" />
      <div className="flex-1 relative h-[7.995px] rounded-[18641400px] overflow-hidden" style={{ background: "linear-gradient(to right, #ff0000, #ff8000, #ffff00, #00ff00, #0080ff, #8000ff, #ff00ff)" }}>
        <div
          className="absolute top-1/2 -translate-y-1/2 size-[10px] rounded-full bg-white shadow-[0px_2px_4px_rgba(0,0,0,0.3)] border border-white/60"
          style={{ left: "calc(38% - 5px)" }}
        />
      </div>
    </div>
  );
}

function BrightnessSlider() {
  return (
    <div className="content-stretch flex gap-[7.995px] items-center relative shrink-0 w-full">
      <Palette size={10} color="#99a1af" strokeWidth={1.5} className="shrink-0" />
      <div className="flex-1 relative h-[7.995px] rounded-[18641400px] overflow-hidden" style={{ background: "linear-gradient(to right, #ffffff, #22c55e)" }}>
        <div
          className="absolute top-1/2 -translate-y-1/2 size-[10px] rounded-full bg-white shadow-[0px_2px_4px_rgba(0,0,0,0.3)] border border-white/60"
          style={{ left: "calc(60% - 5px)" }}
        />
      </div>
    </div>
  );
}

function SwipeIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 11 11" fill="none" className="shrink-0">
      <path d="M4.5 1.5C4.5 1.5 4.5 4 4.5 5.5C4.5 7 5.5 9 7.5 9C9.5 9 10 7.5 10 6V4.5" stroke="#7BF1A8" strokeWidth="0.92" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M4.5 5.5C4.5 5.5 4.5 3 2.5 3C1.5 3 1 3.8 1 4.5V6C1 7.5 2 9.5 4.5 9.5" stroke="#7BF1A8" strokeWidth="0.92" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M7 4.5V2C7 1.5 7.5 1 8 1C8.5 1 9 1.5 9 2V4" stroke="#7BF1A8" strokeWidth="0.92" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M7 4C7 4 7 3 8 3C9 3 10 3.5 10 4.5" stroke="#7BF1A8" strokeWidth="0.92" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function GestureBadgeSwipe() {
  return (
    <div className="bg-[#1a3a2a] content-stretch flex gap-[5.998px] h-[23px] items-center pl-[7.995px] pr-[8px] py-[4px] relative rounded-[10px] shrink-0">
      <SwipeIcon />
      <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#7bf1a8] text-[10px] whitespace-nowrap">
        Swipe
      </p>
    </div>
  );
}

function GestureBadgeDrehen() {
  return (
    <div className="bg-[#1a3a2a] content-stretch flex gap-[5.998px] h-[23px] items-center pl-[7.995px] pr-[8px] py-[4px] relative rounded-[10px] shrink-0">
      <RotateCcw size={11} color="#7bf1a8" strokeWidth={1.5} className="shrink-0" />
      <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#7bf1a8] text-[10px] whitespace-nowrap">
        Drehen
      </p>
    </div>
  );
}

export default function Widget10VoiceAndGesture() {
  return (
    <div className="bg-[#252530] content-stretch flex flex-col items-start p-[16px] relative rounded-[16px] size-full" data-name="Widget 10 - Voice and Gesture">
      <div className="content-stretch flex flex-col h-[172.99px] items-start justify-between relative shrink-0 w-full">
        {/* Top content */}
        <div className="content-stretch flex flex-col gap-[8px] items-start relative shrink-0 w-full">
          <WidgetTitle />
          {/* Sliders panel */}
          <div className="bg-[#1e1e2e] content-stretch flex flex-col gap-[12px] items-start p-[9.998px] relative rounded-[14px] shrink-0 w-full">
            <RGBSlider />
            <BrightnessSlider />
          </div>
        </div>
        {/* Bottom gesture chips */}
        <div className="content-stretch flex flex-col gap-[4px] items-start relative shrink-0 w-full">
          <GestureBadgeSwipe />
          <GestureBadgeDrehen />
        </div>
      </div>
    </div>
  );
}
