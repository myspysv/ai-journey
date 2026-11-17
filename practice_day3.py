def calculate_avg(numbers: list[int]) -> float:
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)

res = calculate_avg([])
print(res)