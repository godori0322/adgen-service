import { useState } from "react";
import { PageTitle, SectionTitle } from "../../components/common/Title";
import ProfileRow from "../../components/myPage/ProfileRow";

export default function MyPage() {
  const [editMode, setEditMode] = useState(false);
  const [user, setUser] = useState({
    userId: "yena",
    name: "백예나",
    storeType: "카페",
    address: "서울특별시 서대문구",
  });
  const [draft, setDraft] = useState({ ...user });

  const handleChange = (key: string, value: string) => {
    setDraft((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    setUser({ ...draft });
    setEditMode(false);
  };
  const handleCancel = () => {
    setDraft(user);
    setEditMode(false);
  };

  return (
    <div className="relative pb-32">
      <PageTitle variant="section">마이페이지</PageTitle>
      <section className="bg-white shadow rounded-xl p-5 mt-6">
        <SectionTitle>내 정보</SectionTitle>
        <div className="space-y-2">
          <ProfileRow
            label="아이디"
            value={draft.userId}
            editMode={editMode}
            onChange={(v) => handleChange("userId", v)}
          />
          <ProfileRow
            label="이름"
            value={draft.name}
            editMode={editMode}
            onChange={(v) => handleChange("name", v)}
          />
          <ProfileRow
            label="업종"
            value={draft.storeType}
            editMode={editMode}
            onChange={(v) => handleChange("storeType", v)}
          />
          <ProfileRow
            label="주소"
            value={draft.address}
            editMode={editMode}
            onChange={(v) => handleChange("address", v)}
          />
        </div>
        {!editMode ? (
          <button
            className="mt-5 w-full py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600"
            onClick={() => setEditMode(true)}
          >
            정보 수정
          </button>
        ) : (
          <div className="flex gap-2 mt-5">
            <button
              className="flex-1 py-2 bg-gray-300 text-gray-800 rounded-lg font-medium hover:bg-gray-400"
              onClick={handleCancel}
            >
              취소
            </button>
            <button
              className="flex-1 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600"
              onClick={handleSave}
            >
              저장
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
