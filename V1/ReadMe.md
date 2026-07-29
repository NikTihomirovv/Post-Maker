


### Запуск контейнера ollama
docker run -d --name ollama-deepseek -p 11434:11434 -v ollama_data:/root/.ollama -v ./models:/root/.ollama/models --restart unless-stopped ollama/ollama

### Загрузка модели
docker exec -it ollama-deepseek ollama pull deepseek-r1:8b


