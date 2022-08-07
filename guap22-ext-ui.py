import tkinter
from tkinter import messagebox
from tkinter.ttk import Combobox, Checkbutton, Style
import os
import requests
import openpyxl
import pandas as pd
from bs4 import BeautifulSoup


class Parser:
    def __init__(self, base_url, url_postfix):
        self.base_url = base_url
        self.courses_url = base_url + url_postfix
        self.courses_table = None
        self.courses_date = None

        self.h3 = None
        self.h4 = None
        self.current_course_table = None
        self.current_course_date = None
        self.current_course_code = None

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

        # Ищем внутри тегов h3 и h4, которые идут подряд, название специальности и количество мест
        self.h3 = soup.findAll('h3')
        self.h4 = soup.findAll('h4')
        if len(self.h3):
            self.h3 = str(self.h3[0]).replace('<h3>', '').replace('</h3>', '')
            if len(self.h4):
                self.h4 = str(self.h4[0]).replace('<h4>', '').replace('</h4>', '').replace('<br>', '').replace('<br/>',
                                                                                                               '')
        return table_data, date


class AppParser:
    def __init__(self, base_url, url_postfix):
        # ui variables
        self.window = tkinter.Tk()
        self.window.geometry('560x120')
        try:
            self.window.iconbitmap('icon.ico')
        except tkinter.TclError:
            pass

        self.window.title('Парсер данных поступающих ГУАП 2022')
        self.window.resizable(width=False, height=False)

        self.label_courses = tkinter.Label(self.window, text='Выберете направление:')
        self.label_courses.grid(column=0, row=0)

        self.combo_courses = Combobox(self.window, width=33)
        self.combo_courses.grid(column=1, row=0)
        self.combo_courses['state'] = 'readonly'
        self.combo_courses_loaded_row = None

        self.combo_courses_type = Combobox(self.window)
        self.combo_courses_type.grid(column=2, row=0)
        self.combo_courses_type['state'] = 'readonly'
        self.combo_courses_type_loaded_row = None

        self.current_course_type = None

        self.button_load_courses = tkinter.Button(self.window, text='Загрузить направление',
                                                  command=self._load_selected_course)
        self.button_load_courses.grid(column=1, row=1, pady=5)

        self.check_state_points = tkinter.BooleanVar()
        self.check_state_accept = tkinter.BooleanVar()
        self.check_state_document = tkinter.BooleanVar()
        self.check_state_points.set(True)
        self.check_state_accept.set(True)
        self.check_state_document.set(True)

        self.check_points = Checkbutton(self.window, text='Фильтровать по баллам', var=self.check_state_points,
                                        command=self._disable_points_widgets)
        self.check_accept = Checkbutton(self.window, text='Фильтровать по согласию', var=self.check_state_accept)
        self.check_document = Checkbutton(self.window, text='Фильтровать по документам', var=self.check_state_document)

        self.check_points.grid(column=0, row=2)
        self.check_accept.grid(column=1, row=2)
        self.check_document.grid(column=2, row=2)

        self.combo_points_sign_variable = tkinter.StringVar()
        self.combo_points_sign = Combobox(self.window, width=5, textvariable=self.combo_points_sign_variable)
        self.combo_points_sign.grid(column=0, row=3, sticky=tkinter.W, padx=5, pady=5)
        self.combo_points_sign['values'] = ('>=', '>', '=', '<=', '<')
        self.combo_points_sign['state'] = 'readonly'
        self.combo_points_sign.current(0)

        self.label_points = tkinter.Label(self.window, text='Введите баллы:')
        self.label_points.grid(column=0, row=3, sticky=tkinter.E, pady=5)

        self.entry_points_value = tkinter.Entry(self.window)
        self.entry_points_value.grid(column=1, row=3, sticky=tkinter.W, pady=5)

        self.button_filter = tkinter.Button(self.window, text='Отфильтровать', command=self._filtrate)
        self.button_filter.grid(column=2, row=3, pady=5)

        # parser variables
        self.parser = Parser(base_url, url_postfix)

    def _load_selected_course(self):
        current_course = self.combo_courses.current()
        current_course_type = self.combo_courses_type.current()
        table_headers = self.parser.courses_table.columns

        for i, row_data in self.parser.courses_table.iterrows():
            if current_course == i:
                url_postfix = row_data[table_headers[current_course_type + 2]]
                if url_postfix == '-' or url_postfix == '0':
                    messagebox.showinfo('Выполнено', 'Текущего списка не существует!')
                else:
                    url_postfix = url_postfix.split(')(')[1].replace(')', '').replace(' ', '')
                    self.parser.current_course_table, self.parser.current_course_date = self.parser.parse_table(
                        self.parser.base_url + url_postfix)
                    self.parser.current_course_date = str(self.parser.current_course_date).replace(':', '-')
                    self.parser.current_course_code = str(row_data[table_headers[0]])
                    self.current_course_type = str(table_headers[current_course_type + 2]).replace(' ', '_')

                    self.combo_courses_loaded_row = current_course
                    self.combo_courses_type_loaded_row = current_course_type

                    filename = f'guap-{self.parser.current_course_code}_{self.parser.current_course_date}_{self.current_course_type}.xlsx'
                    try:
                        with pd.ExcelWriter(filename) as writer:
                            self.parser.current_course_table.to_excel(writer,
                                                                      sheet_name=self.parser.current_course_code,
                                                                      index=False, encoding='utf-8-sig')

                        messagebox.showinfo('Выполнено', f'Направление:\n[{row_data[table_headers[0]]} - '
                                                         f'{row_data[table_headers[1]]}]\n\nУспешно загружено и записано'
                                                         f' в файл [{filename}]!')
                    except PermissionError:
                        messagebox.showerror('Ошибка', f'Не удалось записать данные в файл [{filename}],'
                                                       f' вероятно из-за того, что он открыт!')

    def _filtrate(self):
        if self.parser.current_course_table is None or self.parser.current_course_date is None or self.parser.current_course_code is None:
            messagebox.showwarning('Предупреждение', 'Сначала выберете и загрузите нужное направление!')
            return
        else:
            if self.combo_courses_loaded_row != self.combo_courses.current() \
                    or self.combo_courses_type_loaded_row != self.combo_courses_type.current():
                self._load_selected_course()
                if self.combo_courses_loaded_row != self.combo_courses.current() \
                        or self.combo_courses_type_loaded_row != self.combo_courses_type.current():
                    return

            filename = f'guap-{self.parser.current_course_code}_{self.parser.current_course_date}_{self.current_course_type}.xlsx'
            if not os.path.exists(filename):
                with pd.ExcelWriter(filename) as writer:
                    self.parser.current_course_table.to_excel(writer, sheet_name=self.parser.current_course_code,
                                                              index=False, encoding='utf-8-sig')

            try:
                with pd.ExcelWriter(filename, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
                    table_headers = self.parser.current_course_table.columns
                    self.parser.current_course_table[table_headers[4]] = pd.to_numeric(
                        self.parser.current_course_table[table_headers[4]])

                    sheet_name = 'Фильтр по'
                    sorted_by = ''
                    clipped_data = self.parser.current_course_table

                    if self.check_state_points.get():
                        try:
                            number_of_points = int(self.entry_points_value.get())
                        except ValueError:
                            number_of_points = 0

                        compare_symbol = str(self.combo_points_sign_variable.get())

                        sheet_name += f' балл{compare_symbol}{number_of_points}'
                        sorted_by += f'имеют {compare_symbol}{number_of_points} баллов'

                        if compare_symbol == '>=':
                            clipped_data = clipped_data[clipped_data[table_headers[4]] >= number_of_points]
                        elif compare_symbol == '=':
                            clipped_data = clipped_data[clipped_data[table_headers[4]] == number_of_points]
                        elif compare_symbol == '>':
                            clipped_data = clipped_data[clipped_data[table_headers[4]] > number_of_points]
                        elif compare_symbol == '<=':
                            clipped_data = clipped_data[clipped_data[table_headers[4]] <= number_of_points]
                        elif compare_symbol == '<':
                            clipped_data = clipped_data[clipped_data[table_headers[4]] < number_of_points]

                    if self.check_state_accept.get():
                        sheet_name += ' согл'

                        if len(sorted_by) != 0:
                            sorted_by += ', подали согласие на зачисление'
                        else:
                            sorted_by += 'подали согласие на зачисление'

                        clipped_data = clipped_data[clipped_data[table_headers[5]] == 'Да']

                    if self.check_state_document.get():
                        sheet_name += ' докам'

                        if len(sorted_by) != 0:
                            sorted_by += ', подали оригиналы документов'
                        else:
                            sorted_by += 'подали оригиналы документов'

                        clipped_data = clipped_data[clipped_data[table_headers[6]] == 'Да']

                    if len(sorted_by) == 0:
                        sorted_by = 'поставили данное направление'
                    clipped_data.to_excel(writer, sheet_name=sheet_name, index=False, encoding='utf-8-sig')
                    messagebox.showinfo('Выполнено',
                                        f'Дата актуальности данных: {self.parser.current_course_date.replace("-", ":")}\n\n'
                                        f'Направление:\n{self.parser.h3}\nКоличество мест:\n{self.parser.h4}\n\n'
                                        f''f'Людей, которые {sorted_by}: [{len(clipped_data)}].\n\n'
                                        f'Отфильтрованные данные записаны в файл [{filename}] '
                                        f'в лист с именем [{sheet_name}]')

            except PermissionError:
                messagebox.showerror('Ошибка', f'Не удалось записать данные в файл [{filename}],'
                                               f' вероятно из-за того, что он открыт!')

    def _disable_points_widgets(self):
        if not self.check_state_points.get():
            self.entry_points_value['state'] = 'disable'
            self.combo_points_sign['state'] = 'disable'
        else:
            self.entry_points_value['state'] = 'normal'
            self.combo_points_sign['state'] = 'readonly'

    def load_courses(self):
        self.parser.courses_table, self.parser.courses_date = self.parser.parse_table(self.parser.courses_url)

        table_headers = self.parser.courses_table.columns
        self.parser.courses_table.fillna(0, inplace=True)

        clipped_courses_table = pd.DataFrame(columns=table_headers)
        # Проходимся по-строчно по датафрейму и добавляем поля, которые имеют ссылки внутри, в новый датафрейм
        for i, row_data in self.parser.courses_table.iterrows():
            if (row_data[table_headers[2]] != '-' and row_data[table_headers[2]] != '0') \
                    or (row_data[table_headers[3]] != '-' and row_data[table_headers[3]] != '0') \
                    or (row_data[table_headers[4]] != '-' and row_data[table_headers[4]] != '0'):
                length = len(clipped_courses_table)
                clipped_courses_table.loc[length] = row_data
                self.combo_courses['values'] = (*self.combo_courses['values'], f'{row_data[table_headers[0]]} -'
                                                                               f' {row_data[table_headers[1]]}')

        self.combo_courses.current(0)
        self.parser.courses_table = clipped_courses_table

        self.combo_courses_type['values'] = [table_headers[2], table_headers[3], table_headers[4]]
        self.combo_courses_type.current(0)

    def start(self):
        self.load_courses()
        self.window.mainloop()


def main():
    url = 'https://priem.guap.ru/_lists/'
    app = AppParser(url, 'Pred_35')
    app.start()


if __name__ == '__main__':
    main()
