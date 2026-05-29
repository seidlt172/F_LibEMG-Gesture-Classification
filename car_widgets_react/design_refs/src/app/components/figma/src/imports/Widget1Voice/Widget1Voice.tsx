import svgPaths from "./svg-6ybmc6ipon";

function WidgetTitle() {
  return (
    <div className="content-stretch flex items-start relative shrink-0 w-full" data-name="WidgetTitle">
      <p className="[word-break:break-word] flex-[1_0_0] font-['Inter:Semi_Bold',sans-serif] font-semibold leading-[12.5px] min-w-px not-italic relative text-[#99a1af] text-[10px] tracking-[0.25px] uppercase">Musik</p>
    </div>
  );
}

function Text() {
  return (
    <div className="h-[10px] relative shrink-0 w-[17.83px]" data-name="Text">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-start px-[4px] relative size-full">
        <p className="[word-break:break-word] font-['Inter:Black',sans-serif] font-black leading-[10px] not-italic relative shrink-0 text-[8px] text-[rgba(255,255,255,0.8)] text-center whitespace-nowrap">BL</p>
      </div>
    </div>
  );
}

function Container() {
  return (
    <div className="relative shrink-0 size-[35.998px]" style={{ backgroundImage: "url('data:image/svg+xml;utf8,<svg viewBox=\\'0 0 35.998 35.998\\' xmlns=\\'http://www.w3.org/2000/svg\\' preserveAspectRatio=\\'none\\'><rect x=\\'0\\' y=\\'0\\' height=\\'100%\\' width=\\'100%\\' fill=\\'url(%23grad)\\' opacity=\\'1\\'/><defs><radialGradient id=\\'grad\\' gradientUnits=\\'userSpaceOnUse\\' cx=\\'0\\' cy=\\'0\\' r=\\'10\\' gradientTransform=\\'matrix(0 -3.1844 -3.1844 0 14.399 12.599)\\'><stop stop-color=\\'rgba(124,58,237,1)\\' offset=\\'0\\'/><stop stop-color=\\'rgba(100,50,189,1)\\' offset=\\'0.15\\'/><stop stop-color=\\'rgba(75,42,142,1)\\' offset=\\'0.3\\'/><stop stop-color=\\'rgba(51,34,94,1)\\' offset=\\'0.45\\'/><stop stop-color=\\'rgba(38,30,70,1)\\' offset=\\'0.525\\'/><stop stop-color=\\'rgba(26,26,46,1)\\' offset=\\'0.6\\'/></radialGradient></defs></svg>')" }} data-name="Container">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-center justify-center pl-[9.08px] pr-[9.089px] relative size-full">
        <Text />
      </div>
    </div>
  );
}

function AlbumArt() {
  return (
    <div className="relative rounded-[10px] shrink-0 size-[35.998px]" style={{ backgroundImage: "linear-gradient(135deg, rgb(26, 26, 46) 0%, rgb(22, 33, 62) 50%, rgb(15, 52, 96) 100%)" }} data-name="AlbumArt">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex items-center justify-center overflow-clip relative rounded-[inherit] size-full">
        <Container />
      </div>
    </div>
  );
}

function Paragraph() {
  return (
    <div className="absolute content-stretch flex h-[12.5px] items-start left-0 overflow-clip top-0 w-[102.465px]" data-name="Paragraph">
      <p className="[word-break:break-word] flex-[1_0_0] font-['Inter:Bold',sans-serif] font-bold leading-[12.5px] min-w-px not-italic relative text-[10px] text-white">Blinding Lights</p>
    </div>
  );
}

function Paragraph1() {
  return (
    <div className="absolute h-[13.498px] left-0 overflow-clip top-[12.5px] w-[102.465px]" data-name="Paragraph">
      <p className="[word-break:break-word] absolute font-['Inter:Regular',sans-serif] font-normal leading-[13.5px] left-0 not-italic text-[#99a1af] text-[9px] top-[0.11px] whitespace-nowrap">The Weeknd</p>
    </div>
  );
}

function Container1() {
  return (
    <div className="flex-[102.465_0_0] h-[25.998px] min-w-px relative" data-name="Container">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid relative size-full">
        <Paragraph />
        <Paragraph1 />
      </div>
    </div>
  );
}

function VoicePanel() {
  return (
    <div className="content-stretch flex gap-[7.995px] h-[35.998px] items-center relative shrink-0 w-[146.458px]" data-name="VoicePanel">
      <AlbumArt />
      <Container1 />
    </div>
  );
}

function Frame() {
  return (
    <div className="relative shrink-0 w-full">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex flex-col gap-[8px] items-start relative size-full">
        <WidgetTitle />
        <VoicePanel />
      </div>
    </div>
  );
}

function Container3() {
  return <div className="bg-[#3b82f6] h-[7.995px] relative rounded-[18641400px] shrink-0 w-full" data-name="Container" />;
}

function Container2() {
  return (
    <div className="bg-[#353545] flex-[116.363_0_0] h-[7.995px] min-w-px relative rounded-[18641400px]" data-name="Container">
      <div className="overflow-clip rounded-[inherit] size-full">
        <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex flex-col items-start pr-[29.097px] relative size-full">
          <Container3 />
        </div>
      </div>
    </div>
  );
}

function Text1() {
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
      <Container2 />
      <Text1 />
    </div>
  );
}

function Frame1() {
  return (
    <div className="relative shrink-0 w-full">
      <div className="flex flex-row items-center justify-center size-full">
        <div className="content-stretch flex items-center justify-between px-[48px] relative size-full">
          <div className="flex items-center justify-center relative shrink-0">
            <div className="flex-none rotate-180">
              <div className="relative size-[10px]" data-name="Vector">
                <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10 10">
                  <g id="Vector">
                    <path d={svgPaths.p38de5600} fill="var(--fill-0, #D9D9D9)" />
                    <path d={svgPaths.p1c348680} fill="var(--fill-0, #D9D9D9)" />
                  </g>
                </svg>
              </div>
            </div>
          </div>
          <div className="flex items-center justify-center relative shrink-0 size-[18px]">
            <div className="flex-none rotate-90">
              <div className="relative size-[18px]">
                <div className="absolute bottom-1/4 left-[10.76%] right-[10.76%] top-[5.56%]">
                  <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14.1273 12.5">
                    <path d={svgPaths.p18f60500} fill="var(--fill-0, #D9D9D9)" id="Polygon 4" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
          <div className="relative shrink-0 size-[10px]" data-name="Vector">
            <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 10 10">
              <g id="Vector">
                <path d={svgPaths.p280f4680} fill="var(--fill-0, #D9D9D9)" />
                <path d={svgPaths.p1c348680} fill="var(--fill-0, #D9D9D9)" />
              </g>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function Frame2() {
  return (
    <div className="flex-[1_0_0] min-h-px relative w-full">
      <div className="bg-clip-padding border-0 border-[transparent] border-solid content-stretch flex flex-col items-start justify-between relative size-full">
        <VolumeBar />
        <Frame1 />
      </div>
    </div>
  );
}

export default function Widget1Voice() {
  return (
    <div className="bg-[#252530] content-stretch flex flex-col gap-[8px] items-start pb-[12px] pl-[11.997px] pr-[12px] pt-[11.997px] relative rounded-[16px] size-full" data-name="Widget 1 - Voice">
      <Frame />
      <Frame2 />
    </div>
  );
}
