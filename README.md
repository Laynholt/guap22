# guap22
Простой парсер данных поступающих с сайта ГУАП.

# Особенности
Оба файла независыми друг от друга и отличаются тем, что guap22.py - парсит данные только для одного направления, которое будет указано в функции main(), а 
guap22-ext.py - все направления и позволяет по ним переключаться.

Также есть версия раширенного парсера guap22-ext.py с графическим интерфесом - guap22-ext-ui.py.

# Зависимости
Все необходиные зависимоти указаны в файле requirements.txt
Основные:
```
pip3 install pandas
pip3 install lxml
pip3 install bs4
pip3 install openpyxl
pip3 install requests

```

# Запуск
```
python guap22.py

или

python guap22-ext.py

или

python guap22-ext-ui.py

```

# Скриншоты
Парсер с графическим интерфейсом:

![image](https://user-images.githubusercontent.com/41357381/183255061-c0f64c3d-06dc-429c-8d4c-49a7b1fd902f.png)
