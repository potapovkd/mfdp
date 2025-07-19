import streamlit as st
import requests
import os
import pandas as pd
import io

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

if not st.session_state.get("access_token"):
    st.session_state.access_token = None

st.title("🛍️ Marketplace Price Optimization")
st.markdown("**Система оптимизации цен для маркетплейса на основе ML**")

# Боковая панель для навигации
st.sidebar.title("Навигация")
page = st.sidebar.selectbox("Выберите раздел:", [
    "Аутентификация",
    "Баланс и тарифы",
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

# === БАЛАНС И ТАРИФЫ ===
elif page == "Баланс и тарифы":
    st.header("💰 Баланс и тарифы")

    if not st.session_state.access_token:
        st.error("❌ Необходима авторизация")
        st.stop()

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💳 Ваш баланс")
        
        # Инициализируем значения в session_state
        if "balance" not in st.session_state:
            st.session_state.balance = None
        if "add_amount" not in st.session_state:
            st.session_state.add_amount = 10.00
        
        if st.button("Обновить баланс", key="refresh_balance"):
            try:
                response = requests.get(f"{API_BASE_URL}/users/balance/", headers=headers)
                response.raise_for_status()
                balance_data = response.json()
                st.session_state.balance = balance_data['balance']
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
        
        # Отображаем текущий баланс
        if st.session_state.balance is not None:
            st.metric("Текущий баланс", f"${st.session_state.balance}")

        # Пополнение баланса
        st.subheader("💵 Пополнить баланс")
        add_amount = st.number_input(
            "Сумма для пополнения ($):", 
            min_value=0.01, 
            value=st.session_state.add_amount, 
            step=0.01,
            key="add_amount_input"
        )
        
        # Обновляем session_state
        st.session_state.add_amount = add_amount
        
        if st.button("Пополнить", key="add_balance"):
            try:
                response = requests.post(f"{API_BASE_URL}/users/balance/add/?amount={add_amount}", headers=headers)
                response.raise_for_status()
                result = response.json()
                st.success(f"✅ {result['message']}")
                # Обновляем баланс в session_state
                st.session_state.balance = result['balance']
                st.rerun()
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")

    with col2:
        st.subheader("📋 Тарифы")
        
        # Загружаем тарифы при первой загрузке страницы
        if "tariffs" not in st.session_state:
            try:
                response = requests.get(f"{API_BASE_URL}/users/tariffs/", headers=headers)
                response.raise_for_status()
                st.session_state.tariffs = response.json()
            except Exception as e:
                st.error(f"❌ Ошибка загрузки тарифов: {e}")
                st.session_state.tariffs = None
        
        # Отображаем тарифы
        if st.session_state.tariffs:
            tariffs = st.session_state.tariffs
            st.info(f"💰 Стоимость одного прогноза: ${tariffs['single_item_price']}")
            st.info(f"🎯 Скидка при {tariffs['bulk_discount_threshold']}+ товарах: {tariffs['bulk_discount_percent']}%")
            st.info(f"📦 Максимум товаров в запросе: {tariffs['max_items_per_request']}")
            
            # Калькулятор стоимости
            st.subheader("🧮 Калькулятор стоимости")
            
            # Инициализируем значение в session_state
            if "items_count" not in st.session_state:
                st.session_state.items_count = 1
            
            # Используем key для сохранения состояния
            items_count = st.number_input(
                "Количество товаров:", 
                min_value=1, 
                max_value=100, 
                value=st.session_state.items_count,
                key="items_count_input"
            )
            
            # Обновляем session_state
            st.session_state.items_count = items_count
            
            if st.button("Рассчитать стоимость", key="calculate_cost"):
                try:
                    cost_response = requests.post(f"{API_BASE_URL}/users/calculate-cost/?items_count={items_count}", headers=headers)
                    cost_response.raise_for_status()
                    cost_data = cost_response.json()
                    
                    # Сохраняем результат в session_state
                    st.session_state.cost_result = cost_data
                    
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
            
            # Отображаем результат, если он есть
            if "cost_result" in st.session_state:
                cost_data = st.session_state.cost_result
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Общая стоимость", f"${cost_data['cost']}")
                with col_b:
                    st.metric("Стоимость за товар", f"${cost_data['cost_per_item']}")
        else:
            st.warning("⚠️ Не удалось загрузить тарифы")

# === ТОВАРЫ ===
elif page == "Товары":
    st.header("📦 Управление товарами")

    if not st.session_state.access_token:
        st.error("❌ Необходима авторизация")
        st.stop()

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

    tab1, tab2, tab3 = st.tabs(["Мои товары", "Добавить товар", "Загрузить из Excel"])

    with tab1:
        if st.button("Загрузить товары"):
            try:
                response = requests.get(f"{API_BASE_URL}/products/", headers=headers)
                response.raise_for_status()
                products = response.json()

                if products:
                    st.session_state.user_products = products
                    
                    for product in products:
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{product['name']}**")
                                st.write(f"Категория: {product['category_name']}")
                                st.write(f"Бренд: {product['brand_name']}")
                                st.write(f"Состояние: {product['item_condition_id']}/5")
                                if product["current_price"]:
                                    st.metric("Текущая цена", f"${product['current_price']:.2f}")
                            with col2:
                                st.write(f"ID: {product['id']}")
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

    with tab3:
        st.subheader("📁 Загрузка товаров из Excel")
        
        # Скачать шаблон
        try:
            response = requests.get(f"{API_BASE_URL}/users/products/template/")
            response.raise_for_status()
            
            # Используем st.download_button для правильного скачивания
            st.download_button(
                label="📥 Скачать шаблон Excel",
                data=response.content,
                file_name="products_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Скачайте шаблон, заполните его и загрузите обратно"
            )
            st.info("📝 Заполните шаблон и загрузите обратно")
        except Exception as e:
            st.error(f"❌ Ошибка загрузки шаблона: {e}")
        
        # Загрузка файла
        uploaded_file = st.file_uploader("Выберите Excel файл с товарами", type=['xlsx', 'xls'])
        
        if uploaded_file is not None:
            if st.button("📤 Загрузить товары"):
                try:
                    files = {"file": uploaded_file}
                    response = requests.post(
                        f"{API_BASE_URL}/products/upload-excel/",
                        files=files,
                        headers=headers
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    st.success(f"✅ {result['message']}")
                    st.info(f"📊 Создано товаров: {result['created_count']}")
                    
                    if result['errors']:
                        st.warning("⚠️ Ошибки при обработке:")
                        for error in result['errors']:
                            st.write(f"• {error}")
                            
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")

# === ПРОГНОЗИРОВАНИЕ ЦЕНЫ ===
elif page == "Прогнозирование цены":
    st.header("🤖 ML прогнозирование цены")

    if not st.session_state.access_token:
        st.error("❌ Необходима авторизация")
        st.stop()

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

    tab1, tab2 = st.tabs(["Одиночный прогноз", "Множественный прогноз"])

    with tab1:
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
                            st.subheader("📈 Анализ категории")
                            analysis = result["category_analysis"]
                            st.write(f"**Категория:** {analysis.get('category', 'N/A')}")
                            st.write(f"**Рекомендация:** {analysis.get('recommendation', 'N/A')}")
                            st.write(f"**Позиция на рынке:** {analysis.get('market_position', 'N/A')}")

                    except Exception as e:
                        st.error(f"❌ Ошибка: {e}")
                else:
                    st.warning("⚠️ Заполните обязательные поля")

    with tab2:
        st.subheader("📦 Прогнозирование для множества товаров")
        
        # Загружаем товары пользователя если еще не загружены
        if "user_products" not in st.session_state:
            try:
                response = requests.get(f"{API_BASE_URL}/products/", headers=headers)
                response.raise_for_status()
                st.session_state.user_products = response.json()
            except Exception as e:
                st.error(f"❌ Ошибка загрузки товаров: {e}")
                st.stop()
        
        if st.session_state.user_products:
            # Создаем список товаров для выбора
            product_options = {f"{p['name']} (ID: {p['id']})": p['id'] for p in st.session_state.user_products}
            
            selected_products = st.multiselect(
                "Выберите товары для прогнозирования:",
                options=list(product_options.keys()),
                help="Можно выбрать несколько товаров. Стоимость: $5 за товар"
            )
            
            if selected_products:
                product_ids = [product_options[name] for name in selected_products]
                st.info(f"💰 Стоимость прогнозирования: ${len(product_ids) * 5.00}")
                
                if st.button("🔮 Получить прогнозы"):
                    try:
                        with st.spinner(f"Прогнозирую цены для {len(product_ids)} товаров..."):
                            response = requests.post(
                                f"{API_BASE_URL}/products/pricing/predict-multiple/",
                                json=product_ids,
                                headers=headers
                            )
                            response.raise_for_status()
                            result = response.json()
                        
                        st.success(f"✅ {result['message']}")
                        st.info(f"💳 Списано: ${result['charged_amount']}")
                        st.info(f"💰 Новый баланс: ${result['new_balance']}")
                        
                        # Показываем результаты
                        st.subheader("📊 Результаты прогнозирования")
                        
                        for item in result['results']:
                            with st.container():
                                col1, col2, col3 = st.columns([2, 1, 1])
                                with col1:
                                    st.write(f"**{item['product_name']}**")
                                with col2:
                                    prediction = item['prediction']
                                    st.metric("Цена", f"${prediction['predicted_price']:.2f}")
                                with col3:
                                    st.metric("Уверенность", f"{prediction['confidence_score']:.1%}")
                                st.divider()
                        
                        # Кнопка экспорта
                        try:
                            export_response = requests.post(
                                f"{API_BASE_URL}/products/pricing/export-results/",
                                json=result['results'],
                                headers=headers
                            )
                            export_response.raise_for_status()
                            
                            filename = f"price_predictions_{len(product_ids)}_items.xlsx"
                            st.download_button(
                                label="📥 Экспорт в Excel",
                                data=export_response.content,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                help="Скачайте результаты прогнозирования в Excel"
                            )
                        except Exception as e:
                            st.error(f"❌ Ошибка экспорта: {e}")
                                
                    except Exception as e:
                        st.error(f"❌ Ошибка: {e}")
        else:
            st.info("📝 У вас пока нет товаров. Добавьте товары в разделе 'Товары'")

# === АНАЛИЗ ЦЕН ===
elif page == "Анализ цен":
    st.header("📊 Анализ цен")

    if not st.session_state.access_token:
        st.error("❌ Необходима авторизация")
        st.stop()

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

    st.info("💡 Анализ ценовых характеристик товара (бесплатно)")

    with st.form("analyze_price"):
        name = st.text_input("Название товара*:")
        description = st.text_area("Описание товара:")
        category = st.selectbox("Категория:", [
            "Electronics", "Fashion", "Home & Garden", "Books", "Sports & Outdoors",
            "Beauty", "Kids & Baby", "Automotive", "Other"
        ])
        brand = st.text_input("Бренд:", value="Unknown")
        condition = st.slider("Состояние (1=новый, 5=плохое):", 1, 5, 1)
        shipping = st.radio("Кто платит за доставку:", ["Покупатель", "Продавец"])

        if st.form_submit_button("📊 Анализировать товар"):
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

                    with st.spinner("Анализирую товар..."):
                        response = requests.post(
                            f"{API_BASE_URL}/products/pricing/analyze/",
                            json={"product_data": product_data},
                            headers=headers
                        )
                        response.raise_for_status()
                        result = response.json()

                    st.success("✅ Анализ готов!")

                    # Показываем результаты анализа
                    if "features" in result:
                        st.subheader("🔍 Анализ признаков")
                        features = result["features"]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Текстовые признаки:**")
                            st.write(f"• Длина названия: {features.get('name_length', 0)} символов")
                            st.write(f"• Длина описания: {features.get('description_length', 0)} символов")
                            st.write(f"• Количество слов в названии: {features.get('name_words', 0)}")
                            st.write(f"• Количество слов в описании: {features.get('description_words', 0)}")
                        
                        with col2:
                            st.write("**Категориальные признаки:**")
                            st.write(f"• Категория: {features.get('category', 'N/A')}")
                            st.write(f"• Бренд: {features.get('brand', 'N/A')}")
                            st.write(f"• Состояние: {features.get('condition_text', 'N/A')}")
                            st.write(f"• Доставка: {'Продавец платит' if features.get('shipping', 0) == 1 else 'Покупатель платит'}")

                    if "category_analysis" in result:
                        st.subheader("📊 Анализ категории")
                        category_analysis = result["category_analysis"]
                        st.write(f"**Диапазон цен:** {category_analysis.get('price_range', 'N/A')}")
                        st.write(f"**Ключевые факторы:** {', '.join(category_analysis.get('key_factors', []))}")
                        st.write(f"**Совет:** {category_analysis.get('tips', 'N/A')}")

                    if "recommendations" in result:
                        st.subheader("💡 Рекомендации")
                        recommendations = result["recommendations"]
                        for rec in recommendations:
                            st.write(f"• {rec}")

                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
            else:
                st.warning("⚠️ Заполните обязательные поля")

# === ФУТЕР ===
st.markdown("---")
st.markdown("🛍️ **Marketplace Price Optimization** | Powered by CatBoost ML")
