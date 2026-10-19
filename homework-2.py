import asyncio
from time import perf_counter

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class Data(BaseModel):
    numbers: list[int | float]
    delays: list[int | float]


class Result(BaseModel):
    number: int | float
    square: int | float
    delay: int | float
    time: float


class Answer(BaseModel):
    results: list[Result]
    total_time: float
    parallel_faster_than_sequential: bool


async def calculate_one(number: int | float, delay: int | float) -> Result:
    start = perf_counter()
    await asyncio.sleep(delay)
    return Result(
        number=number,
        square=number ** 2,
        delay=delay,
        time=round(perf_counter() - start, 2),
    )


@app.post("/api/calculate/", response_model=Answer)
async def calculate(data: Data) -> Answer:
    if len(data.numbers) != len(data.delays):
        raise HTTPException(
            status_code=400,
            detail="The numbers and delays lists must have the same length",
        )

    start = perf_counter()
    results = await asyncio.gather(
        *[
            calculate_one(number, delay)
            for number, delay in zip(data.numbers, data.delays)
        ]
    )
    total_time = round(perf_counter() - start, 2)

    return Answer(
        results=results,
        total_time=total_time,
        parallel_faster_than_sequential=total_time < sum(r.time for r in results),
    )
