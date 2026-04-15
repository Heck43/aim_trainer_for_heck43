"""
Скрипт для проверки структуры модели игрока
Показывает есть ли кости/джоинты и их иерархию
"""
import sys
import os
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Filename, loadPrcFileData

# Фикс кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Отключаем окно
loadPrcFileData("", "window-type none")

class ModelInspector(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Находим путь к модели
        if getattr(sys, "frozen", False):
            base_path = os.path.abspath(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        model_dir = os.path.join(base_path, "model_textures")
        model_path = os.path.join(model_dir, "untitled.bam")

        if not os.path.exists(model_path):
            print(f"❌ Модель не найдена: {model_path}")
            sys.exit(1)

        print(f"✅ Загружаю модель: {model_path}\n")

        try:
            model = self.loader.loadModel(Filename.fromOsSpecific(model_path))
            if not model or model.isEmpty():
                print("❌ Не удалось загрузить модель")
                sys.exit(1)

            print("=" * 60)
            print("СТРУКТУРА МОДЕЛИ")
            print("=" * 60)

            # Получаем bounds модели
            bounds = model.getTightBounds()
            if bounds:
                min_pt, max_pt = bounds
                print(f"\n📏 Размеры модели:")
                print(f"   Min: ({min_pt.x:.2f}, {min_pt.y:.2f}, {min_pt.z:.2f})")
                print(f"   Max: ({max_pt.x:.2f}, {max_pt.y:.2f}, {max_pt.z:.2f})")
                print(f"   Высота: {max_pt.z - min_pt.z:.2f}")
                print(f"   Ширина: {max_pt.x - min_pt.x:.2f}")
                print(f"   Глубина: {max_pt.y - min_pt.y:.2f}")

            # Ищем кости/джоинты
            print("\n🦴 ПОИСК КОСТЕЙ/ДЖОИНТОВ:")
            joints = []
            self.find_joints(model, joints)

            if joints:
                print(f"\n✅ Найдено {len(joints)} костей/джоинтов:")
                for joint in joints:
                    pos = joint.getPos()
                    print(f"   - {joint.getName()}: pos=({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})")

                # Ищем ключевые кости для хитбоксов
                print("\n🎯 КЛЮЧЕВЫЕ КОСТИ ДЛЯ ХИТБОКСОВ:")
                key_bones = {
                    "голова": ["head", "Head", "HEAD", "neck", "Neck"],
                    "тело": ["spine", "Spine", "SPINE", "chest", "Chest", "torso", "Torso", "body", "Body"],
                    "левая рука": ["arm.l", "arm_l", "shoulder.l", "shoulder_l", "left_arm", "LeftArm", "L_arm"],
                    "правая рука": ["arm.r", "arm_r", "shoulder.r", "shoulder_r", "right_arm", "RightArm", "R_arm"],
                    "ноги": ["leg", "Leg", "LEG", "hip", "Hip", "thigh", "Thigh"]
                }

                found_bones = {}
                for part_name, patterns in key_bones.items():
                    for joint in joints:
                        joint_name = joint.getName()
                        if any(pattern in joint_name for pattern in patterns):
                            if part_name not in found_bones:
                                found_bones[part_name] = []
                            found_bones[part_name].append(joint_name)

                if found_bones:
                    for part, bones in found_bones.items():
                        print(f"   {part}: {', '.join(bones)}")
                else:
                    print("   ⚠️ Не найдены стандартные имена костей")
                    print("   Все кости:")
                    for joint in joints[:20]:  # Показываем первые 20
                        print(f"      - {joint.getName()}")
                    if len(joints) > 20:
                        print(f"      ... и ещё {len(joints) - 20} костей")
            else:
                print("   ❌ Кости/джоинты не найдены")
                print("   Это статичная меш без скелета")

            # Показываем иерархию узлов
            print("\n🌳 ИЕРАРХИЯ УЗЛОВ (первые уровни):")
            self.print_hierarchy(model, indent=0, max_depth=3)

            # Проверяем геометрию
            print("\n📦 ГЕОМЕТРИЯ:")
            geom_nodes = model.findAllMatches("**/+GeomNode")
            print(f"   Найдено GeomNode узлов: {geom_nodes.getNumPaths()}")

            if geom_nodes.getNumPaths() > 0:
                print("   Части модели:")
                for i in range(min(10, geom_nodes.getNumPaths())):
                    node = geom_nodes.getPath(i)
                    bounds = node.getTightBounds()
                    if bounds:
                        min_pt, max_pt = bounds
                        center_z = (min_pt.z + max_pt.z) / 2
                        height = max_pt.z - min_pt.z
                        print(f"      - {node.getName()}: высота={height:.2f}, центр_z={center_z:.2f}")

            print("\n" + "=" * 60)
            print("РЕКОМЕНДАЦИИ:")
            print("=" * 60)

            if joints:
                print("✅ Модель имеет скелет (rigged)")
                print("   Можно привязать хитбоксы к костям для точности")
                print("   Хитбоксы будут автоматически следовать за костями")
            else:
                print("⚠️ Модель статичная (без скелета)")
                print("   Варианты решения:")
                print("   1. Вычислить хитбоксы по геометрии (bounding boxes частей)")
                print("   2. Использовать масштабируемые хитбоксы относительно размера модели")
                print("   3. Добавить конфигурацию хитбоксов для каждой модели")

        except Exception as e:
            print(f"❌ Ошибка при анализе модели: {e}")
            import traceback
            traceback.print_exc()

        sys.exit(0)

    def find_joints(self, node, joints_list):
        """Рекурсивно ищет все джоинты в модели"""
        # Проверяем тип узла
        node_type = node.node().getType().getName() if hasattr(node.node(), 'getType') else ""

        # Джоинты обычно имеют тип Character или ModelNode
        if "Joint" in node_type or "Character" in node_type:
            joints_list.append(node)

        # Также проверяем по имени (часто джоинты содержат определенные слова)
        name = node.getName().lower()
        joint_keywords = ["joint", "bone", "jnt", "skeleton", "armature"]
        if any(keyword in name for keyword in joint_keywords):
            if node not in joints_list:
                joints_list.append(node)

        # Рекурсивно проверяем детей
        for child in node.getChildren():
            self.find_joints(child, joints_list)

    def print_hierarchy(self, node, indent=0, max_depth=5):
        """Печатает иерархию узлов"""
        if indent > max_depth:
            return

        node_type = node.node().getType().getName() if hasattr(node.node(), 'getType') else "Unknown"
        print("  " * indent + f"└─ {node.getName()} ({node_type})")

        if indent < max_depth:
            for child in node.getChildren():
                self.print_hierarchy(child, indent + 1, max_depth)

if __name__ == "__main__":
    app = ModelInspector()
