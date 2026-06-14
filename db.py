import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "ais_assets.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                department TEXT NOT NULL,
                responsibility TEXT
            );

            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_type TEXT NOT NULL,
                model TEXT NOT NULL,
                serial_number TEXT UNIQUE NOT NULL,
                location TEXT NOT NULL,
                commissioning_date TEXT NOT NULL,
                warranty_until TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'В эксплуатации',
                employee_id INTEGER,
                notes TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            );

            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_type TEXT NOT NULL,
                model TEXT NOT NULL,
                sku TEXT UNIQUE,
                stock_qty INTEGER NOT NULL DEFAULT 0,
                reorder_level INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS equipment_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL,
                component_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (equipment_id) REFERENCES equipment (id) ON DELETE CASCADE,
                FOREIGN KEY (component_id) REFERENCES components (id) ON DELETE CASCADE,
                UNIQUE (equipment_id, component_id)
            );

            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL,
                issue_description TEXT NOT NULL,
                opened_at TEXT NOT NULL,
                resolved_at TEXT,
                resolution_note TEXT,
                incident_status TEXT NOT NULL DEFAULT 'Открыт',
                created_by TEXT,
                FOREIGN KEY (equipment_id) REFERENCES equipment (id)
            );

            CREATE TABLE IF NOT EXISTS purchase_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id INTEGER NOT NULL,
                requested_qty INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                request_status TEXT NOT NULL DEFAULT 'Создана',
                FOREIGN KEY (component_id) REFERENCES components (id)
            );
            """
        )


def seed_demo_data():
    with get_connection() as conn:
        employee_count = conn.execute("SELECT COUNT(*) AS c FROM employees").fetchone()["c"]
        if employee_count == 0:
            conn.executemany(
                "INSERT INTO employees (full_name, department, responsibility) VALUES (?, ?, ?)",
                [
                    ("Иванов Сергей Петрович", "Служба логистики ИТ", "Учет складских остатков"),
                    ("Полякова Анна Дмитриевна", "Отдел сопровождения ВТ", "Ремонт и модернизация"),
                    ("Смирнов Павел Олегович", "Операционный блок", "Ответственный за стойки регистрации"),
                ],
            )

        component_count = conn.execute("SELECT COUNT(*) AS c FROM components").fetchone()["c"]
        if component_count == 0:
            conn.executemany(
                """
                INSERT INTO components (component_type, model, sku, stock_qty, reorder_level)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    ("Видеокарта", "NVIDIA GTX 1050", "GPU-1050", 3, 4),
                    ("Накопитель SSD", "Samsung 870 EVO 500GB", "SSD-870-500", 9, 5),
                    ("Монитор", "Dell P2422H", "MON-P2422H", 2, 3),
                    ("Картридж", "HP CF283A", "CRT-CF283A", 1, 5),
                ],
            )

        equipment_count = conn.execute("SELECT COUNT(*) AS c FROM equipment").fetchone()["c"]
        if equipment_count == 0:
            conn.executemany(
                """
                INSERT INTO equipment
                (asset_type, model, serial_number, location, commissioning_date, warranty_until, status, employee_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        "Рабочая станция",
                        "HP ProDesk 600 G5",
                        "HP-600G5-001",
                        "Стойка регистрации DME-12",
                        "2024-03-01",
                        "2027-03-01",
                        "В эксплуатации",
                        3,
                        "Критический узел регистрации пассажиров",
                    ),
                    (
                        "Ноутбук",
                        "Lenovo ThinkPad T14",
                        "LNV-T14-4421",
                        "Центральный офис, кабинет 401",
                        "2023-09-15",
                        "2026-09-15",
                        "В эксплуатации",
                        1,
                        "Используется в логистике",
                    ),
                ],
            )

        link_count = conn.execute("SELECT COUNT(*) AS c FROM equipment_components").fetchone()["c"]
        if link_count == 0:
            conn.executemany(
                """
                INSERT INTO equipment_components (equipment_id, component_id, quantity)
                VALUES (?, ?, ?)
                """,
                [
                    (1, 1, 1),
                    (1, 2, 1),
                    (1, 3, 2),
                    (2, 2, 1),
                ],
            )
