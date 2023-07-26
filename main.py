from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import sqlite3


bot = Bot('6654814345:AAFADR-WEbkDY_gW3d4zvjM8GL25njVWD3w')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class DeleteToDo(StatesGroup):
    id = State()


class DoneToDo(StatesGroup):
    id = State()


class ToDoForm(StatesGroup):
    title = State()
    description = State()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS todo ('
                ' id integer primary key,'
                ' title varchar(50),'
                ' description text ,'
                ' status boolean )'
                )

    conn.commit()
    cur.close()
    conn.close()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Add', callback_data='add'))
    markup.add(types.InlineKeyboardButton('Done', callback_data='done'))
    markup.add(types.InlineKeyboardButton('List', callback_data='list'))
    markup.add(types.InlineKeyboardButton('Delete', callback_data='delete'))

    await message.answer('Hello, what do you want to do?', reply_markup=markup)



@dp.message_handler(state=ToDoForm.title)
async def set_title(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['title'] = message.text

    await ToDoForm.next()
    await message.answer("Great! Now enter description of to-do:")


@dp.message_handler(state=ToDoForm.description)
async def set_description(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['description'] = message.text

        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()

        cur.execute(f'INSERT INTO todo  VALUES (NULL, "{data["title"]}", "{data["description"]}", 0)')

        conn.commit()
        cur.close()
        conn.close()

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Add', callback_data='add'))
        markup.add(types.InlineKeyboardButton('Done', callback_data='done'))
        markup.add(types.InlineKeyboardButton('List', callback_data='list'))
        markup.add(types.InlineKeyboardButton('Delete', callback_data='delete'))
        await message.answer('Created!', reply_markup=markup)

    await state.finish()


def check_id(id: str) -> str:
    if not id.isdigit():
        return f'"id" must be only integer and positive'
    return ''



@dp.message_handler(state=DeleteToDo.id)
async def delete(message: types.Message,  state: FSMContext):
    async with state.proxy() as data:
        error = check_id(message.text)
        if error:
            await DeleteToDo.id.set()
            await message.answer(error+'. Try again!')
            return

        data['id'] = message.text

        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()

        try:
            cur.execute(f'DELETE FROM todo WHERE id={data["id"]}')

            conn.commit()
        except Exception:
            await message.answer(f'to-do with such id doesn\'t exist!')
            await DeleteToDo.id.set()
            return

        cur.close()
        conn.close()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Add', callback_data='add'))
        markup.add(types.InlineKeyboardButton('Done', callback_data='done'))
        markup.add(types.InlineKeyboardButton('List', callback_data='list'))
        markup.add(types.InlineKeyboardButton('Delete', callback_data='delete'))
        await message.answer('Deleted!', reply_markup=markup)
        await state.finish()


@dp.message_handler(state=DoneToDo.id)
async def done(message: types.Message,  state: FSMContext):
    async with state.proxy() as data:
        data['id'] = message.text

        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()

        cur.execute(f'UPDATE todo SET (status) = (1) WHERE id={data["id"]}')

        conn.commit()
        cur.close()
        conn.close()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Add', callback_data='add'))
    markup.add(types.InlineKeyboardButton('Done', callback_data='done'))
    markup.add(types.InlineKeyboardButton('List', callback_data='list'))
    markup.add(types.InlineKeyboardButton('Delete', callback_data='delete'))
    await message.answer('Undated as done!', reply_markup=markup)
    await state.finish()


@dp.callback_query_handler()
async def callback(call):
    if call.data == 'add':
        await ToDoForm.title.set()
        await call.message.answer('Enter tile of new to-do:')

    elif call.data == 'list':
        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()

        cur.execute(f'SELECT * FROM todo')
        todos = cur.fetchall()
        if not todos:
            await call.message.answer('List is empty!')
            return
        info = ''
        for todo in todos:
            info += f'ID: {todo[0]}) {todo[1]}    {"[done]" if todo[3] else "[undone]":}\n' \
                    f'   {todo[2]}\n'

        cur.close()
        conn.close()

        await call.message.answer(info)

    elif call.data == 'done':
        await DoneToDo.id.set()
        await call.message.answer('Enter id of to-do:')

    elif call.data == 'delete':
        await DeleteToDo.id.set()
        await call.message.answer('Enter id of to-do:')



executor.start_polling(dp)
