"""Unit тесты базы данных для системы ценовой оптимизации."""

import pytest
from sqlalchemy.orm import Session

from products.adapters.orm import ProductORM, TaskORM
from users.adapters.orm import UserORM


def test_create_user(session: Session):
    """Тест создания пользователя."""
    user = UserORM(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password"
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    db_user = session.query(UserORM).filter_by(id=user.id).first()
    assert db_user is not None
    assert db_user.email == "test@example.com"
    assert db_user.username == "testuser"


def test_create_product(session: Session, user):
    """Тест создания продукта."""
    product = ProductORM(
        user_id=user.id,
        name="Test Product",
        category_name="Electronics",
        brand_name="TestBrand"
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    db_product = session.query(ProductORM).filter_by(id=product.id).first()
    assert db_product is not None
    assert db_product.user_id == user.id
    assert db_product.name == "Test Product"


def test_create_task(session: Session, user):
    """Тест создания задачи ценообразования."""
    # Сначала создаем продукт
    product = ProductORM(
        user_id=user.id,
        name="Test Product",
        category_name="Electronics"
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    # Затем создаем задачу
    task = TaskORM(
        product_id=product.id,
        type="pricing",
        input_data='{"product": "test"}'
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    db_task = session.query(TaskORM).filter_by(id=task.id).first()
    assert db_task is not None
    assert db_task.product_id == product.id
    assert db_task.type == "pricing"


def test_fail_create_task_without_product(session: Session):
    """Тест создания задачи без продукта."""
    task = TaskORM(product_id=999, type="pricing")
    with pytest.raises(Exception):
        session.add(task)
        session.commit()
