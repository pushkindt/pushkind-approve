from approve.main.routes_messages import get_email_recipients


def test_get_email_recipients(app, users):
    assert get_email_recipients(users) == [
        ("admin", "Роль: Администратор"),
        ("initiative", "Роль: Инициатор"),
        ("validator", "Роль: Валидатор"),
        ("purchaser", "Роль: Закупщик"),
        ("supervisor", "Роль: Наблюдатель"),
        ("vendor", "Роль: Поставщик"),
        ("admin@example.com", "admin"),
        ("initiative@example.com", "initiative"),
        ("validator@example.com", "validator"),
        ("purchaser@example.com", "purchaser"),
        ("supervisor@example.com", "supervisor"),
        ("vendor@example.com", "vendor"),
    ]
