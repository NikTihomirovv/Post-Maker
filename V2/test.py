from openai import OpenAI

# Инициализация клиента provod.ai (такой же, как для текста)
client = OpenAI(
    api_key="sk_fac90a60032cc7a46103fb21c4521835a17e1316ec9cd547",
    base_url="https://api.provod.ai/v1"
)

# Генерация изображения
response = client.images.generate(
    model="gpt-image-2",  # или gemini-3-pro-image
    prompt="Кот в шляпе, сидящий на Луне, цифровое искусство",
    n=1,                  # количество изображений
    size="1024x1024"      # размер
)

# Сохраняем результат
image_url = response.data[0].url
print(f"Ссылка на изображение: {image_url}")