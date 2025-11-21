import { useEffect, useState } from "react";
import { getMyPageRequest, putMyPageRequest } from "../../api/auth";
import { PageTitle, SectionTitle } from "../../components/common/Title";
import MenuTagEditor from "../../components/myPage/MenuTagEditor";
import ProfileRow from "../../components/myPage/ProfileRow";
import HourRow from "../../components/myPage/HourRow";
import SkeletonLoader from "../../components/common/SkeletonLoader";

interface MyPageUser {
  id: number;
  userName: string;
  email: string;
  businessType: string;
  location: string;
  menuItems: string[];
  openTime: string;
  closeTime: string;
}

export default function MyPage() {
  const [editMode, setEditMode] = useState(false);
  const [user, setUser] = useState<MyPageUser | null>(null);
  const [draft, setDraft] = useState<MyPageUser | null>(null);

  const transformMyPage = (data: any) => {
    const [openTime, closeTime] = data.business_hours.split("-");

    return {
      id: data.id,
      userName: data.username,
      email: data.email,
      businessType: data.business_type,
      location: data.location,
      menuItems: JSON.parse(data.menu_items),
      openTime,
      closeTime,
    };
  };

  useEffect(() => {
    async function loadMyPage() {
      const data = await getMyPageRequest();
      const transformed = transformMyPage(data);
      setTimeout(() => {
        setUser(transformed);
        setDraft(transformed);
      }, 300);
    }
    loadMyPage();
  }, []);

  // handler
  const handleChange = (key: keyof MyPageUser, value: string) => {
    setDraft((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  // 메뉴 handler
  const addMenuItem = (value: string) => {
    if(!draft) return;
    setDraft({...draft, menuItems: [...draft?.menuItems, value]});
  };
  const removeMenuItem = (index: number) => {
    if(!draft) return;
    setDraft({ ...draft, menuItems: draft.menuItems.filter((_, idx) => idx !== index) ?? [] });
  };

  // 저장/취소 handler
  const handleSave = async() => {
    if (!draft || !user) return;
    const payload = {
      business_type: draft.businessType,
      location: draft.location,
      business_hours: `${draft.openTime}-${draft.closeTime}`,
      menu_items: draft.menuItems,
    };
    try {
      await putMyPageRequest(payload);
      setUser({...draft})
    } catch (err) {
      alert("저장 중 오류가 발생하였습니다.")
    }
    setEditMode(false);
  };
  const handleCancel = () => {
    if (user) setDraft({ ...user });
    setEditMode(false);
  };


  return (
    <div className="relative pb-32">
      <PageTitle variant="section">마이페이지</PageTitle>
      <section className="bg-white shadow rounded-xl p-5 mt-6">
        <SectionTitle>내 정보</SectionTitle>
        {!draft ? (
          <SkeletonLoader />
        ) : (
          <>
            <div className="space-y-2">
              <ProfileRow
                label="아이디"
                value={draft.userName ?? ""}
                editMode={false}
                onChange={(v) => handleChange("userName", v)}
              />
              {/* <ProfileRow
            label="이름"
            value={draft.name}
            editMode={editMode} 
            onChange={(v) => handleChange("name", v)}
           /> */}
              <ProfileRow
                label="업종"
                value={draft.businessType ?? ""}
                editMode={editMode}
                onChange={(v) => handleChange("businessType", v)}
              />
              <ProfileRow
                label="주소"
                value={draft.location ?? ""}
                editMode={editMode}
                onChange={(v) => handleChange("location", v)}
              />
              <HourRow
                label="영업시간"
                openTime={draft.openTime ?? ""}
                closeTime={draft.closeTime ?? ""}
                onChange={(key, value) => handleChange(key, value)}
                editMode={editMode}
              />
              <MenuTagEditor
                items={draft.menuItems ?? []}
                editMode={editMode}
                onAdd={addMenuItem}
                onRemove={removeMenuItem}
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
          </>
        )}
      </section>
    </div>
  );
}
