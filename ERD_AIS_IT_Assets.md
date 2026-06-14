# Диаграмма «Сущность-Связь» для АИС учета ИТ-активов

```mermaid
erDiagram
    EMPLOYEES ||--o{ EQUIPMENT : "назначен_ответственным"
    EQUIPMENT ||--o{ INCIDENTS : "имеет_инциденты"
    EQUIPMENT ||--o{ EQUIPMENT_COMPONENTS : "содержит"
    COMPONENTS ||--o{ EQUIPMENT_COMPONENTS : "входит_в_состав"
    COMPONENTS ||--o{ PURCHASE_REQUESTS : "формирует_заявки"

    EMPLOYEES {
        int id PK
        string full_name
        string department
        string responsibility
    }

    EQUIPMENT {
        int id PK
        string asset_type
        string model
        string serial_number UK
        string location
        date commissioning_date
        date warranty_until
        string status
        int employee_id FK
        string notes
    }

    INCIDENTS {
        int id PK
        int equipment_id FK
        string issue_description
        datetime opened_at
        datetime resolved_at
        string resolution_note
        string incident_status
        string created_by
    }

    COMPONENTS {
        int id PK
        string component_type
        string model
        string sku UK
        int stock_qty
        int reorder_level
    }

    EQUIPMENT_COMPONENTS {
        int id PK
        int equipment_id FK
        int component_id FK
        int quantity
    }

    PURCHASE_REQUESTS {
        int id PK
        int component_id FK
        int requested_qty
        string reason
        datetime created_at
        string request_status
    }
```

## Краткие пояснения по связям

- `employees (1) -> (N) equipment` — один сотрудник может отвечать за несколько устройств.
- `equipment (1) -> (N) incidents` — у одного устройства может быть множество инцидентов.
- `equipment (N) <-> (N) components` — реализовано через таблицу `equipment_components`.
- `components (1) -> (N) purchase_requests` — на одну позицию комплектующих может быть много заявок.
