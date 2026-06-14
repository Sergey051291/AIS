from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from db import get_connection, init_db, seed_demo_data

st.set_page_config(page_title="АИС учета и мониторинга ИТ-активов", layout="wide")
st.title("АИС учета и мониторинга ИТ-активов и комплектующих")


def run_query(query, params=()):
    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def run_exec(query, params=()):
    with get_connection() as conn:
        conn.execute(query, params)


init_db()
seed_demo_data()

st.caption(
    "Отделы: сопровождение вычислительной техники и служба логистики/складского учета ИТ-оборудования."
)

tabs = st.tabs(
    [
        "Карточка ИТ-актива",
        "Учет оборудования",
        "Инциденты",
        "Гарантия",
        "Склад и закупки",
        "Отчетность",
    ]
)

with tabs[0]:
    st.subheader("Форма: Карточка ИТ-актива")
    equipment_rows = run_query(
        """
        SELECT e.id, e.asset_type, e.model, e.serial_number, e.location, e.status,
               e.commissioning_date, e.warranty_until,
               emp.full_name AS owner_name
        FROM equipment e
        LEFT JOIN employees emp ON emp.id = e.employee_id
        ORDER BY e.id
        """
    )
    options = {f"#{r['id']} | {r['asset_type']} | {r['model']} ({r['serial_number']})": r["id"] for r in equipment_rows}

    if options:
        selected_label = st.selectbox("Выберите устройство", list(options.keys()))
        equipment_id = options[selected_label]
        selected = next(r for r in equipment_rows if r["id"] == equipment_id)

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Тип:** {selected['asset_type']}")
            st.write(f"**Модель:** {selected['model']}")
            st.write(f"**Серийный номер:** {selected['serial_number']}")
            st.write(f"**Локация:** {selected['location']}")
        with col2:
            st.write(f"**Статус:** {selected['status']}")
            st.write(f"**Дата ввода:** {selected['commissioning_date']}")
            st.write(f"**Гарантия до:** {selected['warranty_until']}")
            st.write(f"**Ответственный:** {selected['owner_name'] or 'Не назначен'}")

        st.markdown("**Установленные комплектующие (ОЗУ/диск/видеокарта и т.д.)**")
        components = run_query(
            """
            SELECT c.component_type, c.model, ec.quantity
            FROM equipment_components ec
            JOIN components c ON c.id = ec.component_id
            WHERE ec.equipment_id = ?
            ORDER BY c.component_type
            """,
            (equipment_id,),
        )
        if components:
            st.dataframe(pd.DataFrame([dict(row) for row in components]), use_container_width=True)
        else:
            st.info("Для устройства пока не привязаны комплектующие.")
    else:
        st.warning("В системе нет оборудования.")

with tabs[1]:
    st.subheader("Форма: Учет оборудования")
    employees = run_query("SELECT id, full_name FROM employees ORDER BY full_name")
    employee_options = {"Не назначен": None, **{r["full_name"]: r["id"] for r in employees}}

    with st.form("new_equipment_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            asset_type = st.text_input("Тип оборудования", value="Рабочая станция")
            model = st.text_input("Модель")
            serial = st.text_input("Серийный номер")
        with c2:
            location = st.text_input("Местоположение")
            commissioning = st.date_input("Дата ввода в эксплуатацию", value=date.today())
            warranty_until = st.date_input("Гарантия до", value=date.today() + timedelta(days=365))
        with c3:
            owner_label = st.selectbox("Ответственный сотрудник", list(employee_options.keys()))
            status = st.selectbox("Статус", ["В эксплуатации", "В ремонте", "Списано"])
            notes = st.text_area("Примечание")

        submitted = st.form_submit_button("Сохранить оборудование")
        if submitted:
            if not (model and serial and location):
                st.error("Заполните обязательные поля: модель, серийный номер, местоположение.")
            else:
                try:
                    run_exec(
                        """
                        INSERT INTO equipment
                        (asset_type, model, serial_number, location, commissioning_date, warranty_until, status, employee_id, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            asset_type,
                            model,
                            serial,
                            location,
                            commissioning.isoformat(),
                            warranty_until.isoformat(),
                            status,
                            employee_options[owner_label],
                            notes.strip(),
                        ),
                    )
                    st.success("Оборудование добавлено.")
                except Exception as exc:
                    st.error(f"Ошибка добавления: {exc}")

with tabs[2]:
    st.subheader("Мониторинг состояния и история инцидентов")
    equipment_short = run_query("SELECT id, model, serial_number FROM equipment ORDER BY id")
    equipment_map = {f"#{r['id']} | {r['model']} ({r['serial_number']})": r["id"] for r in equipment_short}

    with st.form("incident_form", clear_on_submit=True):
        target = st.selectbox("Устройство", list(equipment_map.keys()) if equipment_map else ["Нет данных"])
        issue = st.text_area("Описание неисправности")
        created_by = st.text_input("Кто зарегистрировал", value="Инженер отдела сопровождения")
        add_incident = st.form_submit_button("Зарегистрировать инцидент")
        if add_incident:
            if not equipment_map or not issue.strip():
                st.error("Нужно выбрать устройство и заполнить описание.")
            else:
                run_exec(
                    """
                    INSERT INTO incidents (equipment_id, issue_description, opened_at, created_by)
                    VALUES (?, ?, ?, ?)
                    """,
                    (equipment_map[target], issue.strip(), datetime.now().isoformat(timespec="seconds"), created_by.strip()),
                )
                st.success("Инцидент зарегистрирован.")

    incidents = run_query(
        """
        SELECT i.id, e.model, e.serial_number, i.issue_description, i.opened_at, i.resolved_at, i.incident_status
        FROM incidents i
        JOIN equipment e ON e.id = i.equipment_id
        ORDER BY i.id DESC
        """
    )
    st.markdown("**История инцидентов**")
    if incidents:
        st.dataframe(pd.DataFrame([dict(r) for r in incidents]), use_container_width=True)
    else:
        st.info("Инцидентов пока нет.")

with tabs[3]:
    st.subheader("Алгоритм проверки гарантийного срока")
    soon_days = st.slider("Порог предупреждения (дней)", min_value=7, max_value=180, value=45, step=1)
    eq_for_warranty = run_query(
        "SELECT id, model, serial_number, location, warranty_until FROM equipment WHERE status <> 'Списано' ORDER BY warranty_until"
    )
    today = date.today()
    rows = []
    for r in eq_for_warranty:
        warranty_date = datetime.fromisoformat(r["warranty_until"]).date()
        days_left = (warranty_date - today).days
        severity = "Критично" if days_left < 0 else ("Скоро истечет" if days_left <= soon_days else "ОК")
        rows.append(
            {
                "id": r["id"],
                "model": r["model"],
                "serial_number": r["serial_number"],
                "location": r["location"],
                "warranty_until": r["warranty_until"],
                "days_left": days_left,
                "status": severity,
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)
    st.warning("Подсветка нужна для планирования замены на критически важных узлах (например, стойки регистрации).")

with tabs[4]:
    st.subheader("Склад комплектующих и автоматизация заявок")
    components = run_query("SELECT * FROM components ORDER BY component_type, model")
    if components:
        comp_df = pd.DataFrame([dict(r) for r in components])
        comp_df["needs_reorder"] = comp_df["stock_qty"] <= comp_df["reorder_level"]
        st.dataframe(comp_df, use_container_width=True)

        low_stock = [dict(r) for r in components if r["stock_qty"] <= r["reorder_level"]]
        if low_stock:
            st.error("Обнаружены позиции с низким остатком.")
            for item in low_stock:
                missing = max(1, item["reorder_level"] - item["stock_qty"] + 1)
                if st.button(f"Сформировать заявку: {item['component_type']} {item['model']} (x{missing})"):
                    run_exec(
                        """
                        INSERT INTO purchase_requests (component_id, requested_qty, reason, created_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            item["id"],
                            missing,
                            "Остаток на складе ниже порога",
                            datetime.now().isoformat(timespec="seconds"),
                        ),
                    )
                    st.success("Заявка на закупку создана.")
        else:
            st.success("Складские остатки в норме.")
    else:
        st.info("Комплектующие не заведены.")

    requests = run_query(
        """
        SELECT pr.id, c.component_type, c.model, pr.requested_qty, pr.reason, pr.created_at, pr.request_status
        FROM purchase_requests pr
        JOIN components c ON c.id = pr.component_id
        ORDER BY pr.id DESC
        """
    )
    st.markdown("**Сформированные заявки на закупку**")
    if requests:
        st.dataframe(pd.DataFrame([dict(r) for r in requests]), use_container_width=True)
    else:
        st.info("Пока нет заявок.")

with tabs[5]:
    st.subheader("Отчетность")
    inventory = run_query(
        """
        SELECT e.id, e.asset_type, e.model, e.serial_number, e.location, e.status, emp.full_name AS owner_name
        FROM equipment e
        LEFT JOIN employees emp ON emp.id = e.employee_id
        ORDER BY e.id
        """
    )
    inv_df = pd.DataFrame([dict(r) for r in inventory])
    st.markdown("**Инвентаризационная ведомость**")
    st.dataframe(inv_df, use_container_width=True)
    st.download_button(
        "Скачать инвентаризационную ведомость (CSV)",
        data=inv_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"inventory_{date.today().isoformat()}.csv",
        mime="text/csv",
    )

    disposal_df = inv_df[inv_df["status"] == "Списано"].copy()
    st.markdown("**Акт списания (автогенерация на основе статуса)**")
    st.dataframe(disposal_df, use_container_width=True)
    st.download_button(
        "Скачать акт списания (CSV)",
        data=disposal_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"disposal_{date.today().isoformat()}.csv",
        mime="text/csv",
    )
