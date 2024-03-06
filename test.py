import asyncio

async def async_function(name):
    print(f"Hello, {name}!")
    await asyncio.sleep(2)
    print(f"Goodbye, {name}!")

async def main():
    # Run two asynchronous functions concurrently
    task1 = asyncio.create_task(async_function("Alice"))
    task2 = asyncio.create_task(async_function("Bob"))

    # Wait for both tasks to complete
    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    asyncio.run(main())
