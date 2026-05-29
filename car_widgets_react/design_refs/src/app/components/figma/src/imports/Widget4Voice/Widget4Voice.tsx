import svgPaths from "./svg-m7ryhk709w";

function WidgetTitle() {
  return (
    <div className="content-stretch flex h-[12.5px] items-start relative shrink-0 w-[146.458px]" data-name="WidgetTitle">
      <p className="[word-break:break-word] flex-[1_0_0] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[12.5px] min-w-px not-italic relative text-[#99a1af] text-[10px] tracking-[0.25px] uppercase">Navigation</p>
    </div>
  );
}

function Icon() {
  return (
    <div className="relative shrink-0 size-[13.993px]" data-name="Icon">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 13.9931 13.9931">
        <g clipPath="url(#clip0_1_354)" id="Icon">
          <path d={svgPaths.p25648b80} id="Vector" stroke="var(--stroke-0, white)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.16609" />
        </g>
        <defs>
          <clipPath id="clip0_1_354">
            <rect fill="white" height="13.9931" width="13.9931" />
          </clipPath>
        </defs>
      </svg>
    </div>
  );
}

function Container() {
  return (
    <div className="bg-[#3b82f6] relative rounded-[18641400px] shrink-0 size-[31.997px]" data-name="Container">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-center justify-center px-[9.002px] relative size-full">
        <Icon />
      </div>
    </div>
  );
}

function Paragraph() {
  return (
    <div className="flex-[1_0_0] h-[25px] min-w-px relative" data-name="Paragraph">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid relative size-full">
        <p className="[word-break:break-word] absolute font-['Inter:Regular',sans-serif] font-normal leading-[12.5px] left-0 not-italic right-[25.01px] text-[#d1d5dc] text-[10px] top-0">Navigation Route starten?</p>
      </div>
    </div>
  );
}

function VoicePanel() {
  return (
    <div className="content-stretch flex gap-[7.995px] h-[31.997px] items-center relative shrink-0 w-full" data-name="VoicePanel">
      <Container />
      <Paragraph />
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

function Container2() {
  return <div className="bg-[#3b82f6] h-[7.995px] relative rounded-[18641400px] shrink-0 w-full" data-name="Container" />;
}

function Container1() {
  return (
    <div className="bg-[#353545] flex-[116.363_0_0] h-[7.995px] min-w-px relative rounded-[18641400px]" data-name="Container">
      <div className="overflow-clip rounded-[inherit] size-full">
        <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex flex-col items-start pr-[29.097px] relative size-full">
          <Container2 />
        </div>
      </div>
    </div>
  );
}

function Text() {
  return (
    <div className="h-[15px] relative shrink-0 w-[22.101px]" data-name="Text">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid relative size-full">
        <p className="[word-break:break-word] absolute font-['Inter:Bold',sans-serif] font-bold leading-[15px] left-0 not-italic text-[#3b82f6] text-[10px] top-[0.67px] whitespace-nowrap">75%</p>
      </div>
    </div>
  );
}

function VolumeBar() {
  return (
    <div className="content-stretch flex gap-[7.995px] h-[15px] items-center relative shrink-0 w-full" data-name="VolumeBar">
      <Container1 />
      <Text />
    </div>
  );
}

function Frame1() {
  return (
    <div className="relative shrink-0 w-full">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex flex-col gap-[8px] items-start relative size-full">
        <Frame />
        <VolumeBar />
      </div>
    </div>
  );
}

function Frame2() {
  return (
    <div className="bg-[#e5e7eb] relative rounded-[16px] shrink-0 w-full">
      <div className="flex flex-row items-center justify-center size-full">
        <div className="content-stretch flex items-center justify-center px-[8px] py-[4px] relative size-full">
          <p className="[word-break:break-word] font-['Inter:Bold',sans-serif] font-bold leading-[15px] not-italic relative shrink-0 text-[#111827] text-[10px] text-center tracking-[0.25px] whitespace-nowrap">Annehmen</p>
        </div>
      </div>
    </div>
  );
}

function VoicePanel1() {
  return (
    <div className="relative shrink-0 w-[79px]" data-name="VoicePanel">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex flex-col items-start relative size-full">
        <Frame2 />
      </div>
    </div>
  );
}

export default function Widget4Voice() {
  return (
    <div className="bg-[#252530] content-stretch flex flex-col items-start justify-between p-[16px] relative rounded-[16px] size-full" data-name="Widget 4 - Voice">
      <Frame1 />
      <VoicePanel1 />
    </div>
  );
}
