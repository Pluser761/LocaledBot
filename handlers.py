from typing import Union

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import (Message,
                           CallbackQuery,
                           ReplyKeyboardRemove,
                           InlineKeyboardMarkup,
                           InlineKeyboardButton,
                           ContentTypes,
                           LabeledPrice,
                           PreCheckoutQuery)

import database
from callback_data import *
from loader import dp, bot, _
from reply_keyboards import *
from states import (NewTicket,
                    NewOffer,
                    NewPayment)

from config import (
    PAYMENT_TOKEN
)

db = database.DBCommands()


@dp.message_handler(CommandStart())
async def start_command(msg: Message):
    user = await db.add_new_user()
    await bot.send_message(chat_id=msg.chat.id,
                           text=_("Main menu"),
                           reply_markup=cus_main_menu(user=user))


# ------------- MENUS -------------

@dp.callback_query_handler(cb_menu.filter(menu='cus'))
@dp.callback_query_handler(cb_menu.filter(menu='wor'))
async def main_menu_callback(call: CallbackQuery):
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    user = await db.get_user(call.from_user.id)
    await bot.send_message(chat_id=call.from_user.id,
                           text=_("Main menu"),
                           reply_markup=main_menu(user=user))


@dp.message_handler(lambda msg: msg.text[0] == '📝')
@dp.callback_query_handler(cb_menu.filter(menu='create_ticket'))
async def new_ticket_info(data: Union[Message, CallbackQuery]):
    text = _("Body ticket information")
    if isinstance(data, Message):
        await data.answer(text, reply_markup=ReplyKeyboardRemove())
    else:
        await data.message.answer(text, reply_markup=ReplyKeyboardRemove())
        await data.message.delete_reply_markup()
    await NewTicket.wf_body.set()


@dp.message_handler(state=NewTicket.wf_body, content_types=ContentTypes.TEXT)
async def new_ticket_price(msg: Message, state: FSMContext):
    await state.update_data(body=msg.text)
    await NewTicket.next()
    await msg.answer(_("Price ticket information"))


@dp.message_handler(state=NewTicket.wf_price, content_types=ContentTypes.TEXT)
async def new_ticket_confirmation(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        await msg.reply(text=_("Price must be number"))
        return
    user_data = await state.get_data()
    await state.update_data(price=msg.text)
    await NewTicket.next()
    await msg.answer(_("Ticket: {body}\\.\nCost: {price} rub\\.\nConfirm?").format(
        body=user_data['body'],
        price=msg.text
    ), reply_markup=yes_no_menu())


@dp.message_handler(state=NewTicket.wf_aff, content_types=ContentTypes.TEXT)
async def new_ticket_finalization(msg: Message, state: FSMContext):
    if msg.text == _("Yes"):
        answer = _("Added")
        await db.create_ticket(user_id=msg.from_user.id, user_data=await state.get_data())
    else:
        answer = _("Cancelled")
    ret = await msg.answer(answer)
    user = await db.get_user(msg.from_user.id)
    await msg.answer(_("Main menu"), reply_markup=cus_main_menu(user))
    await bot.delete_message(chat_id=ret.chat.id, message_id=ret.message_id)
    await state.finish()


@dp.message_handler(lambda msg: msg.text[0] == '📖')
@dp.callback_query_handler(cb_menu_page.filter(menu='tickets'))
async def cus_tickets_menu(data: Union[Message, CallbackQuery]):
    if isinstance(data, Message):
        page = 1
    else:
        page = int(data.data.split(':')[-1])
    tickets, pages = await db.get_user_tickets(data.from_user.id, page)
    board, flag = tickets_menu(tickets, page, pages)
    if isinstance(data, Message):
        await data.answer(text=_('Your tickets') if flag else _('No tickets, create'), reply_markup=board)
    else:
        if data.message.text != _('Your tickets'):
            await data.message.edit_text(text=_('Your tickets'), reply_markup=board)
        else:
            await data.message.edit_reply_markup(reply_markup=board)
        await bot.answer_callback_query(data.id)


@dp.callback_query_handler(cb_item_id_action.filter(item='ticket', action='0'))
async def ticket(call: CallbackQuery):
    ticket_info = await db.get_ticket_by_id(call.data.split(':')[-2])
    await call.message.edit_text(text=_("Задание № {id}\n{body}\n{price} рублей").format(
        id=ticket_info.id,
        body=ticket_info.body,
        price=ticket_info.price
    ), reply_markup=ticket_menu(ticket_info, ticket_info.user.balance >= 20))
    await bot.answer_callback_query(call.id)


@dp.callback_query_handler(cb_item_id_action.filter(item='ticket', action='top'))
async def top_ticket(call: CallbackQuery):
    id = call.data.split(':')[-2]
    user = await db.balance_changer(-20)
    if user.balance < 20:
        t = call.message.reply_markup.inline_keyboard
        t.pop(0)
        await call.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=t))
    await call.message.answer(text=f'{id} ticket topped', reply_markup=main_menu(user))


@dp.callback_query_handler(cb_item_id_action.filter(item='ticket', action='offers'))
async def offers_ticket(call: CallbackQuery):
    pass


@dp.callback_query_handler(cb_item_id_action.filter(item='ticket', action='delete'))
async def delete_ticket(call: CallbackQuery):
    pass


# ------------- COMMON -------------

@dp.message_handler(lambda msg: msg.text[0] == '💰')
async def balance_start(msg: Message):
    user = await db.get_user(msg.from_user.id)
    board, text = balance_start_menu(user)
    await msg.answer(text=text, reply_markup=board)


@dp.callback_query_handler(cb_balance.filter(action='add'))
async def balance_add(call: CallbackQuery, state: FSMContext):
    switcher = call.data.split(':')[-1]
    if switcher == 'add':
        await state.update_data(sign=True)
    else:
        await state.update_data(sign=False)

    await call.message.answer(text=_("Enter amount"), reply_markup=ReplyKeyboardRemove())
    await call.message.delete()
    await NewPayment.wf_amount.set()
    await call.answer()


@dp.message_handler(state=NewPayment.wf_amount, content_types=ContentTypes.TEXT)
async def balance_invoice(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        await msg.reply(text=_("Amount must be number"))
        return
    price = int(msg.text)*100
    # ---- TODO: enable payment
    user = await db.balance_changer(int(msg.text))
    await bot.send_message(chat_id=msg.from_user.id,
                           text=_("Main menu"),
                           reply_markup=main_menu(user=user))
    await state.finish()
    return
    # ----
    data = await state.get_data()
    await state.finish()
    if data['sign']:
        await bot.send_invoice(
            msg.chat.id,
            title=_('Top up title'),
            description=_('Top up description'),
            provider_token=PAYMENT_TOKEN,
            currency='rub',
            prices=[LabeledPrice(label=msg.text, amount=price)],
            start_parameter='pay-start-param',
            payload='pay-payload'
        )


@dp.pre_checkout_query_handler(lambda query: True)
async def checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=ContentTypes.SUCCESSFUL_PAYMENT)
async def process_successful_payment(msg: Message):
    # total_amount=msg.successful_payment.total_amount // 100
    # currency=msg.successful_payment.currency
    user = await db.balance_changer(msg.successful_payment.total_amount // 100)
    await bot.send_message(chat_id=msg.from_user.id,
                           text=_("Main menu"),
                           reply_markup=main_menu(user=user))


@dp.callback_query_handler(cb_balance.filter(action='withdraw'))
async def balance_withdraw(call: CallbackQuery, state: FSMContext):
    # TODO: balance_withdraw
    pass


# ------------- SETTINGS -------------

@dp.message_handler(lambda msg: msg.text[0] == '⚙')
async def settings_message(msg: Message):
    user = await db.get_user(msg.from_user.id)
    change_text = _("I'm customer")
    if user.menu_state == 1:
        change_text = _("I'm executor")
    await msg.answer(
        text=_("Settings"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=change_text, callback_data=cb_menu.new(menu="change_state"))],
                [InlineKeyboardButton(text=_("Change language"), callback_data=cb_menu.new(menu="change_lang"))]
            ]
        ))


@dp.callback_query_handler(cb_menu.filter(menu='change_state'))
async def change_state(call: CallbackQuery):
    await db.switch_state()
    await main_menu_callback(call)


@dp.callback_query_handler(cb_menu.filter(menu='change_lang'))
async def change_language(call: CallbackQuery):
    await call.message.edit_text(
        text=_("Language"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Русский", callback_data=cb_lang.new(action='apply', data="ru"))],
                [InlineKeyboardButton(text="English", callback_data=cb_lang.new(action='apply', data="en"))]
            ]
        ))
    await bot.answer_callback_query(call.id)


@dp.callback_query_handler(cb_lang.filter(action='apply'))
async def apply_language(call: CallbackQuery):
    await call.message.edit_reply_markup()
    to_lang = call.data.split(':')[-1]
    is_changed, user = await db.set_language(to_lang)
    if is_changed:
        text = _("Language changes applied", locale=to_lang)
    else:
        text = _("Language already applied", locale=to_lang)
    await call.message.answer(text=text, reply_markup=main_menu(user))
    await call.message.delete()


@dp.message_handler(lambda msg: msg.text[0] == '⚙')
async def about(msg: Message):
    # TODO: about
    pass
"""

@dp.callback_query_handler(lambda call: call.data == 'cus_ord')
async def cus_tickets_menu_callback(call: CallbackQuery):
    board, flag = my_ord_menu_keyboard(
        Ticket.select(Ticket.body, Ticket.id).where(Ticket.user == User.get(User.user_id == call.from_user.id)).dicts())
    await call.message.edit_text(text='Ваши задания' if flag else 'Заданий нет, создайте', reply_markup=board)
    await bot.answer_callback_query(call.id)


@dp.callback_query_handler(lambda call: call.data[:3] == 'ord')
async def ord_card(call: CallbackQuery):
    ticket_id = call.data[4:]
    ticket = Ticket.get(Ticket.id == ticket_id)
    await call.message.edit_text(text=f"Задание № {ticket.id}\n{ticket.body}\n{ticket.price} рублей", reply_markup=ord_card_menu_keyboard(ticket))
    await bot.answer_callback_query(call.id)


@dp.callback_query_handler(lambda call: call.data[:4] == 'chat')
async def cus_offers_callback(call: CallbackQuery):
    ticket = Ticket.get(Ticket.id == call.data.split('_')[1])
    offers = Offer.select(Offer.message, Offer.id, Offer.price).where(Offer.ticket == ticket).dicts()
    board = my_offers_keyboard(offers, ticket.id)
    if board:
        await call.message.edit_text(text='Предложения исполнителей', reply_markup=board)
    else:
        await call.message.answer(text='Предложения нет')
    await bot.answer_callback_query(call.id)


@dp.callback_query_handler(lambda call: call.data[:4] == 'offe')
async def cus_offer_card_callback(call: CallbackQuery):
    offer_id = call.data.split('_')[1]
    offer = Offer.get(Offer.id == offer_id)
    await call.message.edit_text(text=f"Сообщение: {offer.message}.\nЦена: {offer.price}.",
                     reply_markup=offer_card_menu_keyboard(offer_id, offer.ticket.id))


@dp.message_handler(lambda msg: msg.text[0] == '💰')
async def balance(msg: Message):
    user = User.get(User.user_id == msg.from_user.id)
    board, text = balance_menu(user.balance)
    await msg.answer(text=text, reply_markup=board)


@dp.callback_query_handler(lambda call: call.data == 'give')
async def give_balance(call: CallbackQuery):
    user = User.get(User.user_id == call.from_user.id)
    user.balance += 50
    user.save()
    board = cus_menu_keyboard(user) if user.menu_state == 1 else wor_menu_keyboard(user)
    await bot.send_message(chat_id=call.message.chat.id, text='Баланс пополнен', reply_markup=board)


@dp.callback_query_handler(lambda call: call.data[:3] == 'get')
async def get_balance(call: CallbackQuery):
    user = User.get(User.user_id == call.from_user.id)
    user.balance -= 50
    user.save()
    board = cus_menu_keyboard(user) if user.menu_state == 1 else wor_menu_keyboard(user)
    await bot.send_message(chat_id=call.message.chat.id, text='Баланс списан', reply_markup=board)


@dp.message_handler(lambda msg: msg.text[0] == '📍')
async def about(msg: Message):
    title, text = about_menu()
    await msg.answer(text=title+'\n'+text)


@dp.callback_query_handler(lambda call: call.data == 'wor')
async def wor_menu(call):
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    res = User.get_or_none(User.user_id == call.from_user.id)
    if res.menu_state != 0:
        res.menu_state = 0
        res.save()
    await bot.send_message(chat_id=call.message.chat.id, text="Главное меню", reply_markup=wor_menu_keyboard(res))


@dp.message_handler(lambda msg: msg.text[0] == '🗒')
async def wor_show_tasks(msg: Message):
    pass


@dp.message_handler(lambda msg: msg.text[0] == '🗃')
async def wor_show_cats(msg: Message):
    cats = {  # load from database
        'all': 'Все'
    }
    await msg.answer(text=msg.text, reply_markup=cats_menu_keyboard(cats))


@dp.callback_query_handler(lambda call: call.data[:3] == 'cat')
async def wor_show_cat_tasks(call: CallbackQuery):
    await bot.answer_callback_query(call.id)
    pag = call.data.split('_')
    cat = pag[1]  # cat string
    page = int(pag[2])  # cat page

    pagination = 2

    board = None
    if cat == 'all':
        data = Ticket.select(Ticket.body, Ticket.id).order_by(Ticket.id).paginate(page, pagination).dicts()
        max_page = Ticket.select(Ticket.body, Ticket.id).order_by(Ticket.id).count()
        int_max = int(max_page / pagination)
        max_page = int_max if max_page % pagination == 0 else (int_max + 1)
        board = cat_tickets_menu_keyboard(data, page, max_page, cat)

    await call.message.edit_text(text='Страница №' + str(page), reply_markup=board)


@dp.callback_query_handler(lambda call: call.data[:4] == 'task')
async def wor_show_task(call: CallbackQuery):
    await bot.answer_callback_query(call.id)
    pg = call.data.split('_') # cat prom l_b callback data
    cat = pg[1]
    page = call.message.text.split(' ')[1][1:]  # page from message
    task_id = pg[2]
    ticket = Ticket.get(Ticket.id == task_id)
    await call.message.edit_text(text=f"Задание № {ticket.id}\n{ticket.body}\n{ticket.price} рублей",
                                 reply_markup=task_card_menu_keyboard(ticket, cat, page))


@dp.callback_query_handler(lambda call: call.data[:5] == 'cr_of')
async def create_offer_1(call: CallbackQuery):
    state = dp.current_state(user=call.from_user.id)
    await state.update_data(ticket_id=call.data.split('_')[2])
    await call.message.answer("Введите основную информацию", reply_markup=ReplyKeyboardRemove())
    await NewOffer.wf_body.set()


@dp.message_handler(state=NewOffer.wf_body, content_types=ContentTypes.TEXT)
async def create_offer_2(msg: Message, state: FSMContext):
    await state.update_data(body=msg.text)
    await NewOffer.next()
    await msg.answer("Введите предложение по цене")


@dp.message_handler(state=NewOffer.wf_price, content_types=ContentTypes.TEXT)
async def create_offer_3(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        await msg.reply(text="Цена должна быть числом")
        return
    user_data = await state.get_data()
    ticket = Ticket.get(Ticket.id == user_data['ticket_id'])
    await state.update_data(price=msg.text)
    await NewOffer.next()
    await msg.answer(f"Задание: {ticket.body}.\nПредложение заказчика: {ticket.price}.\nВаше сообщение: {user_data['body']}\nВаше предложение: {msg.text}\nПодтвердить?", reply_markup=yes_no_menu())


@dp.message_handler(state=NewOffer.wf_aff, content_types=ContentTypes.TEXT)
async def create_offer_4(msg: Message, state: FSMContext):
    user_data = await state.get_data()
    got_freelancer = User.get_or_none(User.user_id == msg.from_user.id)
    got_ticket = Ticket.get(user_data['ticket_id'])
    if msg.text == 'Да':
        answer = f"Добавлено"
        Offer.create(ticket=got_ticket, message=user_data['body'], price=user_data['price'], executor=got_freelancer)
    else:
        answer = f"Отменено"
    ret = await msg.answer(answer)
    await msg.answer('Главное меню', reply_markup=wor_menu_keyboard(got_freelancer))
    await bot.delete_message(chat_id=ret.chat.id, message_id=ret.message_id)
    await state.finish()

"""