import { Phone, ThumbsUp, RotateCcw } from "lucide-react";

function WidgetTitle() {
  return (
    <div className="content-stretch flex h-[12.5px] items-start relative shrink-0 w-full">
      <p className="[word-break:break-word] flex-[1_0_0] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[12.5px] min-w-px not-italic relative text-[#99a1af] text-[10px] tracking-[0.25px] uppercase">
        Anruf
      </p>
    </div>
  );
}

function PhoneCircle() {
  return (
    <div className="bg-[#16a34a] relative rounded-[18641400px] shrink-0 size-[31.997px] flex items-center justify-center">
      <Phone size={14} color="white" fill="white" strokeWidth={1.5} />
    </div>
  );
}

function CallerInfo() {
  return (
    <div className="content-stretch flex gap-[7.995px] h-[31.997px] items-center relative shrink-0 w-full">
      <PhoneCircle />
      <div className="flex flex-col items-start">
        <p className="[word-break:break-word] font-['Inter:Bold',sans-serif] font-bold leading-[15px] not-italic text-[12px] text-white whitespace-nowrap">
          Max Mustermann
        </p>
        <p className="[word-break:break-word] font-['Inter:Regular',sans-serif] font-normal leading-[15px] not-italic text-[#99a1af] text-[10px] whitespace-nowrap">
          Eingehend
        </p>
      </div>
    </div>
  );
}

function ProgressBar() {
  return (
    <div className="content-stretch flex gap-[7.995px] h-[15px] items-center relative shrink-0 w-full">
      <div className="bg-[#353545] flex-1 h-[7.995px] relative rounded-[18641400px] overflow-hidden">
        <div className="bg-[#16a34a] h-full rounded-[18641400px]" style={{ width: "60%" }} />
      </div>
      <div className="h-[15px] relative shrink-0 w-[22.101px] flex items-start">
        <p className="[word-break:break-word] font-['Inter:Bold',sans-serif] font-bold leading-[15px] not-italic text-[#16a34a] text-[10px] whitespace-nowrap">
          60%
        </p>
      </div>
    </div>
  );
}

function GestureBadgeDaumen() {
  return (
    <div className="bg-[#1a3a2a] content-stretch flex gap-[5.998px] h-[23px] items-center pl-[7.995px] pr-[8px] py-[4px] relative rounded-[10px] shrink-0">
      <ThumbsUp size={11} color="#7bf1a8" strokeWidth={1.5} className="shrink-0" />
      <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#7bf1a8] text-[10px] whitespace-nowrap">
        Daumen hoch
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

export default function Widget12VoiceAndGesture() {
  return (
    <div className="bg-[#252530] content-stretch flex flex-col items-start p-[16px] relative rounded-[16px] size-full" data-name="Widget 12 - Voice and Gesture">
      <div className="content-stretch flex flex-col h-[172.99px] items-start justify-between relative shrink-0 w-full">
        {/* Top content */}
        <div className="content-stretch flex flex-col gap-[12px] items-start relative shrink-0 w-full">
          <div className="content-stretch flex flex-col gap-[8px] items-start relative shrink-0 w-full">
            <WidgetTitle />
            <CallerInfo />
          </div>
          <ProgressBar />
        </div>
        {/* Bottom gesture chips */}
        <div className="content-stretch flex flex-col gap-[4px] items-start relative shrink-0 w-full">
          <GestureBadgeDaumen />
          <GestureBadgeDrehen />
        </div>
      </div>
    </div>
  );
}
