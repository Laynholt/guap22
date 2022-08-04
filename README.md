# guap22
Простой парсер данных поступающих с сайта ГУАП.

# Особенности
Оба файла независыми друг от друга и отличаются тем, что guap22.py - парсит данные только для одного направления, которое будет указанов в функции main(), а 
guap22-ext.py - все направления и позволяем по ним переключаться.

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
```
