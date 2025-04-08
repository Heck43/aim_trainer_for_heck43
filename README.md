# Aim Trainer nsfw/sfm | Тренажер прицеливания nsfw/sfm

[English](#english) | [Русский](#русский)

---

<a name="english"></a>
# Aim Trainer [EN]

A modern 3D aim trainer game built with Python and Panda3D engine. This application helps players improve their aiming skills and reaction time in first-person shooter games.

![Game Screenshot](images/game_screenshot.png)

## Features

- 3D environment with realistic aim training
- Multiple weapon types with unique characteristics
- Customizable target settings and spawn rates
- Advanced hit detection system with damage multipliers
- Performance tracking and statistics
- Modern user interface with animated menus
- Configurable game settings including FOV, sensitivity, and graphics
- Special effects including hit markers, bullet traces, and shell casings
- Music system with multiple tracks and volume control
- Jump mechanics with combo system
- NSFW/SFM content support

![Features Showcase](images/features.png)

## Technical Details

- **Engine**: Panda3D 1.10.15
- **Language**: Python 3.x
- **Dependencies**: 
  - panda3d==1.10.15
  - numpy>=1.21.0
- **Configuration**: JSON-based settings system

## Requirements

- Python 3.x
- Panda3D engine
- Additional Python packages (specified in requirements.txt)
- Graphics card with OpenGL support

## Controls

![Controls Diagram](images/controls.png)

- Mouse movement to aim
- Left click to shoot targets
- Space to jump (with combo system)
- ESC to access menu
- Mouse wheel to switch weapons
- Right click to aim down sights
- 1-9 keys for quick weapon selection

## Installation

### Option 1: Using Pre-built Release
1. Download the latest release from the [Releases](https://github.com/your-repo/releases) page
2. Extract the archive to your desired location
3. Run `main.exe` to start the game

### Option 2: Building from Source
1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run `main.py` to start the game

![Installation Guide](images/installation.png)

## Development

This project is developed with focus on:
- Clean, maintainable Python code
- Modular architecture with separate components for:
  - Weapon systems
  - Target management
  - Effects and particles
  - Menu interface
  - Audio system
- Customizable game settings
- Smooth performance optimization
- Modern visual effects

![Development Architecture](images/architecture.png)

Feel free to contribute to the project or report any issues!

---

<a name="русский"></a>
# Тренажер прицеливания [RU]

Современный 3D тренажер прицеливания, созданный на Python с использованием движка Panda3D. Это приложение помогает игрокам улучшить навыки прицеливания и время реакции в шутерах от первого лица.

![Скриншот игры](images/game_screenshot.png)

## Особенности

- 3D окружение с реалистичной тренировкой прицеливания
- Различные типы оружия с уникальными характеристиками
- Настраиваемые параметры мишеней и частота их появления
- Продвинутая система определения попаданий с множителями урона
- Отслеживание производительности и статистика
- Современный пользовательский интерфейс с анимированными меню
- Настраиваемые игровые параметры (FOV, чувствительность, графика)
- Специальные эффекты: маркеры попаданий, следы пуль, гильзы
- Система музыки с несколькими треками и контролем громкости
- Механика прыжков с системой комбо
- Поддержка NSFW/SFM контента

![Демонстрация функций](images/features.png)

## Технические детали

- **Движок**: Panda3D 1.10.15
- **Язык**: Python 3.x
- **Зависимости**: 
  - panda3d==1.10.15
  - numpy>=1.21.0
- **Конфигурация**: Система настроек на основе JSON

## Требования

- Python 3.x
- Движок Panda3D
- Дополнительные пакеты Python (указаны в requirements.txt)
- Видеокарта с поддержкой OpenGL

## Управление

![Схема управления](images/controls.png)

- Движение мыши для прицеливания
- Левый клик для стрельбы по мишеням
- Пробел для прыжка (с системой комбо)
- ESC для доступа к меню
- Колесико мыши для смены оружия
- Правый клик для прицеливания
- Клавиши 1-9 для быстрого выбора оружия

## Установка

### Вариант 1: Использование готового релиза
1. Скачайте последний релиз со страницы [Releases](https://github.com/your-repo/releases)
2. Распакуйте архив в нужную папку
3. Запустите `main.exe` для старта игры

### Вариант 2: Сборка из исходного кода
1. Клонируйте этот репозиторий
2. Установите необходимые зависимости:
   ```
   pip install -r requirements.txt
   ```
3. Запустите `main.py` для старта игры

![Руководство по установке](images/installation.png)

## Разработка

Проект разработан с фокусом на:
- Чистый, поддерживаемый Python код
- Модульную архитектуру с отдельными компонентами для:
  - Систем оружия
  - Управления мишенями
  - Эффектов и частиц
  - Интерфейса меню
  - Аудио системы
- Настраиваемые игровые параметры
- Оптимизацию производительности
- Современные визуальные эффекты

![Архитектура разработки](images/architecture.png)

Не стесняйтесь вносить свой вклад в проект или сообщать о проблемах! 