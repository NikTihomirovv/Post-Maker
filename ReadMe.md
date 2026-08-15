


### Запуск контейнера ollama
docker run -d --name ollama-deepseek -p 11434:11434 -v ollama_data:/root/.ollama -v ./models:/root/.ollama/models --restart unless-stopped ollama/ollama

### Загрузка модели
docker exec -it ollama-deepseek ollama pull deepseek-r1:8b


Все новости: https://www.sciencedaily.com/rss/all.xml
Top Environment: https://www.sciencedaily.com/rss/top/environment.xml
Top Society: https://www.sciencedaily.com/rss/top/society.xml
Strange & Offbeat: https://www.sciencedaily.com/rss/strange_offbeat.xml
Most Popular: https://www.sciencedaily.com/rss/most_popular.xml

The Guardian (Здоровье): https://www.theguardian.com/health/rss                             Добавил
NPR (Здоровье): https://feeds.npr.org/1128/rss.xml                                          Добавил
New York Times (Здоровье): https://rss.nytimes.com/services/xml/rss/nyt/Health.xml          403
Cardiovascular: https://www.bioworld.com/rss/topic/240-cardiovascular                       Нужна другая структура парсинга
Aging: https://www.bioworld.com/rss/topic/566-aging
Biomarkers: https://www.bioworld.com/rss/topic/543-biomarkers
Diagnostics: https://www.bioworld.com/rss/21
Digital health: https://www.bioworld.com/rss/22
Drugs: https://www.bioworld.com/rss/18
Cancer/Oncology: https://www.bioworld.com/rss/15
Endocrine/Metabolic (Diabetes, Obesity): https://www.bioworld.com/rss/16
FDA: https://www.bioworld.com/rss/topic/430-fda
EMA: https://www.bioworld.com/rss/topic/430-ema
China (NMPA): https://www.bioworld.com/rss/28
Briefs (краткие новости индустрии): https://www.bioworld.com/rss/11
Nature: https://www.nature.com/nature.rss
Science: https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science
arXiv (AI): https://rss.arxiv.org/rss/cs.AI
arXiv (Bioinformatics): https://rss.arxiv.org/rss/q-bio






BBC News (Здоровье): https://feeds.bbci.co.uk/news/health/rss.xml                                   VPN
CNN (Здоровье): https://feeds.bbci.co.uk/news/health/rss.xml                                        VPN
ANSM (Франция, лекарственная безопасность): https://ansm.sante.fr/rss/informations_securite         VPN


ABC News (Здоровье): https://abcnews.go.com/abcnews/healthnews                                      ХЗ





Наука и жизнь	https://www.nkj.ru/en/rssdef/
PsyJournals.ru	https://psyjournals.ru/rss/
