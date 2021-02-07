from aiogram import types

from peewee import *
import math
from playhouse.shortcuts import model_to_dict
from config import (
    DB_FILE,
    ITEMS_PER_PAGE
)

db = SqliteDatabase(DB_FILE)


class BaseModel(Model):
    class Meta:
        abstract = True
        database = db


class User(BaseModel):
    MENU_CHOICE = [
        (0, 'wor'),
        (1, 'cus')
    ]
    user_id = IntegerField(unique=True)
    menu_state = IntegerField(choices=MENU_CHOICE)
    balance = IntegerField(default=0)
    language = CharField(max_length=2, default='en')


class Ticket(BaseModel):
    STATUSES = [
        (0, 'waiting'),
        (1, 'work'),
        (2, 'done')
    ]
    user = ForeignKeyField(User, backref='tickets')
    body = CharField()
    price = CharField()
    executor = ForeignKeyField(User, backref='tasks', default=None, null=True)
    status = IntegerField(choices=STATUSES)


class Offer(BaseModel):
    ticket = ForeignKeyField(Ticket, backref='offers')
    message = CharField()
    price = CharField()
    executor = ForeignKeyField(User, backref='offers', default=None, null=True)


class DBCommands:
    # ------------- USER ACTION -------------
    @staticmethod
    async def get_user(user_id) -> User:
        return User.get_or_none(User.user_id == user_id)

    async def add_new_user(self):
        user = types.User.get_current()
        old_user = await self.get_user(user.id)
        if old_user:
            return old_user
        new_user = User.create(user_id=user.id, menu_state=1, balance=0)
        return new_user

    async def set_language(self, language):
        user_id = types.User.get_current().id
        user = await self.get_user(user_id)
        if user.language == language:
            return False, user
        user.language = language
        user.save()
        return True, user

    async def switch_state(self):
        user_id = types.User.get_current().id
        user = await self.get_user(user_id)
        user.menu_state = (user.menu_state + 1) % 2
        user.save()
        return user

    async def balance_changer(self, delta):
        user_id = types.User.get_current().id
        user = await self.get_user(user_id)
        user.balance += delta
        user.save()
        return user

    # ------------- TICKET ACTION -------------

    async def create_ticket(self, user_id, user_data):
        Ticket.create(user=await self.get_user(user_id), body=user_data['body'], price=user_data['price'], status=0)

    async def get_user_tickets(self, user_id, page=None):
        user = await self.get_user(user_id)
        pages = None
        if not page:
            tickets = user.tickets
        else:
            main_req = Ticket.select().where(Ticket.user == user).order_by(Ticket.id)
            tickets = main_req.paginate(page, ITEMS_PER_PAGE)
            pages = math.ceil(main_req.count() / ITEMS_PER_PAGE)
        return tickets, pages

    @staticmethod
    async def get_ticket_by_id(ticket_id):
        return Ticket.get_or_none(Ticket.id == ticket_id)


async def create_db():
    db.create_tables([User, Ticket, Offer])
