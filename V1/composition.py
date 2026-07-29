from settings import Settings
from managers.parsers_manager import ParsersManager
from managers.articles_manager import ArticlesManager
from managers.ai_manager import AIManager
from managers.db_manager import DBManager
from managers.vk_manager import VKManager


class Composition:
    """Основной класс для сборки проекта."""

    def __init__(self):

        self.settings = Settings()
        self.ai_manager = AIManager(self.settings)
        self.db_manager = DBManager(self.settings)
        self.aricles_manager = ArticlesManager(self.settings)
        self.parsers_manager = ParsersManager(self.settings)
        self.vk_manager = VKManager(self.settings)
        
    def destroy(self):
        """Освобождает все ресурсы"""
        if hasattr(self, 'ai_manager') and self.ai_manager:
            self.ai_manager.destroy()
        if hasattr(self, 'db_manager') and self.db_manager:
            self.db_manager.destroy()
        if hasattr(self, 'aricles_manager') and self.aricles_manager:
            self.aricles_manager.destroy()
        if hasattr(self, 'parsers_manager') and self.parsers_manager:
            self.parsers_manager.destroy()
        if hasattr(self, 'vk_manager') and self.vk_manager:
            self.vk_manager.destroy()