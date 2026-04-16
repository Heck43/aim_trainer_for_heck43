"""
Точка входа для сервера мультиплеера
Запускается отдельно от клиента
"""
import sys
from pathlib import Path

# няяя добавляем корневую папку в путь чтобы питон нашёл multiplayer~~
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from multiplayer.server import main

if __name__ == "__main__":
    main()

