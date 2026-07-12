from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_contact = State()


class EditProfile(StatesGroup):
    waiting_for_name = State()
    waiting_for_contact = State()
