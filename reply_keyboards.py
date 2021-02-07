from loader import _

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram import types

from callback_data import *


# ------------- REPLY -------------

def cus_main_menu(user, balance=0):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(_("📝 Create ticket", locale=user.language))],
            [KeyboardButton(_("📖 My tickets", locale=user.language)),
             KeyboardButton(_("💰 Balance:{balance}", locale=user.language).format(
                 balance=user.balance if balance == 0 else balance
             ))],
            [KeyboardButton(_(u"\U0001F4CD About", locale=user.language)),
             KeyboardButton(_("⚙Settings", locale=user.language))]
        ], resize_keyboard=True)


def wor_main_menu(user):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(_("My tasks", locale=user.language)),
             KeyboardButton(_("Geo finder", locale=user.language))],
            [KeyboardButton(_("Categories", locale=user.language)),
             KeyboardButton(_("💰 Balance:{balance}", locale=user.language).format(
                 balance=user.balance
             ))],
            [KeyboardButton(_(u"\U0001F4CD About", locale=user.language)),
             KeyboardButton(_("⚙Settings", locale=user.language))]
        ], resize_keyboard=True)


def main_menu(user):
    if user.menu_state == 1:
        return cus_main_menu(user)
    else:
        return wor_main_menu(user)


def yes_no_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(_("Yes")), KeyboardButton(_("No"))]
        ],
        resize_keyboard=True
    )


# ------------- INLINE -------------

def tickets_menu(tickets, page, pages):
    keyboard = []
    flag = False
    for item in tickets:
        flag = True
        keyboard.append([InlineKeyboardButton(item.body, callback_data=cb_item_id_action.new(item="ticket",
                                                                                             id=item.id,
                                                                                             action='0'))])
    if not flag:
        keyboard.append([InlineKeyboardButton(_('Create ticket'), callback_data=cb_menu.new(menu='create_ticket'))])
    elif pages != 1:
        if page == 1:
            keyboard.append([
                InlineKeyboardButton("➡️", callback_data=cb_menu_page.new(menu='tickets', page=page + 1))
            ])
        elif page == pages:
            keyboard.append([
                InlineKeyboardButton("⬅", callback_data=cb_menu_page.new(menu='tickets', page=page - 1))
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("⬅", callback_data=cb_menu_page.new(menu='tickets', page=page - 1)),
                InlineKeyboardButton("➡️", callback_data=cb_menu_page.new(menu='tickets', page=page + 1))
            ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard), flag


def ticket_menu(ticket, topup=True):
    board = []
    if topup:
        board.append([InlineKeyboardButton(_('To top (20 rub)'), callback_data=cb_item_id_action.new(item="ticket",
                                                                                                     id=ticket.id,
                                                                                                     action='top'))])
    return InlineKeyboardMarkup(inline_keyboard=board+[
        [InlineKeyboardButton(_('Offers'), callback_data=cb_item_id_action.new(item="ticket",
                                                                               id=ticket.id,
                                                                               action='offers')),
         InlineKeyboardButton(_('Delete'), callback_data=cb_item_id_action.new(item="ticket",
                                                                               id=ticket.id,
                                                                               action='delete'))],
        [InlineKeyboardButton(_('Back'), callback_data=cb_menu_page.new(menu='tickets', page=1))]
    ])


def offers_menu(tickets, page, pages):
    keyboard = []
    flag = False
    for item in tickets:
        flag = True
        keyboard.append([InlineKeyboardButton(item.body, callback_data=cb_item_id_action.new(item="ticket",
                                                                                             id=item.id,
                                                                                             action=0))])
    if not flag:
        keyboard.append([InlineKeyboardButton(_('Create ticket'), callback_data=cb_menu.new(menu='create_ticket'))])
    elif pages != 1:
        if page == 1:
            keyboard.append([
                InlineKeyboardButton("➡️", callback_data=cb_menu_page.new(menu='tickets', page=page + 1))
            ])
        elif page == pages:
            keyboard.append([
                InlineKeyboardButton("⬅", callback_data=cb_menu_page.new(menu='tickets', page=page - 1))
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("⬅", callback_data=cb_menu_page.new(menu='tickets', page=page - 1)),
                InlineKeyboardButton("➡️", callback_data=cb_menu_page.new(menu='tickets', page=page + 1))
            ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard), flag


# ------------- COMMON -------------

def balance_start_menu(user):
    board = [
        [InlineKeyboardButton(_("Top up"), callback_data=cb_balance.new(action="add"))]
    ]
    if user.balance:
        board.append([InlineKeyboardButton(_("Withdraw"), callback_data=cb_balance.new(action="withdraw"))])

    return InlineKeyboardMarkup(inline_keyboard=board), _("Action")
