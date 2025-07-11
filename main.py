import requests
import json
import dotenv
import os
from terminaltables import AsciiTable
from statistics import mean


def predict_rub_salary_for_hh(vacancy):
    salary = vacancy.get('salary')
    if not salary or salary['currency'] != 'RUR':
        return None
    
    salary_from = salary['from']
    salary_to = salary['to']

    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    return None


def get_hh_api_response(langs):
    url = "https://api.hh.ru/vacancies"

    session = requests.Session()
    session.headers.update({'User-Agent': 'hh-stats-script'})

    stats = {}
    for lang in langs:
        base_params = {
            "text": lang,
            "area": 1,
            "per_page": 100,
            "only_with_salary": True,
        }
        count_response = session.get(url, params={**base_params, "per_page": 0}).json()
        vacancies_found = count_response["found"]

        salaries = []
        pages_to_process = min(20, (vacancies_found // 100) + 1)
        
        for page in range(pages_to_process):
            salary_params = {**base_params, "page": page}
            salary_response = session.get(url, params=salary_params).json()

            
            for vacancy in salary_response["items"]:
                salary = predict_rub_salary_for_hh(vacancy)
                if salary:
                    salaries.append(salary)

        stats[lang] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": len(salaries),
            "average_salary": int(mean(salaries)) if salaries else None
        }

    return stats


def print_hh_stats_table(stats):
    table_data = [
        ["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]
    ]
    
    for lang, data in stats.items():
        avg_salary = data['average_salary'] if data['average_salary'] is not None else "-"
        table_data.append([
            lang,
            str(data['vacancies_found']),
            str(data['vacancies_processed']),
            str(avg_salary)
        ])
    
    table = AsciiTable(table_data, "HeadHunter Moscow")
    print(table.table)


def predict_rub_salary_for_superjob(vacancy):
    salary_from = vacancy.get('payment_from')
    salary_to = vacancy.get('payment_to')
    currency = vacancy.get('currency', '').lower()
    
    if not salary_from and not salary_to:
        return None
    if currency != 'rub':
        return None
    
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    return None


def get_superjob_api_response(api_key, languages):
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {'X-Api-App-Id': api_key}
    stats = {}

    for lang in languages:
        base_params = {
            'town': 4,
            'keyword': lang,
            'count': 100
        }

        count_response = requests.get(url, headers=headers, params={**base_params, 'count': 0}).json()
        vacancies_found = count_response.get('total', 0)
        
        salaries = []
        pages_to_process = min(20, (vacancies_found // 100) + 1)

        for page in range(pages_to_process):
            salary_params = {**base_params, 'page': page}
            salary_response = requests.get(url, headers=headers, params=salary_params).json()

            for vacancy in salary_response.get('objects', []):
                salary = predict_rub_salary_for_superjob(vacancy)
                if salary:
                    salaries.append(salary)
        
        stats[lang] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': len(salaries),
            'average_salary': int(mean(salaries)) if salaries else None
        }

    return stats


def print_superjob_stats_table(stats):
    table_data = [
        ["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]
    ]
    
    for lang, data in stats.items():
        avg_salary = data['average_salary'] if data['average_salary'] is not None else "-"
        table_data.append([
            lang,
            str(data['vacancies_found']),
            str(data['vacancies_processed']),
            str(avg_salary)
        ])
    
    table = AsciiTable(table_data, "SuperJob Moscow")
    print(table.table)


def main():
    dotenv.load_dotenv()
    superjob_api = os.getenv("SUPERJOB_API_KEY")

    languages = ["JavaScript", "Java", "Python", "PHP", "1С", "C++", "C#", "C", "Go", "Lua"]

    hh_stats = get_hh_api_response(languages)
    superjob_stats = get_superjob_api_response(superjob_api, languages)

    print_hh_stats_table(hh_stats)
    print()
    print_superjob_stats_table(superjob_stats)


if __name__ == "__main__":
    main()