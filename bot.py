import os
import asyncio
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from dotenv import load_dotenv
from telethon import TelegramClient
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


load_dotenv()

class AnonymStates(StatesGroup):
    waiting_for_message = State()


BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_ID = int(os.getenv("BOT_ID"))

ADMINS_CHECK_MEMBERS = os.getenv("ADMINS_CHECK_MEMBERS").split(",")
ADMINS_CHECK_MEMBERS = [int(id.strip()) for id in ADMINS_CHECK_MEMBERS]



bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()


client = TelegramClient("session_name", API_ID, API_HASH)

async def get_members():
    await client.start()
    members = await client.get_participants(GROUP_ID)
    result = {}  
    for user in members:
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "None"
        if user.id == BOT_ID:
            continue
        result[user.id] = {"name": name, "username": username}
    return result


@router.message(Command("start"))
async def start_command(message: types.Message):
    if message.chat.type == 'private':
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        print(f"User ID: {user_id}, Username: {username}, First Name: {first_name}, Last Name: {last_name}")
        
		  
        if user_id in ADMINS_CHECK_MEMBERS:
            members = await get_members()
            if not members:
                await message.reply("Group has no member or access to group is blocked")
            else:
                members_text = "\n".join([f"{data['name']} ({data['username']}) - {user_id}" for user_id, data in members.items()][:50])
                await message.reply(f"Group members:\n{members_text}")



@router.message(Command("group"))
async def send_group_id(message: types.Message):
    if message.chat.type not in ["supergroup", "group"]:
        return

    if message.from_user.id not in ADMINS_CHECK_MEMBERS:
        return
    
    group_id = message.chat.id
    print(f"You group id: {group_id}")


@router.message(Command("members"))
async def send_members(message: types.Message):
    if message.chat.type != "private":
        return await message.reply("Use this command in private chat with bot.")

    if message.from_user.id not in ADMINS_CHECK_MEMBERS:
        return await message.reply("This command requires admin rights")

    members = await get_members()

    if not members:
        await message.reply("Group has no members or access to group is blocked")
    else:
        members_text = "\n".join([f"{data['name']} ({data['username']}) - {user_id}" for user_id, data in members.items()][:50])
        await message.reply(f"Group members:\n{members_text}")


@router.message(Command("anonym"))
async def get_anonymous_message(message: types.Message, state: FSMContext):
    if message.chat.type != "private":
        return await message.reply("Use this command in private chat with bot.")
    
    await state.set_state(AnonymStates.waiting_for_message)
    await message.answer("Enter message to send anonymously")

@router.message(AnonymStates.waiting_for_message)
async def proccess_message_handler(message: types.Message, state: FSMContext):
    anonym_message = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username

    result = await get_members()

    if user_id not in result:
        await state.clear()
        return

    if not anonym_message:
        await state.clear()
        return await message.reply("Message can not be empty")
    
    print(f"{username} sent: {anonym_message}")
    
    await bot.send_message(GROUP_ID, f"Your anonymous message:\n\n{anonym_message}")
    await message.reply("Message sent anonymously")
    await state.clear()

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())