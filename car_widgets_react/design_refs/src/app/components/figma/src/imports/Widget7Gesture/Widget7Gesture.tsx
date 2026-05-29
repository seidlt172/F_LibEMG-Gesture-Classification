import svgPaths from "./svg-tfi5hmc93n";

function Container() {
  return (
    <div className="bg-[#1e3a5f] h-[27px] relative rounded-[10px] shrink-0 w-full" data-name="Container">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-start justify-between pb-[6px] pt-[5.998px] px-[7.995px] relative size-full">
        <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[10px] text-white whitespace-nowrap">Route A</p>
        <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#51a2ff] text-[10px] whitespace-nowrap">24 min</p>
      </div>
    </div>
  );
}

function Container1() {
  return (
    <div className="bg-[#353545] h-[27px] relative rounded-[10px] shrink-0 w-full" data-name="Container">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-start justify-between pb-[6px] pt-[5.998px] px-[7.995px] relative size-full">
        <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#9ca3af] text-[10px] whitespace-nowrap">Route B</p>
        <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#9ca3af] text-[10px] whitespace-nowrap">29 min</p>
      </div>
    </div>
  );
}

function GesturePanel() {
  return (
    <div className="content-stretch flex flex-col gap-[3.993px] h-[57.986px] items-start relative shrink-0 w-full" data-name="GesturePanel">
      <Container />
      <Container1 />
    </div>
  );
}

function Frame() {
  return (
    <div className="content-stretch flex flex-col gap-[8px] h-[78.486px] items-start relative shrink-0 w-full">
      <p className="[word-break:break-word] flex-[1_0_0] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[12.5px] min-h-px not-italic relative text-[#99a1af] text-[10px] tracking-[0.25px] uppercase w-full">Navigation</p>
      <GesturePanel />
    </div>
  );
}

function SwipeBadge() {
  return (
    <div className="bg-[#353545] content-stretch flex gap-[5.998px] h-[22.986px] items-center pl-[7.995px] pr-[8px] py-[4px] relative rounded-[10px] shrink-0 w-[62.665px]" data-name="Container">
      <div className="relative shrink-0 size-[10.998px]">
        <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10.9983 10.9983">
          <g clipPath="url(#clip0_swipe)" id="Icon">
            <path d={svgPaths.p5cef080} id="Vector" stroke="var(--stroke-0, #C27AFF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
            <path d={svgPaths.p36eb3f00} id="Vector_2" stroke="var(--stroke-0, #C27AFF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
            <path d={svgPaths.p36386e80} id="Vector_3" stroke="var(--stroke-0, #C27AFF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
            <path d={svgPaths.p3ff8cd00} id="Vector_4" stroke="var(--stroke-0, #C27AFF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          </g>
          <defs><clipPath id="clip0_swipe"><rect fill="white" height="10.9983" width="10.9983" /></clipPath></defs>
        </svg>
      </div>
      <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#dab2ff] text-[10px] top-[0.67px] whitespace-nowrap">Swipe</p>
    </div>
  );
}

function TippenBadge() {
  return (
    <div className="bg-[#353545] content-stretch flex gap-[5.998px] h-[22.986px] items-center pl-[7.995px] pr-[8px] py-[4px] relative rounded-[10px] shrink-0 w-[62.665px]" data-name="Container">
      <div className="relative shrink-0 size-[10.998px]">
        <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10.9983 10.9983">
          <g clipPath="url(#clip0_tippen)" id="Icon">
            <path d={svgPaths.p5cef080} id="Vector" stroke="var(--stroke-0, #C27AFF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
            <path d={svgPaths.p36eb3f00} id="Vector_2" stroke="var(--stroke-0, #C27AFF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
            <path d={svgPaths.p36386e80} id="Vector_3" stroke="var(--stroke-0, #C27AFF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
            <path d={svgPaths.p3ff8cd00} id="Vector_4" stroke="var(--stroke-0, #C27AFF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          </g>
          <defs><clipPath id="clip0_tippen"><rect fill="white" height="10.9983" width="10.9983" /></clipPath></defs>
        </svg>
      </div>
      <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#dab2ff] text-[10px] top-[0.67px] whitespace-nowrap">Tippen</p>
    </div>
  );
}

function GesturePanel1() {
  return (
    <div className="content-stretch flex flex-col gap-[4px] items-start relative shrink-0 w-full" data-name="Gesture Panel">
      <SwipeBadge />
      <TippenBadge />
    </div>
  );
}

function Frame1() {
  return (
    <div className="content-stretch flex flex-col h-[172.99px] items-start justify-between relative shrink-0 w-full">
      <Frame />
      <GesturePanel1 />
    </div>
  );
}

export default function Widget7Gesture() {
  return (
    <div className="bg-[#252530] content-stretch flex flex-col items-start p-[16px] relative rounded-[16px] size-full" data-name="Widget 7 - Gesture">
      <Frame1 />
    </div>
  );
}
