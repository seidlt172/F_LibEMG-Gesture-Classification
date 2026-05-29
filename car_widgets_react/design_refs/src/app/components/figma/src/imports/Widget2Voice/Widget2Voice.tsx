import svgPaths from "./svg-ejhf7f6zms";

function WidgetTitle() {
  return (
    <div className="content-stretch flex h-[12.5px] items-start relative shrink-0 w-full" data-name="WidgetTitle">
      <p className="[word-break:break-word] flex-[1_0_0] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[12.5px] min-w-px not-italic relative text-[#99a1af] text-[10px] tracking-[0.25px] uppercase">Eingehender Anruf</p>
    </div>
  );
}

function Icon() {
  return (
    <div className="relative shrink-0 size-[13.993px]" data-name="Icon">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 13.9931 13.9931">
        <g clipPath="url(#clip0_1_351)" id="Icon">
          <path d={svgPaths.pc36ffb0} fill="var(--fill-0, white)" id="Vector" stroke="var(--stroke-0, white)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.16609" />
        </g>
        <defs>
          <clipPath id="clip0_1_351">
            <rect fill="white" height="13.9931" width="13.9931" />
          </clipPath>
        </defs>
      </svg>
    </div>
  );
}

function PhoneCircle() {
  return (
    <div className="bg-[#16a34a] relative rounded-[18641400px] shrink-0 size-[31.997px]" data-name="PhoneCircle">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-center justify-center px-[9.002px] relative size-full">
        <Icon />
      </div>
    </div>
  );
}

function Paragraph() {
  return (
    <div className="content-stretch flex h-[14.991px] items-start relative shrink-0 w-full" data-name="Paragraph">
      <p className="[word-break:break-word] font-['Inter:Bold',sans-serif] font-bold leading-[15px] not-italic relative shrink-0 text-[12px] text-white whitespace-nowrap">Max Mustermann</p>
    </div>
  );
}

function Paragraph1() {
  return (
    <div className="h-[15px] relative shrink-0 w-full" data-name="Paragraph">
      <p className="[word-break:break-word] absolute font-['Inter:Regular',sans-serif] font-normal leading-[15px] left-0 not-italic text-[#99a1af] text-[10px] top-[0.67px] whitespace-nowrap">Mobil</p>
    </div>
  );
}

function Container() {
  return (
    <div className="h-[29.991px] relative shrink-0 w-[70.833px]" data-name="Container">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex flex-col items-start relative size-full">
        <Paragraph />
        <Paragraph1 />
      </div>
    </div>
  );
}

function VoicePanel() {
  return (
    <div className="content-stretch flex gap-[7.995px] h-[31.997px] items-center relative shrink-0 w-full" data-name="VoicePanel">
      <PhoneCircle />
      <Container />
    </div>
  );
}

function Frame() {
  return (
    <div className="content-stretch flex flex-col gap-[8px] items-start relative shrink-0 w-full">
      <WidgetTitle />
      <VoicePanel />
    </div>
  );
}

function Frame2() {
  return (
    <div className="bg-[#16a34a] flex-[1_0_0] min-w-px relative rounded-[16px]">
      <div className="flex flex-row items-center justify-center size-full">
        <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-center justify-center px-[8px] py-[4px] relative size-full">
          <p className="[word-break:break-word] font-['Inter:Bold',sans-serif] font-bold leading-[15px] not-italic relative shrink-0 text-[10px] text-center text-white tracking-[0.25px] whitespace-nowrap">Annehmen</p>
        </div>
      </div>
    </div>
  );
}

function Frame3() {
  return (
    <div className="bg-[#dc2626] flex-[1_0_0] min-w-px relative rounded-[16px]">
      <div className="flex flex-row items-center justify-center size-full">
        <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-center justify-center px-[8px] py-[4px] relative size-full">
          <p className="[word-break:break-word] font-['Inter:Bold',sans-serif] font-bold leading-[15px] not-italic relative shrink-0 text-[10px] text-center text-white tracking-[0.25px] whitespace-nowrap">Ablehnen</p>
        </div>
      </div>
    </div>
  );
}

function VoicePanel1() {
  return (
    <div className="content-stretch flex gap-[5.998px] items-center justify-center relative shrink-0 w-full" data-name="VoicePanel">
      <Frame2 />
      <Frame3 />
    </div>
  );
}

function Frame1() {
  return (
    <div className="content-stretch flex flex-col gap-[12px] items-start relative shrink-0 w-full">
      <Frame />
      <VoicePanel1 />
    </div>
  );
}

export default function Widget2Voice() {
  return (
    <div className="bg-[#252530] content-stretch flex flex-col items-start p-[16px] relative rounded-[16px] size-full" data-name="Widget 2 - Voice">
      <Frame1 />
    </div>
  );
}
