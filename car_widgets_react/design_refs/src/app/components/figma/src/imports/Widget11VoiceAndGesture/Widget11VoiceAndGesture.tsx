import svgPaths from "./svg-67dmmcdmvm";

function WidgetTitle() {
  return (
    <div className="content-stretch flex h-[12.5px] items-start relative shrink-0 w-full" data-name="WidgetTitle">
      <p className="[word-break:break-word] flex-[1_0_0] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[12.5px] min-w-px not-italic relative text-[#99a1af] text-[10px] tracking-[0.25px] uppercase">Musik</p>
    </div>
  );
}

function Container() {
  return <div className="bg-[rgba(255,255,255,0.25)] h-[23.993px] relative rounded-tl-[18641400px] rounded-tr-[18641400px] shrink-0 w-[20px]" data-name="Container" />;
}

function ArtistPhoto() {
  return (
    <div className="relative rounded-[14px] shrink-0 size-[40px]" style={{ backgroundImage: "linear-gradient(160deg, rgb(45, 27, 105) 8.4861%, rgb(17, 153, 142) 91.514%)" }} data-name="ArtistPhoto">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-end justify-center overflow-clip pb-[3.993px] px-[10px] relative rounded-[inherit] size-full">
        <Container />
      </div>
    </div>
  );
}

function Paragraph() {
  return (
    <div className="absolute content-stretch flex h-[12.5px] items-start left-0 overflow-clip top-0 w-[98.455px]" data-name="Paragraph">
      <p className="[word-break:break-word] flex-[1_0_0] font-['Inter:Bold',sans-serif] font-bold leading-[12.5px] min-w-px not-italic relative text-[10px] text-white">The Weeknd</p>
    </div>
  );
}

function Paragraph1() {
  return (
    <div className="absolute h-[13.498px] left-0 overflow-clip top-[12.5px] w-[98.455px]" data-name="Paragraph">
      <p className="[word-break:break-word] absolute font-['Inter:Regular',sans-serif] font-normal leading-[13.5px] left-0 not-italic text-[#99a1af] text-[9px] top-[0.11px] whitespace-nowrap">Blinding Lights</p>
    </div>
  );
}

function Container1() {
  return (
    <div className="flex-[98.455_0_0] h-[25.998px] min-w-px relative" data-name="Container">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid relative size-full">
        <Paragraph />
        <Paragraph1 />
      </div>
    </div>
  );
}

function CombinedPanel() {
  return (
    <div className="h-[40px] relative shrink-0 w-full" data-name="CombinedPanel">
      <div className="flex flex-row items-center size-full">
        <div className="content-stretch flex gap-[7.995px] items-center relative size-full">
          <ArtistPhoto />
          <Container1 />
        </div>
      </div>
    </div>
  );
}

function Icon() {
  return (
    <div className="h-[10.998px] overflow-clip relative shrink-0 w-full" data-name="Icon">
      <div className="absolute inset-[16.67%_37.5%_16.67%_20.83%]" data-name="Vector">
        <div className="absolute inset-[-6.25%_-10%]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 5.49915 8.24873">
            <path d={svgPaths.p3708a880} id="Vector" stroke="var(--stroke-0, white)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          </svg>
        </div>
      </div>
      <div className="absolute inset-[20.83%_20.83%_20.83%_79.17%]" data-name="Vector">
        <div className="absolute inset-[-7.14%_-0.46px]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.916525 7.3322">
            <path d="M0.458263 0.458263V6.87394" id="Vector" stroke="var(--stroke-0, white)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function Button() {
  return (
    <div className="bg-[#353545] relative rounded-[18641400px] shrink-0 size-[18.984px]" data-name="Button">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex flex-col items-start pt-[3.993px] px-[3.993px] relative size-full">
        <Icon />
      </div>
    </div>
  );
}

function CombinedPanel1() {
  return (
    <div className="content-stretch flex gap-[3.993px] h-[18.984px] items-center relative shrink-0 w-full" data-name="CombinedPanel">
      <Button />
      <p className="[word-break:break-word] font-['Inter:Regular',sans-serif] font-normal leading-[13.5px] not-italic text-[#99a1af] text-[9px] whitespace-nowrap">Nächster Titel</p>
    </div>
  );
}

function Frame1() {
  return (
    <div className="content-stretch flex flex-col gap-[8px] items-start relative shrink-0 w-full">
      <WidgetTitle />
      <CombinedPanel />
      <CombinedPanel1 />
    </div>
  );
}

function GestureBadge() {
  return (
    <div className="bg-[#1a3a2a] content-stretch flex gap-[5.998px] h-[22.986px] items-center pl-[7.995px] pr-[8px] py-[4px] relative rounded-[10px] shrink-0" data-name="GestureBadge">
      <div className="relative shrink-0 size-[10.998px]">
        <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10.9983 10.9983">
          <g clipPath="url(#clip0_1_414a)" id="Icon">
            <path d={svgPaths.p5cef080} id="Vector" stroke="var(--stroke-0, #7BF1A8)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
            <path d={svgPaths.p36eb3f00} id="Vector_2" stroke="var(--stroke-0, #7BF1A8)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
            <path d={svgPaths.p36386e80} id="Vector_3" stroke="var(--stroke-0, #7BF1A8)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
            <path d={svgPaths.p3ff8cd00} id="Vector_4" stroke="var(--stroke-0, #7BF1A8)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          </g>
          <defs><clipPath id="clip0_1_414a"><rect fill="white" height="10.9983" width="10.9983" /></clipPath></defs>
        </svg>
      </div>
      <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#7bf1a8] text-[10px] whitespace-nowrap">Tippen</p>
    </div>
  );
}

function GestureBadge1() {
  return (
    <div className="bg-[#1a3a2a] content-stretch flex gap-[5.998px] h-[22.986px] items-center pl-[7.995px] pr-[8px] py-[4px] relative rounded-[10px] shrink-0" data-name="GestureBadge">
      <div className="relative shrink-0 size-[10.998px]">
        <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10.9983 10.9983">
          <g clipPath="url(#clip0_1_414b)" id="Icon">
            <path d={svgPaths.p5cef080} id="Vector" stroke="var(--stroke-0, #7BF1A8)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
            <path d={svgPaths.p36eb3f00} id="Vector_2" stroke="var(--stroke-0, #7BF1A8)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
            <path d={svgPaths.p36386e80} id="Vector_3" stroke="var(--stroke-0, #7BF1A8)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
            <path d={svgPaths.p3ff8cd00} id="Vector_4" stroke="var(--stroke-0, #7BF1A8)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          </g>
          <defs><clipPath id="clip0_1_414b"><rect fill="white" height="10.9983" width="10.9983" /></clipPath></defs>
        </svg>
      </div>
      <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#7bf1a8] text-[10px] whitespace-nowrap">Swipe</p>
    </div>
  );
}

function Frame() {
  return (
    <div className="content-stretch flex flex-col gap-[8px] h-[53.972px] items-start relative shrink-0 w-full">
      <GestureBadge />
      <GestureBadge1 />
    </div>
  );
}

function Frame2() {
  return (
    <div className="content-stretch flex flex-col gap-[11px] items-start relative shrink-0 w-full">
      <Frame1 />
      <Frame />
    </div>
  );
}

export default function Widget11VoiceAndGesture() {
  return (
    <div className="bg-[#252530] content-stretch flex flex-col items-start p-[16px] relative rounded-[16px] size-full" data-name="Widget 11 - Voice and Gesture">
      <Frame2 />
    </div>
  );
}
