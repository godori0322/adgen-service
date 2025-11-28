import { useEffect, useState } from "react";
import { deleteMe, getMyPageRequest, putMyPageRequest } from "../../api/auth";
import AlertModal from "../../components/common/AlertModal";
import ConfirmModal from "../../components/common/ConfirmModal";
import SkeletonLoader from "../../components/common/SkeletonLoader";
import { PageTitle, SectionTitle } from "../../components/common/Title";
import HourRow from "../../components/myPage/HourRow";
import MenuTagEditor from "../../components/myPage/MenuTagEditor";
import ProfileRow from "../../components/myPage/ProfileRow";
import { useAuth } from "../../context/AuthContext";
import { useChat } from "../../context/ChatContext";

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
  const { logout } = useAuth();
  const { resetMessages } = useChat();
  const [editMode, setEditMode] = useState(false);
  const [user, setUser] = useState<MyPageUser | null>(null);
  const [draft, setDraft] = useState<MyPageUser | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showAlert, setShowAlert] = useState(false);
  const [alertContent, setAlertContent] = useState({
    title: "",
    message: "",
    onClose: () => {},
  });
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
    if (!draft) return;
    setDraft({ ...draft, menuItems: [...draft?.menuItems, value] });
  };
  const removeMenuItem = (index: number) => {
    if (!draft) return;
    setDraft({ ...draft, menuItems: draft.menuItems.filter((_, idx) => idx !== index) ?? [] });
  };

  // 저장/취소 handler
  const handleSave = async () => {
    if (!draft || !user) return;
    const payload = {
      business_type: draft.businessType,
      location: draft.location,
      business_hours: `${draft.openTime}-${draft.closeTime}`,
      menu_items: draft.menuItems,
    };
    try {
      await putMyPageRequest(payload);
      setUser({ ...draft });
    } catch (err: any) {
      setAlertContent({
        title: "오류",
        message: err.message || "저장 중 오류가 발생하였습니다.",
        onClose: () => {
          setShowAlert(false);
        },
      });
      setShowAlert(true);
    }
    setEditMode(false);
  };
  const handleCancel = () => {
    if (user) setDraft({ ...user });
    setEditMode(false);
  };
  const handleDeleteConfirm = async () => {
    try {
      const res = await deleteMe();
      setShowDeleteModal(false);

      // 모달 띄우기
      setAlertContent({
        title: "회원 탈퇴 완료",
        message: res.message,
        onClose: () => {
          resetMessages();
          logout();
        },
      });
      setShowAlert(true);
    } catch (err: any) {
      setAlertContent({
        title: "오류",
        message: err.message || "오류가 발생했습니다.",
        onClose: () => setShowAlert(false),
      });
      setShowAlert(true);
    }
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
            <button
              onClick={() => setShowDeleteModal(true)}
              className="w-full mt-6 text-sm text-red-500 hover:text-red-600"
            >
              회원탈퇴
            </button>
          </>
        )}
      </section>
      {showDeleteModal && (
        <ConfirmModal
          title="회원탈퇴"
          message={`정말 탈퇴하시겠습니까?\n삭제된 데이터는 복구할 수 없습니다.`}
          confirmText="탈퇴하기"
          cancelText="취소"
          onConfirm={handleDeleteConfirm}
          onCancel={() => setShowDeleteModal(false)}
        />
      )}
      {showAlert && (
        <AlertModal
          title={alertContent.title}
          message={alertContent.message}
          onClose={alertContent.onClose}
        />
      )}
    </div>
  );
}
