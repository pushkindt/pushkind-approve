from approve.main.routes_messages import get_email_recipients


def test_get_email_recipients(app, users):
    assert get_email_recipients(users) == [
        (1, "Роль: Администратор"),
        (2, "Роль: Инициатор"),
        (3, "Роль: Валидатор"),
        (4, "Роль: Закупщик"),
        (5, "Роль: Наблюдатель"),
        (6, "Роль: Поставщик"),
        ("admin@example.com", "admin"),
        ("initiative@example.com", "initiative"),
        ("validator@example.com", "validator"),
        ("purchaser@example.com", "purchaser"),
        ("supervisor@example.com", "supervisor"),
        ("vendor@example.com", "vendor"),
    ]
