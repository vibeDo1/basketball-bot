import asyncio
import os
import aiohttp

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

URL = "https://api.sofascore.com/api/v1/sport/basketball/events/live"

sent_games = set()

TOP_LEAGUES = [
    "NBA",
    "Euroleague",
    "ACB",
    "NCAA",
    "VTB",
    "BBL",
    "LKL"
]

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Статус")],
        [KeyboardButton(text="🏀 Live матчи")]
    ],
    resize_keyboard=True
)


@dp.message(Command("start"))
async def start_cmd(message: Message):

    await message.answer(
        "🏀 Basketball Signal Bot\n\n"
        "Бот ищет команды,\n"
        "проигравшие 3 четверти подряд.",
        reply_markup=keyboard
    )


@dp.message(lambda message: message.text == "📊 Статус")
async def status_handler(message: Message):

    await message.answer(
        "✅ Basketball scanner active"
    )


@dp.message(lambda message: message.text == "🏀 Live матчи")
async def games_handler(message: Message):

    try:

        async with aiohttp.ClientSession() as session:

            async with session.get(
                URL,
                headers={"User-Agent": "Mozilla/5.0"}
            ) as response:

                data = await response.json()

                events = data.get("events", [])

                text = "🏀 LIVE GAMES\n\n"

                for event in events[:10]:

                    home = event["homeTeam"]["name"]
                    away = event["awayTeam"]["name"]

                    hs = event["homeScore"]["current"]
                    aw = event["awayScore"]["current"]

                    text += f"{home} {hs}:{aw} {away}\n"

                await message.answer(text)

    except Exception as e:

        await message.answer(f"Ошибка: {e}")


async def scanner():

    await asyncio.sleep(10)

    async with aiohttp.ClientSession() as session:

        while True:

            try:

                async with session.get(
                    URL,
                    headers={"User-Agent": "Mozilla/5.0"}
                ) as response:

                    data = await response.json()

                    events = data.get("events", [])

                    for event in events:

                        try:

                            game_id = str(event["id"])

                            if game_id in sent_games:
                                continue

                            tournament = event.get(
                                "tournament",
                                {}
                            ).get(
                                "name",
                                ""
                            )

                            if not any(
                                league in tournament
                                for league in TOP_LEAGUES
                            ):
                                continue

                            home = event["homeTeam"]["name"]
                            away = event["awayTeam"]["name"]

                            home_periods = event.get(
                                "homeScore",
                                {}
                            ).get(
                                "periods",
                                []
                            )

                            away_periods = event.get(
                                "awayScore",
                                {}
                            ).get(
                                "periods",
                                []
                            )

                            if len(home_periods) < 3:
                                continue

                            q1 = home_periods[0] < away_periods[0]
                            q2 = home_periods[1] < away_periods[1]
                            q3 = home_periods[2] < away_periods[2]

                            if not (q1 and q2 and q3):
                                continue

                            current_home = event["homeScore"]["current"]
                            current_away = event["awayScore"]["current"]

                            text = (
                                f"🚨 BASKETBALL SIGNAL\n\n"
                                f"🏀 {home} vs {away}\n\n"
                                f"📉 Home team lost:\n"
                                f"Q1 ❌\n"
                                f"Q2 ❌\n"
                                f"Q3 ❌\n\n"
                                f"📊 SCORE: "
                                f"{current_home}:{current_away}\n\n"
                                f"🔥 Possible comeback"
                            )

                            await bot.send_message(
                                chat_id=CHAT_ID,
                                text=text
                            )

                            sent_games.add(game_id)

                        except Exception as e:
                            print("GAME ERROR:", e)

            except Exception as e:
                print("SCANNER ERROR:", e)

            await asyncio.sleep(30)


async def main():

    asyncio.create_task(scanner())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
