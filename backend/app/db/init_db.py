from app.db.session import engine
from app.db.base import Base

# Р’РђР–РќРћ: С‡С‚РѕР±С‹ РјРѕРґРµР»Рё Р·Р°СЂРµРіРёСЃС‚СЂРёСЂРѕРІР°Р»РёСЃСЊ, РёРјРїРѕСЂС‚РёСЂСѓР№ РёС… С‚СѓС‚ (РєРѕРіРґР° РїРѕСЏРІСЏС‚СЃСЏ РїРѕР»СЏ)
# from app.models import user, employee, terminal, event, schedule  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
