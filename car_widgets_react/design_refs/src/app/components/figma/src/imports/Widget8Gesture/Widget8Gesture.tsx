import svgPaths from "./svg-n892qvsu0w";

function CombinedPanel() {
  return (
    <div className="bg-[#43275c] h-[36px] relative rounded-[10px] shrink-0 w-full" data-name="CombinedPanel">
      <p className="[word-break:break-word] absolute font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] left-[calc(50%-60px)] not-italic text-[#d5abff] text-[10px] top-[calc(50%-7.22px)] whitespace-nowrap">Dunkel Modus aktivieren</p>
    </div>
  );
}

function Container() {
  return <div className="-translate-y-1/2 absolute bg-[#60a5fa] border-[1.667px] border-solid border-white left-[45px] rounded-[18641400px] shadow-[0px_4px_6px_0px_rgba(0,0,0,0.1),0px_2px_4px_0px_rgba(0,0,0,0.1)] size-[10px] top-1/2" data-name="Container" />;
}

function ColorSlider() {
  return (
    <div className="absolute bg-gradient-to-r from-white h-[12px] left-[19px] overflow-clip right-0 rounded-[18641400px] to-[#43275c] top-[-0.23px]" data-name="ColorSlider">
      <Container />
    </div>
  );
}

function Icon() {
  return (
    <div className="absolute left-0 size-[10.998px] top-[1.01px]" data-name="Icon">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10.9983 10.9983">
        <g clipPath="url(#clip0_1_401)" id="Icon">
          <path d={svgPaths.p20ebc200} id="Vector" stroke="var(--stroke-0, #99A1AF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          <path d="M5.49915 0.916525V1.83305" id="Vector_2" stroke="var(--stroke-0, #99A1AF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          <path d="M5.49915 9.16525V10.0818" id="Vector_3" stroke="var(--stroke-0, #99A1AF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          <path d={svgPaths.p357d380} id="Vector_4" stroke="var(--stroke-0, #99A1AF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          <path d={svgPaths.p2d420480} id="Vector_5" stroke="var(--stroke-0, #99A1AF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          <path d="M0.916525 5.49915H1.83305" id="Vector_6" stroke="var(--stroke-0, #99A1AF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          <path d="M9.16525 5.49915H10.0818" id="Vector_7" stroke="var(--stroke-0, #99A1AF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          <path d={svgPaths.p28ea95c0} id="Vector_8" stroke="var(--stroke-0, #99A1AF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
          <path d={svgPaths.pf02e4d0} id="Vector_9" stroke="var(--stroke-0, #99A1AF)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.916525" />
        </g>
        <defs>
          <clipPath id="clip0_1_401">
            <rect fill="white" height="10.9983" width="10.9983" />
          </clipPath>
        </defs>
      </svg>
    </div>
  );
}

function CombinedPanel1() {
  return (
    <div className="h-[11.997px] relative shrink-0 w-full" data-name="CombinedPanel">
      <ColorSlider />
      <Icon />
    </div>
  );
}

function Frame3() {
  return (
    <div className="content-stretch flex flex-col gap-[10px] items-start relative shrink-0 w-full">
      <CombinedPanel />
      <CombinedPanel1 />
    </div>
  );
}

function Frame1() {
  return (
    <div className="content-stretch flex flex-col gap-[16px] items-start relative shrink-0 w-full">
      <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[12.5px] not-italic relative shrink-0 text-[#99a1af] text-[10px] tracking-[0.25px] uppercase w-full">Ambientebeleuchtung</p>
      <Frame3 />
    </div>
  );
}

function GestureBadge() {
  return (
    <div className="bg-[#353545] content-stretch flex gap-[5.998px] h-[23px] items-center pl-[7.995px] pr-[8px] py-[4px] relative rounded-[10px] shrink-0" data-name="GestureBadge">
      <div className="h-[11.997px] overflow-clip relative shrink-0 w-[11.997px]">
        <div className="absolute inset-[41.67%_70.83%_8.33%_29.17%]">
          <div className="absolute inset-[-8.33%_-0.5px]">
            <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 0.999708 6.99796">
              <path d="M0.499854 0.499854V6.4981" stroke="var(--stroke-0, #B172E7)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.999708" />
            </svg>
          </div>
        </div>
        <div className="absolute inset-[8.33%_9.04%_8.33%_8.33%]">
          <div className="absolute inset-[-5%_-5.04%]">
            <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10.9118 10.9968">
              <path d={svgPaths.p33bdb000} stroke="var(--stroke-0, #B172E7)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.999708" />
            </svg>
          </div>
        </div>
      </div>
      <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#dab2ff] text-[10px] whitespace-nowrap">Daumen hoch</p>
    </div>
  );
}

function GestureBadge1() {
  return (
    <div className="bg-[#353545] content-stretch flex gap-[5.998px] h-[23px] items-center pl-[7.995px] pr-[8px] py-[4px] relative rounded-[10px] shrink-0" data-name="GestureBadge">
      <div className="h-[11.997px] overflow-clip relative shrink-0 w-[11.997px]">
        <div className="absolute inset-[12.5%]">
          <div className="absolute inset-[-5.56%]">
            <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 9.99709 9.99709">
              <path d={svgPaths.p2322d500} stroke="var(--stroke-0, #B172E7)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.999708" />
            </svg>
          </div>
        </div>
        <div className="absolute inset-[12.5%_66.67%_66.67%_12.5%]">
          <div className="absolute inset-[-20%]">
            <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 3.49898 3.49898">
              <path d={svgPaths.p11ab4d40} stroke="var(--stroke-0, #B172E7)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.999708" />
            </svg>
          </div>
        </div>
      </div>
      <p className="[word-break:break-word] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[15px] not-italic relative shrink-0 text-[#dab2ff] text-[10px] whitespace-nowrap">Drehen</p>
    </div>
  );
}

function GesturePanel() {
  return (
    <div className="content-stretch flex flex-col gap-[4px] items-start relative shrink-0 w-full" data-name="Gesture Panel">
      <GestureBadge />
      <GestureBadge1 />
    </div>
  );
}

function Frame2() {
  return (
    <div className="content-stretch flex flex-col h-[172.99px] items-start justify-between relative shrink-0 w-full">
      <Frame1 />
      <GesturePanel />
    </div>
  );
}

export default function Widget8Gesture() {
  return (
    <div className="bg-[#252530] content-stretch flex flex-col items-start p-[16px] relative rounded-[16px] size-full" data-name="Widget 8 - Gesture">
      <Frame2 />
    </div>
  );
}
