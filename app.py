import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from flask import Flask, request
from sqlalchemy.orm import Session

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)

print("Подключение настроено")

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, DateTime, String
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    visited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    ip_address: Mapped[str] = mapped_column(String(45))

Base.metadata.create_all(engine)

print("Таблица visits создана")

app = Flask(__name__) 

@app.route("/hello", methods=["GET"])
def hello():
    current_time = datetime.now()
    client_ip = request.remote_addr

    with Session(engine) as session:
        visit = Visit(
            visited_at=current_time,
            ip_address=client_ip
        )

        session.add(visit)
        session.commit()

    return "Hello", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
