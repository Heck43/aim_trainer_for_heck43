# pyi_rth_panda3d.py
# Runtime hook для Panda3D - настраивает PATH для поиска DLL

import sys
import os

# Определяем путь к папке с DLL
dll_path = None

if hasattr(sys, '_MEIPASS'):
    # PyInstaller создает временную папку _MEIPASS
    dll_path = sys._MEIPASS
else:
    # Если не в PyInstaller, используем папку с exe
    if hasattr(sys, 'frozen'):
        exe_dir = os.path.dirname(sys.executable)
        # Проверяем папку _internal (новый формат PyInstaller)
        internal_dir = os.path.join(exe_dir, '_internal')
        if os.path.exists(internal_dir):
            dll_path = internal_dir
        else:
            dll_path = exe_dir
    else:
        dll_path = os.path.dirname(os.path.abspath(__file__))

if dll_path:
    # Добавляем в PATH
    if dll_path not in os.environ.get('PATH', ''):
        os.environ['PATH'] = dll_path + os.pathsep + os.environ.get('PATH', '')
    
    # Используем os.add_dll_directory() для Python 3.8+ (более надежно)
    if sys.version_info >= (3, 8):
        try:
            os.add_dll_directory(dll_path)
        except (AttributeError, OSError):
            pass
    
    # Также добавляем папку с exe (на случай если DLL там)
    if hasattr(sys, 'frozen'):
        exe_dir = os.path.dirname(sys.executable)
        if exe_dir and exe_dir != dll_path:
            if exe_dir not in os.environ.get('PATH', ''):
                os.environ['PATH'] = exe_dir + os.pathsep + os.environ.get('PATH', '')
            if sys.version_info >= (3, 8):
                try:
                    os.add_dll_directory(exe_dir)
                except (AttributeError, OSError):
                    pass