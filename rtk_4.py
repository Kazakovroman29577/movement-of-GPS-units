from tkinter import ttk, messagebox
import csv
import json
import re
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from tkinter import simpledialog
import tkinter as tk
from tkinter import PhotoImage

# ===================== Модели и файлы - без изменений =====================
class Equipment:
    def __init__(self, branch, imei, brand, model, status, condition, location, date_str):
        self.branch = branch
        self.imei = imei
        self.brand = brand
        self.model = model
        self.status = status
        self.condition = condition
        self.location = location
        try:
            self.date = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            self.date = None

    def to_dict(self):
        return {
            'branch': self.branch,
            'imei': self.imei,
            'brand': self.brand,
            'model': self.model,
            'status': self.status,
            'condition': self.condition,
            'location': self.location,
            'date': self.date.strftime('%Y-%m-%d') if self.date else ''
        }

# ... (здесь остаются функции save/load, а также весь предыдущий GUI-код) ...
def save_to_csv(data, filename='equipment_data.csv'):
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            if not data:
                return
            writer = csv.DictWriter(f, fieldnames=data[0].to_dict().keys())
            writer.writeheader()
            for item in data:
                writer.writerow(item.to_dict())
    except Exception as e:
        print(f"Ошибка при сохранении в CSV: {e}")

def load_from_csv(filename='equipment_data.csv'):
    equipments = []
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                equipments.append(Equipment(
                    branch=row['branch'],
                    imei=row['imei'],
                    brand=row['brand'],
                    model=row['model'],
                    status=row['status'],
                    condition=row['condition'],
                    location=row['location'],
                    date_str=row['date']
                ))
    except Exception as e:
        print(f"Ошибка при чтении CSV: {e}")
    return equipments

def save_to_json(data, filename='equipment_data.json'):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([item.to_dict() for item in data], f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка при сохранении в JSON: {e}")

def load_from_json(filename='equipment_data.json'):
    equipments = []
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            data_list = json.load(f)
            for data in data_list:
                equipments.append(Equipment(
                    branch=data['branch'],
                    imei=data['imei'],
                    brand=data['brand'],
                    model=data['model'],
                    status=data['status'],
                    condition=data['condition'],
                    location=data['location'],
                    date_str=data['date']
                ))
    except Exception as e:
        print(f"Ошибка при чтении JSON: {e}")
    return equipments

# ===================== analysis.py: функции анализа и визуализации =====================

def top_branches_defective(equipments, top_n=10):
    """Выводит топ N филиалов по числу неисправных устройств."""
    df = pd.DataFrame([eq.to_dict() for eq in equipments])
    if df.empty or 'status' not in df:
        messagebox.showinfo("Информация", "Нет данных для отображения.")
        return

    faulty_mask = df['status'].str.lower().str.contains('неисправен', na=False)
    df_faulty = df[faulty_mask]
    if df_faulty.empty:
        messagebox.showinfo("Информация", "Нет неисправных устройств.")
        return

    result = df_faulty['branch'].value_counts().head(top_n)

    # Правильно: создаем фигуру и ось, и рисуем на ней
    fig, ax = plt.subplots(figsize=(10, 6))
    result.plot(kind='bar', color='red', ax=ax)
    ax.set_title(f"Топ {top_n} филиалов по количеству неисправных устройств")
    ax.set_ylabel("Количество")
    fig.tight_layout()
    plt.show()
def dynamics_by_condition(equipments):
    """Выводит количество устройств по брендам, начиная с 2024 года."""
    df = pd.DataFrame([eq.to_dict() for eq in equipments])
    if df.empty:
        messagebox.showinfo("Информация", "Нет данных для отображения.")
        return

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    start_date = pd.Timestamp('2000-01-01')
    df_filtered = df[df['date'] >= start_date]
    if df_filtered.empty:
        messagebox.showinfo("Информация", "Нет данных начиная с 2024 года.")
        return

    counts = df_filtered.groupby(['brand', 'condition']).size().reset_index(name='count')
    pivot_table = counts.pivot(index='brand', columns='condition', values='count').fillna(0)

    # Правильно: создаем фигуру и ось, и рисуем на ней
    fig, ax = plt.subplots(figsize=(12, 8))
    pivot_table.plot(kind='bar', stacked=True, colormap='tab20', ax=ax)

    ax.set_title("Количество устройств по брендам")
    ax.set_xlabel("Бренд")
    ax.set_ylabel("Количество")
    ax.legend(title='Состояние')
    fig.tight_layout()
    plt.show()

def sort_equipments_by(field, equipments):
    """Сортирует список Equipment по заданному полю."""
    if field == 'date':
        return sorted(equipments, key=lambda eq: eq.date or datetime.min)
    elif field == 'condition':
        return sorted(equipments, key=lambda eq: eq.condition)
    else:
        return equipments

# ===================== Вспомогательные функции валидации =====================

ALLOWED_STATUS = {'исправен', 'неисправен'}
ALLOWED_CONDITION = {'установлен', 'диагностика', 'ремонт', 'демонтирован', 'неустановлен'}
ALLOWED_LOCATION = {'склад', 'тс'}

def normalize(s: str) -> str:
    return (s or '').strip().lower()

def is_cyrillic_letters(s: str) -> bool:
    # только кириллица без пробелов и знаков (включая букву ё)
    return bool(re.fullmatch(r'[а-яё]+', s))

def is_digits(s: str) -> bool:
    return bool(re.fullmatch(r'\d+', s))

def validate_fields(d: dict):
    """
    d = {
        'branch','imei','brand','model','status','condition','location','date'
    }
    Преобразует к нижнему регистру и проверяет ограничения.
    Возвращает (ok, err_msg_or_none, normalized_dict)
    """
    out = {k: normalize(v) for k, v in d.items()}

    # обязательные поля
    required = ['branch', 'imei', 'brand', 'model', 'status', 'condition', 'location', 'date']
    missing = [r for r in required if not out.get(r)]
    if missing:
        return False, f"Заполните поля: {', '.join(missing)}", None

    # буквы (кириллица) для этих полей
    for k in ['branch', 'brand', 'status', 'condition', 'location']:
        if not is_cyrillic_letters(out[k]):
            return False, f"Поле '{k}' должно содержать только буквы кириллицы без пробелов и знаков.", None

    # цифры только
    for k in ['imei', 'model']:
        if not is_digits(out[k]):
            return False, f"Поле '{k}' должно содержать только цифры.", None

    # дополнительные проверки IMEI (если нужно ограничение длины)
    if not (3 <= len(out['imei']) <= 15):
        return False, "Длина IMEI должна быть от 3 до 15 цифр.", None

    # перечислимые значения
    if out['status'] not in ALLOWED_STATUS:
        return False, f"Недопустимый статус. Разрешено: {', '.join(sorted(ALLOWED_STATUS))}.", None
    if out['condition'] not in ALLOWED_CONDITION:
        return False, f"Недопустимое состояние. Разрешено: {', '.join(sorted(ALLOWED_CONDITION))}.", None
    if out['location'] not in ALLOWED_LOCATION:
        return False, f"Недопустимое расположение. Разрешено: {', '.join(sorted(ALLOWED_LOCATION))}.", None

    # дата формата YYYY-MM-DD
    try:
        datetime.strptime(out['date'], '%Y-%m-%d')
    except Exception:
        return False, "Неверный формат даты. Используйте YYYY-MM-DD.", None

    return True, None, out

# ===================== Обновленный основной класс GUI =====================

class App:
    def __init__(self, master):
        self.master = master
        self.master.title("Учет оборудования и анализ")

        # Меню
        self._build_menu()

        # Данные
        self.equipments = load_from_json()

        # Остальной интерфейс
        self._build_ui()

        # Сохранение при закрытии окна (крестик)
        self.master.protocol("WM_DELETE_WINDOW", self.save_and_exit)

    def _build_menu(self):
        menubar = tk.Menu(self.master)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        sort_menu = tk.Menu(menubar, tearoff=0)
        sort_menu.add_command(label="Сортировать по дате", command=lambda: self.sort_equipments('date'))
        sort_menu.add_command(label="Сортировать по состоянию", command=lambda: self.sort_equipments('condition'))
        menubar.add_cascade(label="Сортировка", menu=sort_menu)

        self.master.config(menu=menubar)

    def _build_ui(self):
        # Ввод для поиска
        frame_input = ttk.Frame(self.master)
        frame_input.pack(padx=10, pady=10)

        ttk.Label(frame_input, text="Филиал").grid(row=0, column=0, sticky='w')
        self.entry_branch = ttk.Entry(frame_input)
        self.entry_branch.grid(row=0, column=1)

        ttk.Label(frame_input, text="IMEI").grid(row=1, column=0, sticky='w')
        self.entry_imei = ttk.Entry(frame_input)
        self.entry_imei.grid(row=1, column=1)

        ttk.Button(frame_input, text="Поиск", command=self.search).grid(row=2, column=0, columnspan=2, pady=5)

        # Результат
        self.result_label = ttk.Label(self.master, text="", justify='left', background='white', relief='solid')
        self.result_label.pack(padx=50, pady=50, fill='x')

        # Добавление оборудования
        ttk.Label(self.master, text="Добавить оборудование", font=('Arial', 12, 'bold')).pack(pady=10)
        frame_add = ttk.Frame(self.master)
        frame_add.pack(padx=10, pady=5)

        self.fields = [
            ('branch', 'Филиал'),
            ('imei', 'IMEI'),
            ('brand', 'Марка'),
            ('model', 'Модель'),
            ('status', 'Статус (исправен/неисправен)'),
            ('condition', 'Состояние (установлен/неустановлен/демонтирован/диагностика/ремонт)'),
            ('location', 'Расположение (склад/тс)'),
            ('date', 'Дата (YYYY-MM-DD)'),
        ]
        self.entries = {}
        for i, (key, lbl) in enumerate(self.fields):
            ttk.Label(frame_add, text=lbl).grid(row=i, column=0, sticky='w')
            e = ttk.Entry(frame_add)
            e.grid(row=i, column=1)
            self.entries[key] = e

        ttk.Button(frame_add, text="Добавить оборудование", command=self.add_equipment)\
            .grid(row=len(self.fields), column=0, columnspan=2, pady=5)

        # Аналитика
        frame_analysis = ttk.Frame(self.master)
        frame_analysis.pack(pady=5)
        # ttk.Button(frame_analysis, text="ТОП 10 по неисправным",
        #            command=lambda: top_branches_defective(self.equipments)).grid(row=0, column=0, padx=5)
        self.top_icon = tk.PhotoImage(file="imgs/icons6.png")

        # кнопка ТОП-10 с иконкой и текстом
        top_btn = ttk.Button(
            frame_analysis,
            text="ТОП 10 по неисправным",
            image=self.top_icon,
            compound="top",  # размещение текста слева от изображения; можно 'right'
            command=lambda: top_branches_defective(self.equipments)
        )
        top_btn.grid(row=0, column=0, padx=5)
        # ttk.Button(frame_analysis, text="Динамика по состоянию",
        #            command=lambda: dynamics_by_condition(self.equipments)).grid(row=0, column=1, padx=5)
        self.din_icon = tk.PhotoImage(file="imgs/icons7.png")

        # кнопка Динамика по состоянию с иконкой и текстом
        din_btn = ttk.Button(
            frame_analysis,
            text="Динамика по состоянию",
            image=self.din_icon,
            compound="top",  # размещение текста слева от изображения; можно 'right'
            command=lambda: dynamics_by_condition(self.equipments)
        )
        din_btn.grid(row=0, column=1, padx=5)

        # Сохранение/загрузка/выход
        frame_buttons = ttk.Frame(self.master)
        frame_buttons.pack(pady=5)
        # ttk.Button(frame_buttons, text="Сохранить в CSV",
        #            command=lambda: self.save_data('csv', show_msg=True)).grid(row=0, column=0, padx=5)
        self.save_csv_icon = tk.PhotoImage(file="imgs/icons4.png")

        # кнопка Сохранить в CSV с иконкой и текстом
        save_csv_btn = ttk.Button(
            frame_buttons,
            text="Сохранить в CSV",
            image=self.save_csv_icon,
            compound="top",  # размещение текста слева от изображения; можно 'right'
            command=lambda: self.save_data('csv', show_msg=True)
        )
        save_csv_btn.grid(row=0, column=0, padx=5)
        # ttk.Button(frame_buttons, text="Сохранить в JSON",
        #            command=lambda: self.save_data('json', show_msg=True)).grid(row=0, column=1, padx=5)
        self.save_json_icon = tk.PhotoImage(file="imgs/icons5.png")

        # кнопка Сохранить в JSON с иконкой и текстом
        save_json_btn = ttk.Button(
            frame_buttons,
            text="Сохранить в JSON",
            image=self.save_json_icon,
            compound="top",  # размещение текста слева от изображения; можно 'right'
            command=lambda: self.save_data('json', show_msg=True)
        )
        save_json_btn.grid(row=0, column=1, padx=5)
        # ttk.Button(frame_buttons, text="Загрузить из CSV", command=self.load_csv).grid(row=0, column=2, padx=5)
        self.load_csv_icon = tk.PhotoImage(file="imgs/icons2.png")

        # кнопка Загрузить из CSV с иконкой и текстом
        load_csv_btn = ttk.Button(
            frame_buttons,
            text="Загрузить из CSV",
            image=self.load_csv_icon,
            compound="top",  # размещение текста слева от изображения; можно 'right'
            command=self.load_csv
        )
        load_csv_btn.grid(row=0, column=2, padx=5)
        # ttk.Button(frame_buttons, text="Загрузить из JSON", command=self.load_json).grid(row=0, column=3, padx=5)
        self.load_json_icon = tk.PhotoImage(file="imgs/icons3.png")

        # кнопка Загрузить из JSON с иконкой и текстом
        load_json_btn = ttk.Button(
            frame_buttons,
            text="Загрузить из JSON",
            image=self.load_json_icon,
            compound="top",  # размещение текста слева от изображения; можно 'right'
            command=self.load_json
        )
        load_json_btn.grid(row=0, column=3, padx=5)
        # ttk.Button(frame_buttons, text="Выход", command=self.save_and_exit).grid(row=0, column=4, padx=5)
        self.exit_icon = tk.PhotoImage(file="imgs/icons8.png")

        # кнопка Выход с иконкой и текстом
        exit_btn = ttk.Button(
            frame_buttons,
            text="Выход",
            image=self.exit_icon,
            compound="left",  # размещение текста слева от изображения; можно 'right'
            command=self.save_and_exit
        )
        exit_btn.grid(row=0, column=4, padx=5)




    def show_about(self):
        messagebox.showinfo(
            "О программе",
            "Учет оборудования и анализ\nВерсия: 1.0\nСортировка доступна в меню «Сортировка»."
        )

    def add_equipment(self):
        raw = {k: self.entries[k].get() for k, _ in self.fields}
        ok, err, data = validate_fields(raw)
        if not ok:
            messagebox.showerror("Ошибка валидации", err)
            return

        if any(eq.imei == data['imei'] for eq in self.equipments):
            messagebox.showerror("Ошибка", "Этот IMEI уже существует в базе.")
            return

        eq = Equipment(
            branch=data['branch'],
            imei=data['imei'],
            brand=data['brand'],
            model=data['model'],
            status=data['status'],
            condition=data['condition'],
            location=data['location'],
            date_str=data['date']
        )
        self.equipments.append(eq)
        self.autosave()
        messagebox.showinfo("Удачно", "Оборудование добавлено.")

        for e in self.entries.values():
            e.delete(0, tk.END)

    def autosave(self):
        save_to_json(self.equipments)
        save_to_csv(self.equipments)

    def save_data(self, fmt, show_msg=False):
        if fmt == 'csv':
            save_to_csv(self.equipments)
        else:
            save_to_json(self.equipments)
        if show_msg:
            messagebox.showinfo("Готово", f"Данные сохранены в {fmt.upper()}.")

    def load_csv(self):
        self.equipments = load_from_csv()
        messagebox.showinfo("Готово", "Данные загружены из CSV.")

    def load_json(self):
        self.equipments = load_from_json()
        messagebox.showinfo("Готово", "Данные загружены из JSON.")

    def search(self):
        branch_val = normalize(self.entry_branch.get())
        imei_val = normalize(self.entry_imei.get())

        if not branch_val or not imei_val:
            messagebox.showerror("Ошибка", "Введите Филиал и IMEI")
            return

        selected_eq = None
        for eq in self.equipments:
            if eq.branch == branch_val and eq.imei == imei_val:
                selected_eq = eq
                break

        if not selected_eq:
            self.result_label.config(text="Объект не найден.")
            return

        today = datetime.now()
        days_passed = (today - selected_eq.date).days if selected_eq.date else None
        guarantee_status = "Дата неизвестна."
        if days_passed is not None:
            guarantee_status = "Гарантия завершена." if days_passed >= 1095 else "На гарантии."

        info_text = (
            f"Филиал: {selected_eq.branch}\n"
            f"IMEI: {selected_eq.imei}\n"
            f"Марка: {selected_eq.brand}\n"
            f"Модель: {selected_eq.model}\n"
            f"Статус: {selected_eq.status}\n"
            f"Состояние: {selected_eq.condition}\n"
            f"Расположение: {selected_eq.location}\n"
            f"Дата: {selected_eq.date.strftime('%Y-%m-%d') if selected_eq.date else 'неизвестна'}\n"
            f"Статус гарантии: {guarantee_status}"
        )
        self.result_label.config(text=info_text)

        if messagebox.askquestion("Редактировать?", "Хотите внести изменения в Статус, Состояние или Расположение?") == 'yes':
            self.edit_fields(selected_eq)

    def edit_fields(self, equipment_obj):
        new_status = simpledialog.askstring("Редактировать", "Статус:", initialvalue=equipment_obj.status)
        if new_status is not None:
            ns = normalize(new_status)
            if is_cyrillic_letters(ns) and ns in ALLOWED_STATUS:
                equipment_obj.status = ns
            else:
                messagebox.showerror("Ошибка", f"Недопустимый статус. Разрешено: {', '.join(sorted(ALLOWED_STATUS))}.")

        new_condition = simpledialog.askstring("Редактировать", "Состояние:", initialvalue=equipment_obj.condition)
        if new_condition is not None:
            nc = normalize(new_condition)
            if is_cyrillic_letters(nc) and nc in ALLOWED_CONDITION:
                equipment_obj.condition = nc
            else:
                messagebox.showerror("Ошибка", f"Недопустимое состояние. Разрешено: {', '.join(sorted(ALLOWED_CONDITION))}.")

        new_location = simpledialog.askstring("Редактировать", "Расположение:", initialvalue=equipment_obj.location)
        if new_location is not None:
            nl = normalize(new_location)
            if is_cyrillic_letters(nl) and nl in ALLOWED_LOCATION:
                equipment_obj.location = nl
            else:
                messagebox.showerror("Ошибка", f"Недопустимое расположение. Разрешено: {', '.join(sorted(ALLOWED_LOCATION))}.")

        self.autosave()
        messagebox.showinfo("Обновлено", "Данные обновлены.")

    def sort_equipments(self, field):
        self.equipments = sort_equipments_by(field, self.equipments)
        messagebox.showinfo("Готово", f"Отсортировано по {field}", icon='info')


    def save_and_exit(self):
        self.autosave()
        self.master.destroy()

# ===================== запуск =====================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()



