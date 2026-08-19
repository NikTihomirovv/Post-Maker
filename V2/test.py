from openai import OpenAI

# Инициализация клиента provod.ai
client = OpenAI(
    api_key="sk_fac90a60032cc7a46103fb21c4521835a17e1316ec9cd547",          # Ваш ключ API от provod.ai [citation:3]
    base_url="https://api.provod.ai/v1"   # Базовый URL для запросов [citation:1][citation:9]
)


# Запрос списка моделей
models = client.models.list()
for model in models.data:
    print(model.id)




response = client.chat.completions.create(
    model="deepseek-v4-flash-0731",  # ← выбрали модель
    messages=[
        {"role": "system", "content": "Ты — полезный ассистент."},
        {"role": "user", "content": "Кратко опиши, что такое ИИ."}
    ],
    temperature=0.7,
    max_tokens=10000
)

print(response.choices[0].message.content)