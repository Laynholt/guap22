import pandas as pd
import requests
from bs4 import BeautifulSoup
import os


class ParserGuap22:
    def __init__(self, base_url, url_postfix):
        """
        Конструктор класса
        :param base_url: общий url без постфиксов (к нему будут они добавляться для перехода на другие страницы)
        :param url_postfix: постфикс страницы направлений
        """
        self.base_url = base_url
        self.courses_url = base_url + url_postfix
        self.courses_table = None
        self.courses_date = None

    def parse_table(self, url):
        """
        Метод принимает url страницы, парсит с нее таблицу с данными и дату актуальности этих данных
        :param url: Страницы
        :return: (DataFrame, str)
        """
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'lxml')

        # Парсим всю таблицу, поочередно проходясь по строкам, копируя полное содержание элементов всемте с ссылками
        table = soup.findAll('table')
        trs = table[0].findAll("tr")

        headers = []
        for th in trs[0].findAll("th"):
            headers.append(th.text)
        rows = []
        for i in range(1, len(trs)):
            tds = []
            for td in trs[i].findAll("td"):
                a = td.findAll("a")
                spans = td.findAll("span")
                inputs = td.findAll("input")
                ret = ""
                if len(a) != 0 or len(spans) != 0 or len(inputs) != 0:
                    if len(a) != 0:
                        for link in a:
                            ret += link.text + '(' + link['href'] + ') '
                    if len(spans) != 0:
                        for span in spans:
                            if span.has_attr('title'):
                                ret += span.text + '(' + span['title'] + ') '
                    if len(inputs) != 0:
                        for inp in inputs:
                            if inp.has_attr('value'):
                                if inp.has_attr('type'):
                                    if inp['type'] == "hidden":
                                        ret += inp['value']
                else:
                    ret = td.text if td.text != '' and td.text != '\n' else "NaN"
                tds.append(ret)
            rows.append(tds)
        # Преобразуем полученные данные в датафрейм
        table_data = pd.DataFrame(rows, columns=headers)

        # Ищем в html коде внутри тегов текст с данными актуальности даты
        date = ''
        for category in soup('b', text=lambda text: text and text == 'Дата актуализации - '):
            date = category.next_sibling.strip('" \n')
        print(f'Данные актуальны на {date}')

        # Ищем внутри тегов h3 и h4, которые идут подряд, название специальности и количество мест
        h3s = soup.findAll('h3')
        h4s = soup.findAll('h4')
        if len(h3s):
            print(f"{str(h3s[0]).replace('<h3>', '').replace('</h3>', '')}")
            if len(h4s):
                print(f"{str(h4s[0]).replace('<h4>', '').replace('</h4>', '').replace('<br>', '').replace('<br/>', '')}\n")

        return table_data, date

    def courses_menu(self):
        """
        Метод обработки дейтсвий пользователя на странице курсов
        :return: None
        """
        end = False
        table_headers = self.courses_table.columns

        self.courses_table.fillna(0, inplace=True)

        print('Выберете интересующее направление:')
        clipped_courses_table = pd.DataFrame(columns=table_headers)
        count = 0
        # Проходимся по-строчно по датафрейму и добавляем поля, которые имеют ссылки внутри, в новый датафрейм
        for i, row_data in self.courses_table.iterrows():
            if (row_data[table_headers[2]] != '-' and row_data[table_headers[2]] != '0') \
                    or (row_data[table_headers[3]] != '-' and row_data[table_headers[3]] != '0') \
                    or (row_data[table_headers[4]] != '-' and row_data[table_headers[4]] != '0'):
                length = len(clipped_courses_table)
                clipped_courses_table.loc[length] = row_data
                print(f'{count}] {row_data[table_headers[0]]} - {row_data[table_headers[1]]}')
                count += 1

        while not end:
            try:
                choice = int(input('>> '))
            except ValueError:
                choice = 0

            for i, row_data in clipped_courses_table.iterrows():
                if choice == i:
                    try:
                        choice = int(input(f'Выберете нужный список:\n'
                                           f'1] {table_headers[2]}\n2] {table_headers[3]}\n3] {table_headers[4]}\n>> '))
                    except ValueError:
                        choice = 1
                    if choice < 1 or choice > 3:
                        choice = 1

                    url_postfix = row_data[table_headers[choice + 1]]
                    if url_postfix == '-' or url_postfix == '0':
                        print('Текущего списка не существует!')
                    else:
                        url_postfix = url_postfix.split(')(')[1].replace(')', '').replace(' ', '')
                        course_table, course_date = self.parse_table(self.base_url + url_postfix)
                        self.current_course_menu(course_table, str(course_date).replace(':', '-'),
                                                 str(row_data[table_headers[0]]))
                    break

            choice = input('Попробовать ещё раз с другими направлениями? [да/нет]:\n>> ')
            if choice.lower() == 'да':
                os.system('clear')
                print('Выберете интересующее направление:')
                count = 0
                for i, row_data in clipped_courses_table.iterrows():
                    print(f'{count}] {row_data[table_headers[0]]} - {row_data[table_headers[1]]}')
                    count += 1
            else:
                end = True

    def current_course_menu(self, table, date, course_code):
        """
        Метод обработки действий пользователя на странице нужного курса
        :param table: датафрейм нужной таблицы текущего направления
        :param date: строка актуальности спаршенных данных
        :param course_code: код направления
        :return:
        """
        filename = f'guap-{course_code}_{date}.xlsx'
        with pd.ExcelWriter(filename) as writer:
            table.to_excel(writer, sheet_name=course_code, index=False, encoding='utf-8-sig')
            print(f"Файл сохранен как {filename}\n")

            choice = input('Нужен отфильтрованный вывод? (Например: вывести людей с баллами > 100) [да/нет]:\n>> ')
            if choice.lower() == 'да':
                end = False
                table_headers = table.columns
                table[table_headers[4]] = pd.to_numeric(table[table_headers[4]])

                while not end:
                    sheet_name = 'Фильтр по'
                    sorted_by = ''
                    was_sorted = False
                    didnt_choose_anything = 'Доступные параметра фильтровки закончились! :(\n'
                    clipped_data = table

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

    def start(self):
        self.courses_table, self.courses_date = self.parse_table(self.courses_url)
        self.courses_menu()


def main():
    url = 'https://priem.guap.ru/_lists/'
    parser = ParserGuap22(url, 'Pred_35')
    parser.start()


if __name__ == '__main__':
    main()
