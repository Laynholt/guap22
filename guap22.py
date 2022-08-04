import pandas as pd
import requests
from bs4 import BeautifulSoup


def menu(table_data, date: str):
    """
    Функция для выбора и сортировки по пределенным параметрам
    :param table_data: Датафрейм pandas
    :param date: Дата актуальности данных строка
    :return: None
    """

    filename = f'guap-{date}.xlsx'
    with pd.ExcelWriter(filename) as writer:
        table_data.to_excel(writer, sheet_name='09.04.00', index=False, encoding='utf-8-sig')
        print(f"Файл сохранен как {filename}\n")

        choice = input('Нужен отфильтрованный вывод? (Например: вывести людей с баллами > 100) [да/нет]:\n>> ')
        if choice.lower() == 'да':
            end = False
            table_headers = table_data.columns

            while not end:
                sheet_name = 'Фильтр по'
                sorted_by = ''
                was_sorted = False
                didnt_choose_anything = 'Доступные параметра фильтровки закончились! :(\n'
                clipped_data = table_data

                choice = input('Фильтровать людей по количеству общих баллов? [да/нет]:\n>> ')
                if choice.lower() == 'да':
                    didnt_choose_anything = ''
                    was_sorted = True

                    try:
                        number_of_points = int(input('Введите от скольки баллов начинать (включительно):\n>> '))
                    except ValueError:
                        number_of_points = 0
                    sheet_name += f' баллам{number_of_points}'
                    sorted_by += f'имеют =>{number_of_points} баллов'
                    clipped_data = clipped_data[clipped_data[table_headers[4]] >= number_of_points]

                choice = input('Фильтровать людей по согласию на зачисление? [да/нет]:\n>> ')
                if choice.lower() == 'да':
                    didnt_choose_anything = ''
                    was_sorted = True
                    sheet_name += ' согл'

                    if len(sorted_by) != 0:
                        sorted_by += ', подали согласие на зачисление'
                    else:
                        sorted_by += 'подали согласие на зачисление'

                    clipped_data = clipped_data[clipped_data[table_headers[5]] == 'Да']

                choice = input('Фильтровать людей по оригиналам документов? [да/нет]:\n>> ')
                if choice.lower() == 'да':
                    didnt_choose_anything = ''
                    was_sorted = True
                    sheet_name += ' докам'

                    if len(sorted_by) != 0:
                        sorted_by += ', подали оригиналы документов'
                    else:
                        sorted_by += 'подали оригиналы документов'

                    clipped_data = clipped_data[clipped_data[table_headers[6]] == 'Да']

                if was_sorted:
                    print(f'Людей, которые {sorted_by}: {len(clipped_data)}')

                    choice = input('Записать результаты фильтровки в файл? [да/нет]:\n>> ')
                    if choice.lower() == 'да':
                        clipped_data.to_excel(writer, sheet_name=sheet_name, index=False, encoding='utf-8-sig')
                        print(f"Изменения сохранены в {filename}")

                choice = input(f'{didnt_choose_anything}Попробовать отфильтровать снова? [да/нет]:\n>> ')
                if choice.lower() == 'нет':
                    end = True


def get_table_data(url: str):
    """
    Функция считывает данные с сайта и возвращает датафрейм
    :param url: URL сайта
    :return: (table_data: DataFrame, date: str)
    """

    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')

    table = soup.find_all('table')
    table_data = pd.read_html(str(table))[0]
    table_headers = table_data.columns
    table_data[table_headers[1]].fillna('Нет', inplace=True)

    date = ''
    for category in soup('b', text=lambda text: text and text == 'Дата актуализации - '):
        date = category.next_sibling.strip('" \n')
    print(f'Данные актуальны на {date}')

    return table_data, date.replace(':', '-')


def main():
    url = 'https://priem.guap.ru/_lists/List_1725_14'
    table, date = get_table_data(url)
    menu(table, date)


if __name__ == '__main__':
    main()
