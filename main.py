import requests
import dotenv
import os
import time
from terminaltables import AsciiTable
from statistics import mean

HH_MOSCOW_AREA_ID = 1
SJ_MOSCOW_TOWN_ID = 4
PAGE_SIZE = 100


def estimate_rub_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) // 2
    if salary_from:
        return int(salary_from * 1.2)
    if salary_to:
        return int(salary_to * 0.8)
    return None


def fetch_hh_vacancy_stats(languages):
    url = "https://api.hh.ru/vacancies"
    stats = {}

    for language in languages:
        params = {
            "text": language,
            "area": HH_MOSCOW_AREA_ID,
            "per_page": PAGE_SIZE,
            "page": 0,
        }
        salaries = []
        while True:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()

            for vacancy in payload["items"]:
                salary_block = vacancy.get("salary")
                if salary_block and salary_block["currency"] == "RUR":
                    salary = estimate_rub_salary(
                        salary_block["from"],
                        salary_block["to"],
                    )
                    if salary:
                        salaries.append(salary)

            if payload["page"] >= payload["pages"] - 1:
                break
            params["page"] += 1
            time.sleep(1)

        stats[language] = {
            "vacancies_found": payload["found"],
            "vacancies_processed": len(salaries),
            "average_salary": int(mean(salaries)) if salaries else None,
        }
    return stats


def fetch_superjob_vacancy_stats(api_key, languages):
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {"X-Api-App-Id": api_key}
    stats = {}

    for language in languages:
        params = {
            "town": SJ_MOSCOW_TOWN_ID,
            "keyword": language,
            "count": PAGE_SIZE,
            "page": 0,
        }
        salaries = []
        while True:
            response = requests.get(
                url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()

            for vacancy in payload["objects"]:
                if vacancy.get("currency", "").lower() == "rub":
                    salary = estimate_rub_salary(
                        vacancy["payment_from"],
                        vacancy["payment_to"],
                    )
                    if salary:
                        salaries.append(salary)

            if not payload.get("more"):
                break
            params["page"] += 1

        stats[language] = {
            "vacancies_found": payload.get("total", len(salaries)),
            "vacancies_processed": len(salaries),
            "average_salary": int(mean(salaries)) if salaries else None,
        }
    return stats


def print_stats_table(title, language_stats):
    table_data = [
        ['Язык', 'Найдено', 'Обработано', 'Средняя ЗП']
    ]
    for language, stat in language_stats.items():
        avg = stat['average_salary'] or '-'
        table_data.append([
            language,
            stat['vacancies_found'],
            stat['vacancies_processed'],
            avg,
        ])
    print(AsciiTable(table_data, title).table)


def main():
    dotenv.load_dotenv()
    superjob_api = os.getenv("SUPERJOB_API_KEY")

    languages = [
        "JavaScript",
        "Java",
        "Python",
        "PHP",
        "1С",
        "C++",
        "C#",
        "C",
        "Go",
        "Lua"]

    hh_stats = fetch_hh_vacancy_stats(languages)
    sj_stats = fetch_superjob_vacancy_stats(superjob_api, languages)

    print_stats_table('HeadHunter Moscow', hh_stats)
    print()
    print_stats_table('SuperJob Moscow', sj_stats)


if __name__ == "__main__":
    main()
