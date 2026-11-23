import requests
import json

url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"

def fetch_nbu_rates() -> list[dict]:
    response = requests.get(url, timeout=10)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Помилка! Сервер повернув код: {response.status_code}")
        return []

def filter_currencies(all_rates: list[dict], target_codes: list[str]) -> dict[str, dict]:
    filtered = {}
    for item in all_rates:
        if item["cc"] in target_codes:
            filtered[item["cc"]] = {
                "name": item["txt"],
                "rate": item["rate"],
                "date": item["exchangedate"]
            }
    return filtered

def save_to_json(data: dict, filename: str = "rates.json") -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print(f"Дані успішно збережено у {filename}")

def convert_uah(amount_uah: float, currency_code: str, filename: str = "rates.json") -> float:
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
    rate = data[currency_code]["rate"]
    return round((amount_uah) / rate, 2)


all_rates = fetch_nbu_rates()

if all_rates:
    filtered_rates = filter_currencies(all_rates, ["USD", "EUR", "PLN"])
    save_to_json(filtered_rates)
converted_uah = convert_uah(10000, "USD")
print(converted_uah)