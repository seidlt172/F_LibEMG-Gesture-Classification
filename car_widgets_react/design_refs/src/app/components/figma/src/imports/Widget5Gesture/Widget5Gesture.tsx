import svgPaths from "./svg-z9prc2p8jz";

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
    <div className="absolute content-stretch flex h-[12.5px] items-start left-0 top-[15px] w-[98.455px]" data-name="Paragraph">
      <p className="[word-break:break-word] flex-[1_0_0] font-['Inter:Bold',sans-serif] font-bold leading-[12.5px] min-w-px not-italic relative text-[10px] text-white">Save Your Tears</p>
    </div>
  );
}

function Container1() {
  return (
    <div className="flex-[98.455_0_0] h-[27.5px] min-w-px relative" data-name="Container">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid relative size-full">
        <p className="[word-break:break-word] absolute font-['Inter:Regular',sans-serif] font-normal leading-[15px] left-0 not-italic text-[#99a1af] text-[10px] top-[0.67px] whitespace-nowrap">Vorschlag</p>
        <Paragraph />
      </div>
    </div>
  );
}

function Content() {
  return (
    <div className="h-[40px] relative shrink-0 w-full" data-name="Content">
      <div className="flex flex-row items-center size-full">
        <div className="content-stretch flex gap-[7.995px] items-center relative size-full">
          <ArtistPhoto />
          <Container1 />
        </div>
      </div>
    </div>
  );
}

function Frame() {
  return (
    <div className="content-stretch flex flex-col gap-[8px] items-start relative shrink-0 w-full">
      <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[12.5px] not-italic relative shrink-0 text-[#99a1af] text-[10px] tracking-[0.25px] uppercase w-full">Musik</p>
      <Content />
    </div>
  );
}

function Icon() {
  return (
    <div className="h-[11.997px] overflow-clip relative shrink-0 w-full" data-name="Icon">
      <div className="absolute inset-[41.67%_70.83%_8.33%_29.17%]" data-name="Vector">
        <div className="absolute inset-[-8.33%_-0.5px]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.999708 6.99796">
            <path d="M0.499854 0.499854V6.4981" id="Vector" stroke="var(--stroke-0, #B172E7)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.999708" />
          </svg>
        </div>
      </div>
      <div className="absolute inset-[8.33%_9.04%_8.33%_8.33%]" data-name="Vector">
        <div className="absolute inset-[-5%_-5.04%]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10.9118 10.9968">
            <path d={svgPaths.p33bdb000} id="Vector" stroke="var(--stroke-0, #B172E7)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.999708" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function Text() {
  return (
    <div className="relative shrink-0 size-[11.997px]" data-name="Text">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex flex-col items-start relative size-full">
        <Icon />
      </div>
    </div>
  );
}

function GestureBadge() {
  return (
    <div className="bg-[#353545] content-stretch flex gap-[5.998px] h-[23px] items-center pl-[7.995px] pr-[8px] py-[4px] relative rounded-[10px] shrink-0" data-name="GestureBadge">
      <Text />
      <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#dab2ff] text-[10px] whitespace-nowrap">Daumen hoch</p>
    </div>
  );
}

function Icon1() {
  return (
    <div className="relative shrink-0 size-[10.998px]" data-name="Icon">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10.9983 10.9983">
        <g clipPath="url(#clip0_1_359)" id="Icon">
          <path d={svgPaths.p5cef080} id="Vector" stroke="var(--stroke-0, #C27AFF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          <path d={svgPaths.p36eb3f00} id="Vector_2" stroke="var(--stroke-0, #C27AFF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          <path d={svgPaths.p36386e80} id="Vector_3" stroke="var(--stroke-0, #C27AFF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          <path d={svgPaths.p3ff8cd00} id="Vector_4" stroke="var(--stroke-0, #C27AFF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
        </g>
        <defs>
          <clipPath id="clip0_1_359">
            <rect fill="white" height="10.9983" width="10.9983" />
          </clipPath>
        </defs>
      </svg>
    </div>
  );
}

function Text1() {
  return (
    <div className="h-[15px] relative shrink-0 w-[29.679px]" data-name="Text">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid relative size-full">
        <p className="[word-break:break-word] absolute font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] left-0 not-italic text-[#dab2ff] text-[10px] top-[0.67px] whitespace-nowrap">Swipe</p>
      </div>
    </div>
  );
}

function Container2() {
  return (
    <div className="bg-[#353545] content-stretch flex gap-[5.998px] h-[22.986px] items-center pl-[7.995px] pr-[8px] py-[4px] relative rounded-[10px] shrink-0 w-[62.665px]" data-name="Container">
      <Icon1 />
      <Text1 />
    </div>
  );
}

function GesturePanel() {
  return (
    <div className="content-stretch flex flex-col gap-[4px] items-start relative shrink-0 w-full" data-name="Gesture Panel">
      <GestureBadge />
      <Container2 />
    </div>
  );
}

function Frame1() {
  return (
    <div className="content-stretch flex flex-col gap-[62px] items-start relative shrink-0 w-full">
      <Frame />
      <GesturePanel />
    </div>
  );
}

export default function Widget5Gesture() {
  return (
    <div className="bg-[#252530] content-stretch flex flex-col items-start p-[16px] relative rounded-[16px] size-full" data-name="Widget 5 - Gesture">
      <Frame1 />
    </div>
  );
}
