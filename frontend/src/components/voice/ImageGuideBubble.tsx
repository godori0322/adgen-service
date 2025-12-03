export default function ImageGuideBubble() {
  return (
    <div className="bg-white p-5 rounded-xl shadow text-gray-800 leading-relaxed space-y-4">
      {/* 제목 */}
      <div>
        <p className="font-bold text-gray-900 text-lg">🎨📸 제품 사진 촬영 가이드</p>
        <p className="text-xs text-gray-500 mt-1">(자동 배경 제거 정확도 향상)</p>
      </div>

      {/* 핵심 3가지 */}
      <p className="text-sm font-semibold text-gray-800">
        💡 좋은 결과를 위해 아래 <span className="text-blue-600">3가지만</span> 기억해주세요!
      </p>

      <div className="space-y-3">
        <GuideItem
          number="1️⃣"
          title="제품은 화면 중앙"
          desc="한쪽 치우치면 배경으로 오인될 수 있어요."
        />
        <GuideItem number="2️⃣" title="제품 크기 20~60%" desc="너무 작거나 크면 감지가 어려워요." />
        <GuideItem
          number="3️⃣"
          title="배경은 깔끔하게"
          desc="복잡한 무늬 · 그림자 · 강한 반사는 인식 저하!"
        />
      </div>

      {/* 구분선 */}
      <div className="border-t border-gray-300 pt-3"></div>

      {/* 추가 팁 */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-gray-800">✨ 추가로 기억하면 좋아요!</p>

        <ul className="text-xs space-y-2 text-gray-600 ml-2">
          <li>
            • 여러 물체를 함께 찍지 않기
            <br />
            <span className="ml-3 text-[11px] text-gray-500">
              → 한 제품에 최적화되어 있어요 (컵 + 케이크 + 접시는 인식 어려움)
            </span>
          </li>

          <li>
            • 제품과 배경의 색상 대비 만들기
            <br />
            <span className="ml-3 text-[11px] text-gray-500">
              → 흰 컵 + 흰 테이블 ❌
              <br />→ 천/보드를 깔아 대비 ↑
            </span>
          </li>

          <li>
            • 흔들림 · 초점 흐림 주의
            <br />
            <span className="ml-3 text-[11px] text-gray-500">
              → 촬영 전 화면 탭하여 자동 초점 맞추기 ☝️
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
}

interface GuideItemProps {
  number: string;
  title: string;
  desc: string;
}

function GuideItem({ number, title, desc }: GuideItemProps) {
  return (
    <div className="flex gap-3">
      <span className="text-blue-600 font-bold text-lg">{number}</span>
      <div className="flex flex-col leading-snug">
        <span className="font-semibold">{title}</span>
        <span className="text-xs text-gray-600">{desc}</span>
      </div>
    </div>
  );
}
