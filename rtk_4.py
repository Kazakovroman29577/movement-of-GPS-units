import tkinter as tk
from tkinter import messagebox, simpledialog
import pandas as pd
import os
import datetime
from datetime import timedelta
import matplotlib.pyplot as plt

# Путь к файлу данных
DATA_FILE = 'data.xlsx'

# --- Вспомогательные функции ---
def check_warranty(date: datetime.date) -> bool:
    today = datetime.date.today()
    delta = today - date
    return delta < timedelta(days=1095)

def add_new_object(branch: str, imei: int, device_type: str, model: str):
    global main_dict, date_dict
    date_nat = date_dict.get(imei, pd.NaT)  # Получаем дату из date_dict, если IMEI есть
    if branch not in main_dict:
        main_dict[branch] = {}
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
    brand_statuses = {}

    # Анализ статусов в основном списке
    for branch, im_dict in main_dict.items():
        for imei, info in im_dict.items():
            status = info[3]
            brand = info[0]

            if status in statuses:
                statuses[status] += 1

            if brand not in brand_statuses:
                brand_statuses[brand] = {'установлен': 0, 'склад': 0, 'диагностика': 0}
            brand_statuses[brand][status] += 1

    # Анализ статусов в списке неправильных объектов
    for branch, im_dict in wrong_dict.items():
        for imei, info in im_dict.items():
            status = info[3]
            brand = info[0]

            if status in statuses:
                statuses[status] += 1

            if brand not in brand_statuses:
                brand_statuses[brand] = {'установлен': 0, 'склад': 0, 'диагностика': 0}
            brand_statuses[brand][status] += 1

    # Анализ статусов в списке диагностики
    for branch, im_dict in diag_dict.items():
        for imei, info in im_dict.items():
            status = info[3]
            brand = info[0]

            if status in statuses:
                statuses[status] += 1

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

# Загрузка и сохранение данных
def load_data():
    if os.path.exists(DATA_FILE):
        df_main = pd.read_excel(DATA_FILE, sheet_name='rtk_obgect')
        df_wrong = pd.read_excel(DATA_FILE, sheet_name='rtk_obgect_wrong')
        df_diag = pd.read_excel(DATA_FILE, sheet_name='rkr_obgect_diagnostic')
        df_dates = pd.read_excel(DATA_FILE, sheet_name='date_dict')
    else:
        columns = ['Филиал', 'IMEI', 'Тип', 'Модель', 'Статус', 'Локация', 'Дата']
        df_main = pd.DataFrame(columns=columns)
        df_wrong = pd.DataFrame(columns=columns)
        df_diag = pd.DataFrame(columns=columns)
        df_dates = pd.DataFrame(columns=['IMEI', 'Дата'])
    return df_main, df_wrong, df_diag, df_dates

def save_data(df_main, df_wrong, df_diag, df_dates):
    with pd.ExcelWriter(DATA_FILE) as writer:
        df_main.to_excel(writer, sheet_name='rtk_obgect', index=False)
        df_wrong.to_excel(writer, sheet_name='rtk_obgect_wrong', index=False)
        df_diag.to_excel(writer, sheet_name='rkr_obgect_diagnostic', index=False)
        df_dates.to_excel(writer, sheet_name='date_dict', index=False)

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

# Загрузка данных при старте
df_main, df_wrong, df_diag, df_dates = load_data()
main_dict = df_to_dicts(df_main)
wrong_dict = df_to_dicts(df_wrong)
diag_dict = df_to_dicts(df_diag)
date_dict = dict(zip(df_dates['IMEI'], df_dates['Дата'].dt.date))

# Главный GUI
root = tk.Tk()
root.title("Система управления IMEI")

def input_client():
    branch = simpledialog.askstring("Введите филиал", "Филиал:")
    if branch is None:
        return
    if branch not in main_dict:
        messagebox.showerror("Ошибка", "Такого филиала нет.")
        return

    imei_input = simpledialog.askstring("Введите IMEI", "IMEI:")
    if imei_input is None:
        return

    try:
        imei_num = int(imei_input)
    except ValueError:
        messagebox.showerror("Ошибка", "Некорректный формат IMEI.")
        return

    if imei_num not in main_dict.get(branch, {}):
        if messagebox.askyesno("Добавить новый", f"IMEI {imei_num} не найден. Добавить новый объект?"):
            device_type = simpledialog.askstring("Введите тип устройства", "Тип устройства:")
            model = simpledialog.askstring("Введите модель устройства", "Модель устройства:")
            add_new_object(branch, imei_num, device_type, model)
            messagebox.showinfo("Успех", "Объект добавлен.")
        return

    info = main_dict[branch][imei_num]
    date_obj = info[4]  # уже datetime.date
    warranty_status = check_warranty(date_obj)
    messagebox.showinfo("Данные", str(info[:-1]) + "\nГарантия: " + ('не завершена' if warranty_status else 'завершена'))

    action = simpledialog.askstring("Действие", 'Выберите действие - (диагностика / неисправен):')
    if action == 'диагностика':
        move_to_diagnostic(branch, imei_num)
    elif action == 'неисправен':
        move_to_wrong(branch, imei_num)
    else:
        messagebox.showerror("Ошибка", "Неверная команда.")

def show_status_distribution():
    plot_status_distribution()

# Кнопки для действий
btn_input_client = tk.Button(root, text="Ввести филиал и IMEI", command=input_client)
btn_input_client.pack(pady=10)

btn_show_distribution = tk.Button(root, text="Показать распределение IMEI по статусам", command=show_status_distribution)
btn_show_distribution.pack(pady=10)

btn_exit = tk.Button(root, text="Выход", command=root.quit)
btn_exit.pack(pady=10)

# Запуск главного цикла tkinter
root.mainloop()
