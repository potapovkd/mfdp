import os
from smolagents import tool
from sqlalchemy import create_engine, text

# Получаем параметры подключения из переменных окружения (docker-compose)
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pricing_optimization")
DB_USER = os.getenv("DB_USER", "pricing_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "pricing_password")

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

@tool
def sql_engine(query: str) -> str:
    """
    Позволяет выполнять SQL-запросы к основной базе данных (PostgreSQL).
    Доступные таблицы:
    
    products:
        id: INTEGER, primary key
        user_id: INTEGER, внешний ключ на users.id
        name: TEXT, название товара
        brand_name: TEXT, бренд
        category_name: TEXT, категория
        item_description: TEXT, описание
        item_condition_id: INTEGER, 1-5 (1=новый, 5=плохое)
        shipping: INTEGER, 0=покупатель платит, 1=продавец платит
        created_at: DATETIME
    price_predictions:
        id: INTEGER, primary key
        product_id: INTEGER, внешний ключ на products.id
        predicted_price: FLOAT, предсказанная цена
        confidence_score: FLOAT, уверенность
        model_version: TEXT
        created_at: DATETIME
    tasks:
        id: INTEGER, primary key
        product_id: INTEGER, внешний ключ на products.id
        status: TEXT (new, queued, processing, completed, failed)
        type: TEXT
        input_data: TEXT (json)
        result: TEXT
        created_at: DATETIME
        updated_at: DATETIME
    users:
        id: INTEGER, primary key
        email: TEXT
        username: TEXT
        password_hash: TEXT
        balance: FLOAT
        created_at: DATETIME
    
    Args:
        query: SQL-запрос (SELECT ...)
    """
    output = ""
    with engine.connect() as con:
        rows = con.execute(text(query))
        for row in rows:
            output += "\n" + str(row)
    return output 