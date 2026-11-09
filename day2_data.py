data = [
    {"name": "A", "value": 10},
    {"name": "B", "value": 25},
    {"name": "C", "value": 15}
]

result = [
    item["name"]
    for item in data
    if item["value"] > 12
]

print(result)