from __future__ import annotations
import os, json, secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Numeric, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./database/game_donat.db"
    secret_key: str = "change-me"
    admin_ids: str = ""
    card_number: str = ""
    card_owner: str = ""
    referral_enabled: bool = True
    referral_discount: int = 5000
    referral_subscription_limit: int = 3
    class Config:
        env_file = "config/.env"
        extra = "ignore"

settings = Settings()
Path("database").mkdir(exist_ok=True)
Path("uploads/receipts").mkdir(parents=True, exist_ok=True)
engine = create_async_engine(settings.database_url, future=True)
Session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[str]=mapped_column(String(64), unique=True, index=True)
    name: Mapped[str]=mapped_column(String(200), default="User")
    balance: Mapped[int]=mapped_column(Integer, default=0)
    referral_code: Mapped[str]=mapped_column(String(32), unique=True, index=True)
    referred_by_id: Mapped[Optional[int]]=mapped_column(ForeignKey("users.id"), nullable=True)
    discount_uses: Mapped[int]=mapped_column(Integer, default=0)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class Game(Base):
    __tablename__="games"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    slug: Mapped[str]=mapped_column(String(80), unique=True)
    name: Mapped[str]=mapped_column(String(120))
    image: Mapped[str]=mapped_column(String(300))
    font: Mapped[Optional[str]]=mapped_column(String(300), nullable=True)
    active: Mapped[bool]=mapped_column(Boolean, default=True)

class Product(Base):
    __tablename__="products"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    game_id: Mapped[int]=mapped_column(ForeignKey("games.id"), index=True)
    name: Mapped[str]=mapped_column(String(200))
    category: Mapped[str]=mapped_column(String(80), default="Paketlar")
    image: Mapped[str]=mapped_column(String(300))
    price: Mapped[int]=mapped_column(Integer)
    product_type: Mapped[str]=mapped_column(String(40), default="topup")
    active: Mapped[bool]=mapped_column(Boolean, default=True)

class Order(Base):
    __tablename__="orders"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int]=mapped_column(ForeignKey("products.id"))
    status: Mapped[str]=mapped_column(String(30), default="pending")
    account_data: Mapped[str]=mapped_column(Text, default="{}")
    price: Mapped[int]=mapped_column(Integer)
    discount_applied: Mapped[int]=mapped_column(Integer, default=0)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]]=mapped_column(DateTime, nullable=True)

class Deposit(Base):
    __tablename__="deposits"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"))
    requested_amount: Mapped[int]=mapped_column(Integer)
    credited_amount: Mapped[int]=mapped_column(Integer, default=0)
    receipt_path: Mapped[Optional[str]]=mapped_column(String(500), nullable=True)
    status: Mapped[str]=mapped_column(String(30), default="pending")
    created_at: Mapped[datetime]=mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class ReferralReward(Base):
    __tablename__="referral_rewards"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    referrer_id: Mapped[int]=mapped_column(ForeignKey("users.id"))
    referred_user_id: Mapped[int]=mapped_column(ForeignKey("users.id"), unique=True)
    status: Mapped[str]=mapped_column(String(30), default="pending")
    created_at: Mapped[datetime]=mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    confirmed_at: Mapped[Optional[datetime]]=mapped_column(DateTime, nullable=True)

class SupportTicket(Base):
    __tablename__="support_tickets"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"))
    message: Mapped[str]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(30), default="open")
    created_at: Mapped[datetime]=mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class UserIn(BaseModel):
    telegram_id: str
    name: str = "User"
    referral_code: Optional[str] = None

class OrderIn(BaseModel):
    telegram_id: str
    product_id: int
    account_data: dict

class DepositIn(BaseModel):
    telegram_id: str
    amount: int

class DepositCredit(BaseModel):
    credited_amount: int

class ReferralConfirm(BaseModel):
    referred_user_id: int

class TicketIn(BaseModel):
    telegram_id: str
    message: str

app=FastAPI(title="Game Donat API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

async def user_by_tg(db, tg:str):
    return (await db.execute(select(User).where(User.telegram_id==tg))).scalar_one_or_none()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with Session() as db:
        count=(await db.execute(select(Game))).scalars().all()
        if not count:
            games=[
                ("wuthering-waves","Wuthering Waves","assets/games/wuthering-waves/icon.png"),
                ("pgr","Punishing: Gray Raven","assets/games/pgr/icon.png"),
                ("genshin","Genshin Impact","assets/games/genshin/icon.webp"),
                ("hsr","Honkai: Star Rail","assets/games/hsr/icon.png"),
                ("zzz","Zenless Zone Zero","assets/games/zzz/icon.png"),
                ("endfield","Arknights: Endfield","assets/games/endfield/icon.png"),
                ("nte","Neverness to Everness","assets/games/nte/icon.png"),
            ]
            db.add_all([Game(slug=s,name=n,image=i) for s,n,i in games])
            await db.commit()

@app.get("/api/health")
async def health(): return {"ok":True}

@app.post("/api/users")
async def create_user(data:UserIn):
    async with Session() as db:
        u=await user_by_tg(db,data.telegram_id)
        if u: return {"id":u.id,"balance":u.balance,"referral_code":u.referral_code}
        referrer=None
        if data.referral_code:
            referrer=(await db.execute(select(User).where(User.referral_code==data.referral_code))).scalar_one_or_none()
        u=User(telegram_id=data.telegram_id,name=data.name,referral_code=secrets.token_urlsafe(8),referred_by_id=referrer.id if referrer else None)
        db.add(u); await db.commit(); await db.refresh(u)
        if referrer:
            db.add(ReferralReward(referrer_id=referrer.id,referred_user_id=u.id)); await db.commit()
        return {"id":u.id,"balance":u.balance,"referral_code":u.referral_code}

@app.get("/api/games")
async def games():
    async with Session() as db:
        rows=(await db.execute(select(Game).where(Game.active==True))).scalars().all()
        return [{"id":g.id,"slug":g.slug,"name":g.name,"image":g.image,"font":g.font} for g in rows]

@app.get("/api/games/{game_id}/products")
async def products(game_id:int):
    async with Session() as db:
        rows=(await db.execute(select(Product).where(Product.game_id==game_id,Product.active==True))).scalars().all()
        return [{"id":p.id,"name":p.name,"category":p.category,"image":p.image,"price":p.price,"product_type":p.product_type} for p in rows]

@app.get("/api/me")
async def me(telegram_id:str):
    async with Session() as db:
        u=await user_by_tg(db,telegram_id)
        if not u: raise HTTPException(404,"User not found")
        return {"id":u.id,"name":u.name,"balance":u.balance,"referral_code":u.referral_code,"discount_uses":u.discount_uses,"discount_limit":settings.referral_subscription_limit}

@app.post("/api/orders")
async def create_order(data:OrderIn):
    async with Session() as db:
        u=await user_by_tg(db,data.telegram_id)
        if not u: raise HTTPException(404,"User not found")
        p=(await db.execute(select(Product).where(Product.id==data.product_id,Product.active==True))).scalar_one_or_none()
        if not p: raise HTTPException(404,"Product not found")
        discount=0
        if p.product_type=="subscription" and settings.referral_enabled and u.discount_uses < settings.referral_subscription_limit:
            # A reward is granted per confirmed referral; consume only when available.
            confirmed=(await db.execute(select(ReferralReward).where(ReferralReward.referrer_id==u.id,ReferralReward.status=="confirmed"))).scalars().all()
            available=max(0,len(confirmed)-u.discount_uses)
            if available>0: discount=settings.referral_discount
        total=max(0,p.price-discount)
        if u.balance < total: raise HTTPException(400,"Insufficient balance")
        u.balance-=total
        if discount: u.discount_uses+=1
        o=Order(user_id=u.id,product_id=p.id,account_data=json.dumps(data.account_data),price=total,discount_applied=discount)
        db.add(o); await db.commit(); await db.refresh(o)
        return {"id":o.id,"status":o.status,"price":o.price,"discount":discount,"balance":u.balance}

@app.get("/api/orders")
async def orders(telegram_id:str):
    async with Session() as db:
        u=await user_by_tg(db,telegram_id)
        if not u: raise HTTPException(404,"User not found")
        rows=(await db.execute(select(Order).where(Order.user_id==u.id).order_by(Order.id.desc()))).scalars().all()
        return [{"id":o.id,"product_id":o.product_id,"status":o.status,"price":o.price,"discount":o.discount_applied,"created_at":o.created_at.isoformat(),"completed_at":o.completed_at.isoformat() if o.completed_at else None} for o in rows]

@app.post("/api/deposits")
async def deposit(data:DepositIn, receipt:UploadFile=File(...)):
    async with Session() as db:
        u=await user_by_tg(db,data.telegram_id)
        if not u: raise HTTPException(404,"User not found")
        if data.amount<=0: raise HTTPException(400,"Invalid amount")
        safe=f"{secrets.token_hex(12)}_{receipt.filename or 'receipt'}".replace("/","_")
        path=Path("uploads/receipts")/safe
        path.write_bytes(await receipt.read())
        d=Deposit(user_id=u.id,requested_amount=data.amount,receipt_path=str(path))
        db.add(d); await db.commit(); await db.refresh(d)
        return {"id":d.id,"status":d.status,"message":"Chek adminga yuborildi."}

@app.post("/api/admin/deposits/{deposit_id}/credit")
async def credit_deposit(deposit_id:int,data:DepositCredit,x_admin_id:str=Header("")):
    if x_admin_id not in [x.strip() for x in settings.admin_ids.split(",") if x.strip()]: raise HTTPException(403,"Forbidden")
    async with Session() as db:
        d=await db.get(Deposit,deposit_id)
        if not d or d.status!="pending": raise HTTPException(404,"Deposit not found")
        u=await db.get(User,d.user_id)
        d.credited_amount=data.credited_amount; d.status="approved"; u.balance+=data.credited_amount
        await db.commit()
        return {"ok":True,"balance":u.balance}

@app.post("/api/admin/referrals/confirm")
async def confirm_referral(data:ReferralConfirm,x_admin_id:str=Header("")):
    if x_admin_id not in [x.strip() for x in settings.admin_ids.split(",") if x.strip()]: raise HTTPException(403,"Forbidden")
    async with Session() as db:
        r=(await db.execute(select(ReferralReward).where(ReferralReward.referred_user_id==data.referred_user_id))).scalar_one_or_none()
        if not r: raise HTTPException(404,"Referral not found")
        r.status="confirmed"; r.confirmed_at=datetime.now(timezone.utc); await db.commit()
        return {"ok":True}

@app.post("/api/support")
async def support(data:TicketIn):
    async with Session() as db:
        u=await user_by_tg(db,data.telegram_id)
        if not u: raise HTTPException(404,"User not found")
        db.add(SupportTicket(user_id=u.id,message=data.message)); await db.commit()
        return {"ok":True}

@app.get("/api/payment-config")
async def payment_config():
    return {"manual_receipt":True,"google_pay":False,"click":False,"octo":False,"card_gateway":False,"card_number":settings.card_number,"card_owner":settings.card_owner}

@app.get("/api/referral/config")
async def referral_config():
    return {"enabled":settings.referral_enabled,"discount":settings.referral_discount,"subscription_limit":settings.referral_subscription_limit}
