import pandas as pd
import datetime
import os
from datetime import timedelta
import matplotlib.pyplot as plt




# Путь к файлу данных
DATA_FILE = 'data.xlsx'


# --- Загрузка данных ---
def load_data():
    if os.path.exists(DATA_FILE):
        # Загрузка данных из листов
        df_main = pd.read_excel(DATA_FILE, sheet_name='rtk_obgect')
        df_wrong = pd.read_excel(DATA_FILE, sheet_name='rtk_obgect_wrong')
        df_diag = pd.read_excel(DATA_FILE, sheet_name='rkr_obgect_diagnostic')
        df_dates = pd.read_excel(DATA_FILE, sheet_name='date_dict')
    else:
        # Если файла нет, создаём пустые DataFrame
        columns = ['Филиал', 'IMEI', 'Тип', 'Модель', 'Статус', 'Локация', 'Дата']
        df_main = pd.DataFrame(columns=columns)
        df_wrong = pd.DataFrame(columns=columns)
        df_diag = pd.DataFrame(columns=columns)
        df_dates = pd.DataFrame(columns=['IMEI', 'Дата'])
    return df_main, df_wrong, df_diag, df_dates


# --- Сохранение данных ---
def save_data(df_main, df_wrong, df_diag, df_dates):
    with pd.ExcelWriter(DATA_FILE) as writer:
        df_main.to_excel(writer, sheet_name='rtk_obgect', index=False)
        df_wrong.to_excel(writer, sheet_name='rtk_obgect_wrong', index=False)
        df_diag.to_excel(writer, sheet_name='rkr_obgect_diagnostic', index=False)
        df_dates.to_excel(writer, sheet_name='date_dict', index=False)


# --- Обработка загрузки ---
df_main, df_wrong, df_diag, df_dates = load_data()


# --- Перевод данных из DataFrame в словари ---
def df_to_dicts(df):
    result = {}
    for _, row in df.iterrows():
        branch = row['Филиал']
        imei = int(row['IMEI'])
        date_value = row['Дата'].date() if isinstance(row['Дата'], pd.Timestamp) else row['Дата']
        data_tuple = (row['Тип'], row['Модель'], row['Статус'], row['Локация'], date_value)
        if branch not in result:
            result[branch] = {}
        result[branch][imei] = data_tuple
    return result


def dicts_to_df(data_dict):
    rows = []
    for branch, im_dict in data_dict.items():
        for imei, data in im_dict.items():
            row = {
                'Филиал': branch,
                'IMEI': imei,
                'Тип': data[0],
                'Модель': data[1],
                'Статус': data[2],
                'Локация': data[3],
                'Дата': data[4]
            }
            rows.append(row)
    return pd.DataFrame(rows)


# Обратное преобразование
main_dict = df_to_dicts(df_main)
wrong_dict = df_to_dicts(df_wrong)
diag_dict = df_to_dicts(df_diag)

# Создаем словарь для дат IMEI
date_dict = dict(zip(df_dates['IMEI'], df_dates['Дата'].dt.date))

# --- Заполнение пустых дат ---
for branch, imei_dict in main_dict.items():
    for imei, info in imei_dict.items():
        date_value = info[4]  # Текущая дата объекта
        if pd.isnull(date_value) and imei in date_dict:  # Проверяем, если дата пуста и IMEI присутствует в date_dict
            # Заполняем пустую дату из date_dict
            main_dict[branch][imei] = (info[0], info[1], info[2], info[3], date_dict[imei])
            print(f"Дата для IMEI {imei} заменена на {date_dict[imei]} в филиале {branch}.")


# --- Вспомогательные функции ---
def check_warranty(date: datetime.date) -> bool:
    today = datetime.date.today()
    delta = today - date
    return delta < timedelta(days=1095)


def add_new_object(branch: str, imei: int, device_type: str, model: str):
    global main_dict, date_dict
    # Проверяем, если IMEI уже существует в date_dict
    date_nat = date_dict.get(imei, pd.NaT)  # Получаем дату из date_dict, если IMEI есть
    if branch not in main_dict:
        main_dict[branch] = {}
    # Сохраняем объект с правильной датой
    main_dict[branch][imei] = (device_type, model, 'исправен', 'установлен', date_nat)
    date_dict[imei] = date_nat  # Обновляем date_dict
    print(f"Объект IMEI {imei} добавлен в филиал {branch}. Дата: {date_nat}")
    save_all()


def save_all():
    global main_dict, wrong_dict, diag_dict, date_dict
    df_main = dicts_to_df(main_dict)
    df_wrong = dicts_to_df(wrong_dict)
    df_diag = dicts_to_df(diag_dict)
    df_dates = pd.DataFrame([{'IMEI': imei, 'Дата': date} for imei, date in date_dict.items()])
    save_data(df_main, df_wrong, df_diag, df_dates)


def move_to_diagnostic(branch: str, imei: int):
    global main_dict, diag_dict
    if branch in main_dict and imei in main_dict[branch]:
        info = main_dict[branch][imei]
        date_value = info[4]
        diag_dict[branch] = diag_dict.get(branch, {})
        diag_dict[branch][imei] = (info[0], info[1], 'не исправен', 'диагностика', date_value)
        del main_dict[branch][imei]
        print(f"IMEI {imei} перемещен в диагностику.")
        save_all()


def move_to_wrong(branch: str, imei: int):
    global main_dict, wrong_dict
    if branch in main_dict and imei in main_dict[branch]:
        info = main_dict[branch][imei]
        date_value = info[4]
        wrong_dict[branch] = wrong_dict.get(branch, {})
        wrong_dict[branch][imei] = (info[0], info[1], 'не исправен', 'склад', date_value)
        del main_dict[branch][imei]
        print(f"IMEI {imei} перемещен в не исправные объекты.")
        save_all()
def plot_status_distribution():
    statuses = {'установлен': 0, 'склад': 0, 'диагностика': 0}
    brand_statuses = {}  # Словарь для хранения статусов по маркам

    # Подсчитываем в основном списке
    for branch, im_dict in main_dict.items():
        for imei, info in im_dict.items():
            status = info[3]  # Изменение: используем info[3] вместо info[2]
            brand = info[0]   # Предполагаем, что марка находится в info[0]

            # Обновление общего статуса
            if status in statuses:
                statuses[status] += 1

            # Обновление статусов по марке
            if brand not in brand_statuses:
                brand_statuses[brand] = {'установлен': 0, 'склад': 0, 'диагностика': 0}
            brand_statuses[brand][status] += 1

    # В списке wrong
    for branch, im_dict in wrong_dict.items():
        for imei, info in im_dict.items():
            status = info[3]  # Изменение: используем info[3] вместо info[2]
            brand = info[0]   # Предполагаем, что марка находится в info[0]

            # Обновление общего статуса
            if status in statuses:
                statuses[status] += 1

            # Обновление статусов по марке
            if brand not in brand_statuses:
                brand_statuses[brand] = {'установлен': 0, 'склад': 0, 'диагностика': 0}
            brand_statuses[brand][status] += 1

    # В списке диагностики
    for branch, im_dict in diag_dict.items():
        for imei, info in im_dict.items():
            status = info[3]  # Изменение: используем info[3] вместо info[2]
            brand = info[0]   # Предполагаем, что марка находится в info[0]

            # Обновление общего статуса
            if status in statuses:
                statuses[status] += 1

            # Обновление статусов по марке
            if brand not in brand_statuses:
                brand_statuses[brand] = {'установлен': 0, 'склад': 0, 'диагностика': 0}
            brand_statuses[brand][status] += 1

    # Построение графиков для каждого бренда
    for brand, status_count in brand_statuses.items():
        labels = list(status_count.keys())
        counts = list(status_count.values())

        plt.figure()
        plt.barh(labels, counts, color=['green', 'red', 'orange'])
        plt.xlabel('Количество объектов')
        plt.title(f'Распределение объектов по статусам для марки: {brand}')

        # Добавление аннотаций
        for index, value in enumerate(counts):
            plt.annotate(f'{value}',
                         xy=(value, index),
                         ha='left',
                         va='center',
                         fontsize=15,
                         color='black')

        plt.show()

    # Построение общего графика
    labels = list(statuses.keys())
    counts = list(statuses.values())

    plt.figure()
    plt.barh(labels, counts, color=['green', 'red', 'orange'])
    plt.xlabel('Количество объектов')
    plt.title('Общее распределение объектов по статусам')

    # Добавление аннотаций
    for index, value in enumerate(counts):
        plt.annotate(f'{value}',
                     xy=(value, index),
                     ha='left',
                     va='center',
                     fontsize=20,
                     color='red')

    plt.show()

# --- Основной цикл ---
while True:

    print("\n--- Меню ---")
    print("1. Ввести филиал и IMEI")
    print("2. Показать распределение IMEI по статусам (гистограмма)")
    print("0. Выход")
    choice = input('Выберите действие: ').strip()
    if choice == '0':
        print("Завершение работы.")
        break
    elif choice == '2':
        plot_status_distribution()
        continue
    elif choice == '1':
        branch = input('Введите филиал: ').strip()
        if branch.lower() == 'выход':
            break
        if branch not in main_dict:
            print('Такого филиала нет.')
            continue
        imei_input = input('Введите IMEI: ').strip()
        try:
            imei_num = int(imei_input)
        except:
            print('Некорректный формат IMEI.')
            continue

    # Проверка наличия IMEI
    in_main = imei_num in main_dict.get(branch, {})
    in_wrong = imei_num in wrong_dict.get(branch, {})
    in_diag = imei_num in diag_dict.get(branch, {})

    if not in_main:
        if in_wrong or in_diag:
            print('Объект с таким IMEI найден в другом списке.')
            if in_wrong:
                print('В списке "неисправен".')
            if in_diag:
                print('В списке "диагностика".')
            choice = input('Проверить информацию там? (да/нет): ').strip().lower()
            if choice == 'да':
                if in_wrong:
                    print('Информация (неисправен):', wrong_dict[branch][imei_num])
                if in_diag:
                    print('Информация (диагностика):', diag_dict[branch][imei_num])
            continue
        else:
            # Нет такого IMEI - спросить добавить
            add_choice = input('Объекта такого не найдено. Добавить новый? (да/нет): ').strip().lower()
            if add_choice == 'да':
                device_type = input('Введите тип устройства: ').strip()
                model = input('Введите модель устройства: ').strip()
                add_new_object(branch, imei_num, device_type, model)
            continue
    else:
        # IMEI есть в основном списке
        info = main_dict[branch][imei_num]
        date_obj = info[4]  # уже datetime.date
        warranty_status = check_warranty(date_obj)  # теперь здесь гарантированно datetime.date
        print('Данные:', info[:-1])
        print('Гарантия не завершена' if warranty_status else 'Гарантия завершена')

        # выбор действия
        action = input('Действие - (диагностика / неисправен): ').strip().lower()
        if action == 'диагностика':
            move_to_diagnostic(branch, imei_num)
        elif action == 'неисправен':
            move_to_wrong(branch, imei_num)
        else:
            print('Неверная команда.')

# Перед завершением сохраняем данные
save_all()