import streamlit as st
import requests
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

if not st.session_state.get("access_token"):
    st.session_state.access_token = None

st.title("🛍️ Marketplace Price Optimization")
st.markdown("**Система оптимизации цен для маркетплейса на основе ML**")

# Боковая панель для навигации
st.sidebar.title("Навигация")
page = st.sidebar.selectbox("Выберите раздел:", [
    "Аутентификация",
    "Товары",
    "Прогнозирование цены",
    "Анализ цен"
])

# === АУТЕНТИФИКАЦИЯ ===
if page == "Аутентификация":
    st.header("🔐 Управление аккаунтом")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Регистрация")
        reg_email = st.text_input("Email:", key="reg_email")
        reg_password = st.text_input("Пароль:", type="password", key="reg_password")

        if st.button("Зарегистрироваться"):
            if reg_email and reg_password:
                try:
                    response = requests.post(f"{API_BASE_URL}/users/", json={
                        "email": reg_email,
                        "password": reg_password
                    })
                    response.raise_for_status()
                    st.success("✅ Пользователь успешно зарегистрирован!")
                except Exception as e:
                    st.error(f"❌ Ошибка регистрации: {e}")
            else:
                st.warning("⚠️ Заполните все поля")

    with col2:
        st.subheader("Вход в систему")
        email = st.text_input("Email:", key="login_email")
        password = st.text_input("Пароль:", type="password", key="login_password")

        if st.button("Войти"):
            if email and password:
                try:
                    response = requests.post(f"{API_BASE_URL}/users/auth/", json={
                        "email": email,
                        "password": password
                    })
                    response.raise_for_status()
                    token_data = response.json()
                    st.session_state.access_token = token_data["access_token"]
                    st.success("✅ Успешная аутентификация!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Ошибка входа: {e}")
            else:
                st.warning("⚠️ Введите email и пароль")

    if st.session_state.access_token:
        st.success("🟢 Вы авторизованы!")
        if st.button("Выйти"):
            st.session_state.access_token = None
            st.rerun()
    else:
        st.warning("🔴 Войдите для доступа к функциям")

# === ТОВАРЫ ===
elif page == "Товары":
    st.header("📦 Управление товарами")

    if not st.session_state.access_token:
        st.error("❌ Необходима авторизация")
        st.stop()

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

    tab1, tab2 = st.tabs(["Мои товары", "Добавить товар"])

    with tab1:
        if st.button("Загрузить товары"):
            try:
                response = requests.get(f"{API_BASE_URL}/products/", headers=headers)
                response.raise_for_status()
                products = response.json()

                if products:
                    for product in products:
                        with st.container():
                            st.markdown(f"**{product['name']}**")
                            st.write(f"Категория: {product['category_name']}")
                            st.write(f"Бренд: {product['brand_name']}")
                            st.write(f"Состояние: {product['item_condition_id']}/5")
                            if product["current_price"]:
                                st.metric("Текущая цена", f"${product['current_price']:.2f}")
                            st.divider()
                else:
                    st.info("У вас пока нет товаров")
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")

    with tab2:
        with st.form("add_product"):
            name = st.text_input("Название товара*:")
            description = st.text_area("Описание:")
            category = st.selectbox("Категория:", [
                "Electronics", "Fashion", "Home", "Books", "Sports", "Other"
            ])
            brand = st.text_input("Бренд:", value="Unknown")
            condition = st.slider("Состояние (1=новый, 5=плохое):", 1, 5, 1)
            shipping = st.radio("Доставка:", ["Покупатель платит", "Продавец платит"])

            if st.form_submit_button("Добавить товар"):
                if name and category:
                    try:
                        product_data = {
                            "name": name,
                            "item_description": description,
                            "category_name": category,
                            "brand_name": brand,
                            "item_condition_id": condition,
                            "shipping": 1 if shipping == "Продавец платит" else 0
                        }
                        response = requests.post(
                            f"{API_BASE_URL}/products/",
                            json=product_data,
                            headers=headers
                        )
                        response.raise_for_status()
                        st.success("✅ Товар добавлен!")
                    except Exception as e:
                        st.error(f"❌ Ошибка: {e}")
                else:
                    st.warning("⚠️ Заполните обязательные поля")

# === ПРОГНОЗИРОВАНИЕ ЦЕНЫ ===
elif page == "Прогнозирование цены":
    st.header("🤖 ML прогнозирование цены")

    if not st.session_state.access_token:
        st.error("❌ Необходима авторизация")
        st.stop()

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

    st.info("💡 Стоимость прогноза: $5.00")

    with st.form("predict_price"):
        name = st.text_input("Название товара*:")
        description = st.text_area("Описание товара:")
        category = st.selectbox("Категория:", [
            "Electronics", "Fashion", "Home & Garden", "Books", "Sports & Outdoors",
            "Beauty", "Kids & Baby", "Automotive", "Other"
        ])
        brand = st.text_input("Бренд:", value="Unknown")
        condition = st.slider("Состояние (1=новый, 5=плохое):", 1, 5, 1)
        shipping = st.radio("Кто платит за доставку:", ["Покупатель", "Продавец"])

        if st.form_submit_button("🔮 Получить прогноз цены"):
            if name and category:
                try:
                    product_data = {
                        "name": name,
                        "item_description": description,
                        "category_name": category,
                        "brand_name": brand,
                        "item_condition_id": condition,
                        "shipping": 1 if shipping == "Продавец" else 0
                    }

                    with st.spinner("Анализирую товар и прогнозирую цену..."):
                        response = requests.post(
                            f"{API_BASE_URL}/products/pricing/predict/",
                            json={"product_data": product_data},
                            headers=headers
                        )
                        response.raise_for_status()
                        result = response.json()

                    st.success("✅ Прогноз готов!")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("💰 Прогноз цены", f"${result['predicted_price']:.2f}")
                    with col2:
                        st.metric("🎯 Уверенность", f"{result['confidence_score']:.1%}")
                    with col3:
                        price_range = result["price_range"]
                        st.metric("📊 Диапазон", f"${price_range['min']:.2f} - ${price_range['max']:.2f}")

                    if "category_analysis" in result:
                        st.write("📈 **Анализ по категории:**")
                        for key, value in result["category_analysis"].items():
                            st.write(f"• {key}: {value}")

                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
            else:
                st.warning("⚠️ Заполните название и категорию")

# === АНАЛИЗ ЦЕН ===
elif page == "Анализ цен":
    st.header("📊 Анализ ценовых характеристик")

    if not st.session_state.access_token:
        st.error("❌ Необходима авторизация")
        st.stop()

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

    # Информация о сервисе
    try:
        response = requests.get(f"{API_BASE_URL}/products/pricing/info/")
        if response.status_code == 200:
            info = response.json()
            st.success("🤖 **Информация о ML модели:**")
            st.write(f"• Тип модели: {info.get('model_type', 'N/A')}")
            st.write(f"• Версия: {info.get('version', 'N/A')}")
            st.write(f"• Количество признаков: {info.get('features_count', 'N/A')}")
    except:
        pass

    st.subheader("🔍 Быстрый анализ товара")

    with st.form("analyze_product"):
        name = st.text_input("Название товара:")
        description = st.text_area("Описание:")
        category = st.selectbox("Категория:", [
            "Electronics", "Fashion", "Home", "Books", "Sports", "Other"
        ])

        if st.form_submit_button("Анализировать"):
            if name:
                try:
                    product_data = {
                        "name": name,
                        "item_description": description,
                        "category_name": category,
                        "brand_name": "Unknown",
                        "item_condition_id": 1,
                        "shipping": 0
                    }

                    response = requests.post(
                        f"{API_BASE_URL}/products/pricing/analyze/",
                        json={"product_data": product_data},
                        headers=headers
                    )
                    response.raise_for_status()
                    analysis = response.json()

                    st.success("✅ Анализ завершен!")
                    st.json(analysis)

                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")

# === ФУТЕР ===
st.markdown("---")
st.markdown("🛍️ **Marketplace Price Optimization** | Powered by CatBoost ML")
