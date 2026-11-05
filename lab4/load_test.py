import argparse
import asyncio
import math
import random
import time
import httpx

def report(name, results, duration):
    times = sorted(elapsed for elapsed, _ in results)
    count = len(times)

    print(f"\n{name}")
    print(f"Запросов: {count}")

    if count == 0:
        print("Нет измерений")
        return

    def percentile(p):
        index = max(0, math.ceil(count * p) - 1)
        return times[index] * 1000

    errors = sum(error for _, error in results)

    print(f"Запросов в секунду: {count / duration:.2f}")
    print(
        f"Время ответа, мс: p50={percentile(0.50):.1f}, "
        f"p95={percentile(0.95):.1f}, "
        f"p99={percentile(0.99):.1f}, "
        f"максимум={times[-1] * 1000:.1f}"
    )
    print(f"Ошибки: {errors / count * 100:.2f}%")

async def send(client, url, params, results, start, end):
    request_start = time.perf_counter()

    try:
        response = await client.get(url, params=params)
        error = not response.is_success
    except httpx.HTTPError:
        error = True

    request_end = time.perf_counter()

    # Учитываем только запросы, начатые во время замера.
    if start <= request_start < end:
        results.append((request_end - request_start, error))

async def closed_mode(client, params, results, clients, start, end):
    async def worker():
        while time.perf_counter() < end:
            await send(client, "/search", params, results, start, end)

    await asyncio.gather(*(worker() for _ in range(clients)))

async def open_mode(client, params, results, rate, start, end):
    tasks = []

    while time.perf_counter() < end:
        # Интервал между отправками имеет экспоненциальное распределение.
        await asyncio.sleep(random.expovariate(rate))

        if time.perf_counter() < end:
            tasks.append(asyncio.create_task(
                send(client, "/search", params, results, start, end)
            ))

    await asyncio.gather(*tasks)

async def monitor_health(client, results, start, end):
    tasks = []

    while time.perf_counter() < end:
        tasks.append(asyncio.create_task(
            send(client, "/health", None, results, start, end)
        ))
        await asyncio.sleep(0.1)

    await asyncio.gather(*tasks)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["closed", "open"], required=True)
    parser.add_argument("--clients", type=int, default=10)
    parser.add_argument("--rate", type=float, default=5)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--warmup", type=int, default=10)
    args = parser.parse_args()

    if args.clients < 1 or args.rate <= 0:
        parser.error("--clients и --rate должны быть больше 0")

    params = {
        "origin": "A01",
        "destination": "A02",
        "date": "2026-11-04",
    }

    measure_start = time.perf_counter() + args.warmup
    measure_end = measure_start + args.duration

    search_results = []
    health_results = []

    limits = httpx.Limits(
        max_connections=1000,
        max_keepalive_connections=1000,
    )

    async with httpx.AsyncClient(
        base_url="http://localhost:8000",
        timeout=30,
        limits=limits,
    ) as client:
        health_task = asyncio.create_task(
            monitor_health(
                client, health_results, measure_start, measure_end
            )
        )

        await asyncio.sleep(max(0, measure_start - time.perf_counter()))

        if args.mode == "closed":
            await closed_mode(
                client, params, search_results,
                args.clients, measure_start, measure_end
            )
        else:
            await open_mode(
                client, params, search_results,
                args.rate, measure_start, measure_end
            )

        await health_task

    print(f"Прогрев: {args.warmup} с; замер: {args.duration} с")
    report("Поиск /search", search_results, args.duration)
    report("GET /health", health_results, args.duration)

if __name__ == "__main__":
    asyncio.run(main())
