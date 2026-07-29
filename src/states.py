"""🧠 وضعیت‌های FSM ربات."""
from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    name = State()
    grade = State()
    major = State()


class EditProfile(StatesGroup):
    name = State()


class AdminExamWizard(StatesGroup):
    title = State()
    grade = State()
    lessons = State()
    time = State()
    mode = State()           # دستی یا فایل
    q_text = State()
    q_opt1 = State()
    q_opt2 = State()
    q_opt3 = State()
    q_opt4 = State()
    q_correct = State()
    q_expl = State()
    q_done = State()
    import_file = State()


class AdminCardWizard(StatesGroup):
    grade = State()
    lesson = State()
    category = State()
    front = State()
    back = State()
    example = State()
    tip = State()
    import_file = State()
    # 🆕 stateهای ویرایش کارت
    edit_front = State()
    edit_back = State()
    edit_example = State()
    edit_tip = State()


class Broadcast(StatesGroup):
    text = State()
    confirm = State()


class EditContent(StatesGroup):
    value = State()


class ExamSession(StatesGroup):
    running = State()


class AdminSearch(StatesGroup):
    user = State()


class AdminLogin(StatesGroup):
    username = State()
    password = State()
