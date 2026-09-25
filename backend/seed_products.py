# Product seeding is intentionally separate from startup.
# After assets are uploaded, map the real product image paths and set prices here.
# Run with: python -m backend.seed_products
from .main import Session, Game, Product
from sqlalchemy import select
import asyncio

async def main():
    async with Session() as db:
        games=(await db.execute(select(Game))).scalars().all()
        by={g.slug:g for g in games}
        examples=[
          ("wuthering-waves","300 Lunite","Paketlar","assets/games/wuthering-waves/products/300-lunite.png",35000,"topup"),
          ("wuthering-waves","Lunite Subscription","Obunalar","assets/games/wuthering-waves/products/lunite-subscription.png",55000,"subscription"),
          ("genshin","300 Genesis Crystals","Paketlar","assets/games/genshin/products/300-genesis-crystals.png",35000,"topup"),
          ("hsr","300 Oneiric Shard","Paketlar","assets/games/hsr/products/300-oneiric-shard.png",35000,"topup"),
          ("pgr","5 Rainbow Cards","Paketlar","assets/games/pgr/products/5-rainbow-cards.png",35000,"topup"),
          ("zzz","300 Monochrome","Paketlar","assets/games/zzz/products/300-monochrome.png",35000,"topup"),
          ("endfield","12 Origeometry","Paketlar","assets/games/endfield/products/12-origeometry.png",35000,"topup"),
          ("nte","300 Riftcrystals","Paketlar","assets/games/nte/products/300-riftcrystals.png",35000,"topup")
        ]
        for slug,name,cat,img,price,typ in examples:
            if slug in by: db.add(Product(game_id=by[slug].id,name=name,category=cat,image=img,price=price,product_type=typ))
        await db.commit()
asyncio.run(main())
