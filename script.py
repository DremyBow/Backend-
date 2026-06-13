import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "clinic.db")


def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            cabinet TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            is_available INTEGER DEFAULT 1,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            schedule_id INTEGER NOT NULL,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id),
            FOREIGN KEY (schedule_id) REFERENCES schedules(id)
        )
    """)

    conn.commit()
    conn.close()


def input_int(message):
    try:
        return int(input(message))
    except ValueError:
        print("Ошибка: нужно ввести число.")
        return None


def patient_exists(patient_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM patients WHERE id = ?", (patient_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def doctor_exists(doctor_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM doctors WHERE id = ?", (doctor_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def add_patient():
    full_name = input("Введите ФИО пациента: ")
    phone = input("Введите телефон пациента: ")

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO patients (full_name, phone) VALUES (?, ?)",
        (full_name, phone)
    )

    patient_id = cursor.lastrowid

    conn.commit()
    conn.close()

    print(f"Пациент успешно зарегистрирован. Ваш ID: {patient_id}")


def add_doctor():
    full_name = input("Введите ФИО врача: ")
    specialization = input("Введите специальность врача: ")
    cabinet = input("Введите кабинет: ")

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO doctors (full_name, specialization, cabinet) VALUES (?, ?, ?)",
        (full_name, specialization, cabinet)
    )

    conn.commit()
    conn.close()

    print("Врач успешно добавлен.")


def show_doctors():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()

    conn.close()

    if not doctors:
        print("Врачей пока нет.")
        return False

    print("\nСписок врачей:")
    for doctor in doctors:
        print(f"{doctor[0]}. {doctor[1]} | {doctor[2]} | кабинет {doctor[3]}")

    return True


def show_patients():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()

    conn.close()

    if not patients:
        print("Пациентов пока нет.")
        return False

    print("\nСписок пациентов:")
    for patient in patients:
        print(f"{patient[0]}. {patient[1]} | телефон: {patient[2]}")

    return True


def add_schedule():
    if not show_doctors():
        return

    doctor_id = input_int("Введите ID врача: ")
    if doctor_id is None:
        return

    if not doctor_exists(doctor_id):
        print("Ошибка: врача с таким ID нет.")
        return

    date = input("Введите дату приёма, например 2026-06-15: ")
    time = input("Введите время приёма, например 14:30: ")

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO schedules (doctor_id, date, time, is_available) VALUES (?, ?, ?, 1)",
        (doctor_id, date, time)
    )

    conn.commit()
    conn.close()

    print("Расписание успешно добавлено.")


def show_schedule():
    if not show_doctors():
        return

    doctor_id = input_int("Введите ID врача: ")
    if doctor_id is None:
        return

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT schedules.id, doctors.full_name, schedules.date, schedules.time
        FROM schedules
        JOIN doctors ON schedules.doctor_id = doctors.id
        WHERE schedules.doctor_id = ? AND schedules.is_available = 1
    """, (doctor_id,))

    schedules = cursor.fetchall()
    conn.close()

    if not schedules:
        print("Свободного времени у этого врача нет.")
        return

    print("\nСвободное расписание:")
    for item in schedules:
        print(f"{item[0]}. Врач: {item[1]} | Дата: {item[2]} | Время: {item[3]}")


def create_appointment_for_patient():
    patient_id = input_int("Введите ваш ID пациента: ")
    if patient_id is None:
        return

    if not patient_exists(patient_id):
        print("Пациент с таким ID не найден. Сначала зарегистрируйтесь.")
        return

    if not show_doctors():
        return

    doctor_id = input_int("Введите ID врача: ")
    if doctor_id is None:
        return

    if not doctor_exists(doctor_id):
        print("Ошибка: врача с таким ID нет.")
        return

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, date, time
        FROM schedules
        WHERE doctor_id = ? AND is_available = 1
    """, (doctor_id,))

    schedules = cursor.fetchall()

    if not schedules:
        print("У выбранного врача нет свободного времени.")
        conn.close()
        return

    print("\nДоступное время:")
    for schedule in schedules:
        print(f"{schedule[0]}. Дата: {schedule[1]} | Время: {schedule[2]}")

    schedule_id = input_int("Введите ID времени приёма: ")
    if schedule_id is None:
        conn.close()
        return

    cursor.execute("""
        SELECT id
        FROM schedules
        WHERE id = ? AND doctor_id = ? AND is_available = 1
    """, (schedule_id, doctor_id))

    result = cursor.fetchone()

    if result is None:
        print("Ошибка: выбранное время недоступно.")
        conn.close()
        return

    cursor.execute("""
        INSERT INTO appointments (patient_id, doctor_id, schedule_id, status)
        VALUES (?, ?, ?, 'active')
    """, (patient_id, doctor_id, schedule_id))

    cursor.execute("""
        UPDATE schedules
        SET is_available = 0
        WHERE id = ?
    """, (schedule_id,))

    conn.commit()
    conn.close()

    print("Запись на приём успешно создана.")


def show_all_appointments():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            appointments.id,
            patients.full_name,
            doctors.full_name,
            doctors.specialization,
            schedules.date,
            schedules.time,
            appointments.status
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.id
        JOIN doctors ON appointments.doctor_id = doctors.id
        JOIN schedules ON appointments.schedule_id = schedules.id
        ORDER BY schedules.date, schedules.time
    """)

    appointments = cursor.fetchall()
    conn.close()

    if not appointments:
        print("Записей на приём пока нет.")
        return False

    print("\nВсе записи на приём:")
    for app in appointments:
        print(
            f"{app[0]}. Пациент: {app[1]} | "
            f"Врач: {app[2]} | "
            f"Специальность: {app[3]} | "
            f"Дата: {app[4]} | "
            f"Время: {app[5]} | "
            f"Статус: {app[6]}"
        )

    return True


def show_my_appointments():
    patient_id = input_int("Введите ваш ID пациента: ")
    if patient_id is None:
        return

    if not patient_exists(patient_id):
        print("Пациент с таким ID не найден.")
        return

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            appointments.id,
            doctors.full_name,
            doctors.specialization,
            doctors.cabinet,
            schedules.date,
            schedules.time,
            appointments.status
        FROM appointments
        JOIN doctors ON appointments.doctor_id = doctors.id
        JOIN schedules ON appointments.schedule_id = schedules.id
        WHERE appointments.patient_id = ?
        ORDER BY schedules.date, schedules.time
    """, (patient_id,))

    appointments = cursor.fetchall()
    conn.close()

    if not appointments:
        print("У вас пока нет записей.")
        return

    print("\nВаши записи:")
    for app in appointments:
        print(
            f"{app[0]}. Врач: {app[1]} | "
            f"Специальность: {app[2]} | "
            f"Кабинет: {app[3]} | "
            f"Дата: {app[4]} | "
            f"Время: {app[5]} | "
            f"Статус: {app[6]}"
        )


def cancel_any_appointment():
    if not show_all_appointments():
        return

    appointment_id = input_int("Введите ID записи для отмены: ")
    if appointment_id is None:
        return

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT schedule_id FROM appointments WHERE id = ? AND status = 'active'",
        (appointment_id,)
    )

    result = cursor.fetchone()

    if result is None:
        print("Активная запись не найдена.")
        conn.close()
        return

    schedule_id = result[0]

    cursor.execute("""
        UPDATE appointments
        SET status = 'cancelled'
        WHERE id = ?
    """, (appointment_id,))

    cursor.execute("""
        UPDATE schedules
        SET is_available = 1
        WHERE id = ?
    """, (schedule_id,))

    conn.commit()
    conn.close()

    print("Запись отменена. Время снова доступно.")


def cancel_my_appointment():
    patient_id = input_int("Введите ваш ID пациента: ")
    if patient_id is None:
        return

    if not patient_exists(patient_id):
        print("Пациент с таким ID не найден.")
        return

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            appointments.id,
            doctors.full_name,
            schedules.date,
            schedules.time
        FROM appointments
        JOIN doctors ON appointments.doctor_id = doctors.id
        JOIN schedules ON appointments.schedule_id = schedules.id
        WHERE appointments.patient_id = ? AND appointments.status = 'active'
        ORDER BY schedules.date, schedules.time
    """, (patient_id,))

    appointments = cursor.fetchall()

    if not appointments:
        print("У вас нет активных записей.")
        conn.close()
        return

    print("\nВаши активные записи:")
    for app in appointments:
        print(f"{app[0]}. Врач: {app[1]} | Дата: {app[2]} | Время: {app[3]}")

    appointment_id = input_int("Введите ID записи для отмены: ")
    if appointment_id is None:
        conn.close()
        return

    cursor.execute("""
        SELECT schedule_id
        FROM appointments
        WHERE id = ? AND patient_id = ? AND status = 'active'
    """, (appointment_id, patient_id))

    result = cursor.fetchone()

    if result is None:
        print("Ошибка: активная запись не найдена.")
        conn.close()
        return

    schedule_id = result[0]

    cursor.execute("""
        UPDATE appointments
        SET status = 'cancelled'
        WHERE id = ?
    """, (appointment_id,))

    cursor.execute("""
        UPDATE schedules
        SET is_available = 1
        WHERE id = ?
    """, (schedule_id,))

    conn.commit()
    conn.close()

    print("Ваша запись отменена. Время снова доступно.")


def patient_menu():
    while True:
        print("\n=== Режим пациента ===")
        print("1. Зарегистрироваться")
        print("2. Показать врачей")
        print("3. Показать свободное расписание врача")
        print("4. Записаться на приём")
        print("5. Посмотреть мои записи")
        print("6. Отменить мою запись")
        print("0. Назад")

        choice = input("Выберите действие: ")

        if choice == "1":
            add_patient()
        elif choice == "2":
            show_doctors()
        elif choice == "3":
            show_schedule()
        elif choice == "4":
            create_appointment_for_patient()
        elif choice == "5":
            show_my_appointments()
        elif choice == "6":
            cancel_my_appointment()
        elif choice == "0":
            break
        else:
            print("Неверный пункт меню.")


def admin_menu():
    while True:
        print("\n=== Режим администратора ===")
        print("1. Добавить врача")
        print("2. Добавить расписание врачу")
        print("3. Показать всех врачей")
        print("4. Показать всех пациентов")
        print("5. Показать все записи")
        print("6. Отменить любую запись")
        print("0. Назад")

        choice = input("Выберите действие: ")

        if choice == "1":
            add_doctor()
        elif choice == "2":
            add_schedule()
        elif choice == "3":
            show_doctors()
        elif choice == "4":
            show_patients()
        elif choice == "5":
            show_all_appointments()
        elif choice == "6":
            cancel_any_appointment()
        elif choice == "0":
            break
        else:
            print("Неверный пункт меню.")


def main_menu():
    while True:
        print("\n=== Система записи к врачу ===")
        print("1. Режим пациента")
        print("2. Режим администратора")
        print("0. Выход")

        choice = input("Выберите режим: ")

        if choice == "1":
            patient_menu()
        elif choice == "2":
            admin_menu()
        elif choice == "0":
            print("Выход из программы.")
            break
        else:
            print("Неверный пункт меню.")


create_tables()
print("База данных создана или уже существует:", DB_NAME)
main_menu()
