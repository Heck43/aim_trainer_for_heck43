from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, CardMaker, TransparencyAttrib
from direct.showbase.ShowBaseGlobal import globalClock, aspect2d

class KillfeedManager:
    def __init__(self, game):
        self.game = game
        self.messages = []

        self.fade_time = 0.3
        self.slide_distance = 0.4
        self.display_duration = 5.0
        self.max_messages = 5

    def create_message(self, target_name="Target"):
        hud_scale = self.game.get_hud_ui_scale()
        y_pos = 0.9 - len(self.messages) * 0.06
        x_pos = 1.3 + self.slide_distance

        message = OnscreenText(
            text=f"You killed {target_name}",
            fg=(0.3, 0.6, 1, 0),
            shadow=(0, 0, 0, 0),
            pos=(x_pos, y_pos),
            align=TextNode.ARight,
            scale=0.04 * hud_scale
        )
        message.setBin('gui-popup', 0)

        frame_root = aspect2d.attachNewNode("frame_root")
        frame_root.setPos(x_pos, 0, y_pos)
        frame_root.setScale(hud_scale)

        cm = CardMaker('killfeed_bg')
        cm.setFrame(-0.5, 0.05, -0.015, 0.025)
        bg = frame_root.attachNewNode(cm.generate())
        bg.setTransparency(TransparencyAttrib.MAlpha)
        bg.setColor(0, 0, 0, 0)
        bg.setBin('background', 10)

        border_thickness = 0.002
        borders = []

        cm_top = CardMaker('border_top')
        cm_top.setFrame(-0.5, 0.05, 0.025, 0.025 + border_thickness)
        border_top = frame_root.attachNewNode(cm_top.generate())
        border_top.setColor(1, 1, 1, 0)
        border_top.setTransparency(TransparencyAttrib.MAlpha)
        border_top.setBin('background', 11)
        borders.append(border_top)

        cm_bottom = CardMaker('border_bottom')
        cm_bottom.setFrame(-0.5, 0.05, -0.015 - border_thickness, -0.015)
        border_bottom = frame_root.attachNewNode(cm_bottom.generate())
        border_bottom.setColor(1, 1, 1, 0)
        border_bottom.setTransparency(TransparencyAttrib.MAlpha)
        border_bottom.setBin('background', 11)
        borders.append(border_bottom)

        cm_left = CardMaker('border_left')
        cm_left.setFrame(-0.5 - border_thickness, -0.5, -0.015, 0.025)
        border_left = frame_root.attachNewNode(cm_left.generate())
        border_left.setColor(1, 1, 1, 0)
        border_left.setTransparency(TransparencyAttrib.MAlpha)
        border_left.setBin('background', 11)
        borders.append(border_left)

        cm_right = CardMaker('border_right')
        cm_right.setFrame(0.05, 0.05 + border_thickness, -0.015, 0.025)
        border_right = frame_root.attachNewNode(cm_right.generate())
        border_right.setColor(1, 1, 1, 0)
        border_right.setTransparency(TransparencyAttrib.MAlpha)
        border_right.setBin('background', 11)
        borders.append(border_right)

        self.messages.append({
            'message': message,
            'frame_root': frame_root,
            'background': bg,
            'borders': borders,
            'creation_time': globalClock.getFrameTime(),
            'y_pos': y_pos,
            'x_pos': x_pos,
            'alpha': 0,
            'target_alpha': 1,
            'x_offset': self.slide_distance
        })

        if len(self.messages) > self.max_messages:
            oldest = self.messages[0]
            oldest['target_alpha'] = 0

    def update_positions(self):
        current_time = globalClock.getFrameTime()
        messages_to_remove = []

        for i, msg_data in enumerate(self.messages):
            age = current_time - msg_data['creation_time']

            if msg_data['alpha'] != msg_data['target_alpha']:
                alpha_change = globalClock.getDt() / self.fade_time
                if msg_data['target_alpha'] > msg_data['alpha']:
                    msg_data['alpha'] = min(msg_data['target_alpha'], msg_data['alpha'] + alpha_change)
                else:
                    msg_data['alpha'] = max(msg_data['target_alpha'], msg_data['alpha'] - alpha_change)

                msg_data['message'].setFg((0.3, 0.6, 1, msg_data['alpha']))
                msg_data['message'].setShadow((0, 0, 0, msg_data['alpha']))
                msg_data['background'].setColor(0, 0, 0, msg_data['alpha'] * 0.3)
                for border in msg_data['borders']:
                    border.setColor(1, 1, 1, msg_data['alpha'] * 0.8)

            if msg_data['x_offset'] > 0:
                slide_speed = self.slide_distance / self.fade_time
                msg_data['x_offset'] = max(0, msg_data['x_offset'] - slide_speed * globalClock.getDt())
                new_x = 1.3 + msg_data['x_offset']

                msg_data['message'].setPos(new_x, msg_data['y_pos'])
                msg_data['frame_root'].setPos(new_x, 0, msg_data['y_pos'])
                msg_data['x_pos'] = new_x

            if age > self.display_duration and msg_data['target_alpha'] == 1:
                msg_data['target_alpha'] = 0

            if msg_data['alpha'] <= 0 and msg_data['target_alpha'] == 0:
                messages_to_remove.append(msg_data)

            target_y = 0.9 - i * 0.06
            if msg_data['y_pos'] != target_y:
                msg_data['y_pos'] = target_y
                msg_data['message'].setPos(msg_data['x_pos'], target_y)
                msg_data['frame_root'].setPos(msg_data['x_pos'], 0, target_y)

        for msg_data in messages_to_remove:
            msg_data['message'].removeNode()
            msg_data['frame_root'].removeNode()
            self.messages.remove(msg_data)
