function WidgetTitle() {
  return (
    <div className="h-[12.5px] relative shrink-0 w-[146.45px]" data-name="WidgetTitle">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-start relative size-full">
        <p className="[word-break:break-word] flex-[1_0_0] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[12.5px] min-w-px not-italic relative text-[#99a1af] text-[10px] tracking-[0.25px] uppercase">Nachrichten</p>
      </div>
    </div>
  );
}

function Paragraph() {
  return (
    <div className="h-[13.75px] relative shrink-0 w-full" data-name="Paragraph">
      <p className="[word-break:break-word] absolute font-['Inter:Medium',sans-serif] font-medium leading-[13.75px] left-0 not-italic text-[#d1d5dc] text-[10px] top-[-0.44px] whitespace-nowrap">Neue Nachricht</p>
    </div>
  );
}

function Paragraph1() {
  return (
    <div className="h-[15px] relative shrink-0 w-full" data-name="Paragraph">
      <p className="[word-break:break-word] absolute font-['Inter:Regular',sans-serif] font-normal leading-[0] left-0 not-italic text-[#99a1af] text-[0px] top-[0.67px] whitespace-nowrap">
        <span className="leading-[15px] text-[10px]">{`Von: `}</span>
        <span className="font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] text-[10px] text-white">Anna</span>
      </p>
    </div>
  );
}

function VoicePanel() {
  return (
    <div className="bg-[#1e1e2e] flex-[126.753_0_0] min-h-px relative rounded-[14px] w-full" data-name="VoicePanel">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex flex-col items-start pt-[7.995px] px-[7.995px] relative size-full">
        <Paragraph />
        <Paragraph1 />
      </div>
    </div>
  );
}

function Frame() {
  return (
    <div className="bg-[#7c3aed] flex-[1_0_0] min-w-px relative rounded-[16px]">
      <div className="flex flex-row items-center justify-center size-full">
        <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-center justify-center px-[8px] py-[4px] relative size-full">
          <p className="[word-break:break-word] font-['Inter:Bold',sans-serif] font-bold leading-[15px] not-italic relative shrink-0 text-[10px] text-center text-white tracking-[0.25px] whitespace-nowrap">Öffnen</p>
        </div>
      </div>
    </div>
  );
}

function Frame1() {
  return (
    <div className="bg-[#7c3aed] flex-[1_0_0] min-w-px relative rounded-[16px]">
      <div className="flex flex-row items-center justify-center size-full">
        <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-center justify-center px-[8px] py-[4px] relative size-full">
          <p className="[word-break:break-word] font-['Inter:Bold',sans-serif] font-bold leading-[15px] not-italic relative shrink-0 text-[10px] text-center text-white tracking-[0.25px] whitespace-nowrap">Schließen</p>
        </div>
      </div>
    </div>
  );
}

function VoicePanel1() {
  return (
    <div className="relative shrink-0 w-full" data-name="VoicePanel">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex gap-[5.998px] items-center justify-center relative size-full">
        <Frame />
        <Frame1 />
      </div>
    </div>
  );
}

export default function Widget3Voice() {
  return (
    <div className="bg-[#252530] content-stretch flex flex-col gap-[7.995px] items-start pb-[11.996px] pl-[11.997px] pr-[12px] pt-[11.997px] relative rounded-[16px] size-full" data-name="Widget 3 - Voice">
      <WidgetTitle />
      <VoicePanel />
      <VoicePanel1 />
    </div>
  );
}
