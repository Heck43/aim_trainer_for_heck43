# managers/effects_manager.py
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import *
import random

class EffectsManager:
    """Manages visual effects: damage text, bullet traces, killfeed"""

    def __init__(self, game):
        self.game = game
        self.damage_texts = []
        self.killfeed_messages = []
        self.shot_effects = []

        # Killfeed settings
        self.killfeed_fade_time = 0.3
        self.killfeed_slide_distance = 0.2
        self.killfeed_duration = 5

        # Bullet traces node
        self.bullet_traces = self.game.render.attachNewNode("bullet_traces")

    def spawn_damage_text(self, text, pos=None):
        """Creates floating damage text"""
        damage_text = TextNode('damage')
        damage_text.setText(str(text))
        damage_text.setAlign(TextNode.ACenter)

        text_node_path = self.game.aspect2d.attachNewNode(damage_text)

        offset_x = random.uniform(-0.15, 0.15)
        offset_y = random.uniform(-0.15, 0.15)

        if pos is None:
            pos = Point3(offset_x, 0, offset_y)
        else:
            text_node_path.setPos(pos.x + offset_x, 0, pos.y + offset_y)

        # Scale based on UI scale
        hud_scale = self.game.get_hud_ui_scale() if hasattr(self.game, 'get_hud_ui_scale') else 1.0
        text_node_path.setScale(0.07 * hud_scale)

        # Color based on damage amount
        try:
            damage_value = int(text)
            if damage_value >= 100:
                text_node_path.setColor(1, 0, 0, 1)  # Red for headshot
            elif damage_value >= 60:
                text_node_path.setColor(1, 0.5, 0, 1)  # Orange for body
            else:
                text_node_path.setColor(1, 1, 1, 1)  # White for limbs
        except:
            text_node_path.setColor(1, 1, 0, 1)  # Yellow for other

        # Fade out animation
        fade_interval = LerpColorScaleInterval(
            text_node_path,
            0.5,
            Vec4(1, 1, 1, 0),
            Vec4(1, 1, 1, 1)
        )

        # Move up animation
        move_interval = LerpPosInterval(
            text_node_path,
            1.0,
            text_node_path.getPos() + Vec3(0, 0, 0.5)
        )

        # Combine and start
        Sequence(
            Parallel(fade_interval, move_interval),
            Func(text_node_path.removeNode)
        ).start()

        # Track for cleanup
        current_time = globalClock.getFrameTime()
        self.damage_texts.append((text_node_path, current_time, text_node_path.getPos()))

    def create_bullet_trace(self, start_pos, end_pos):
        """Creates bullet trace line from start to end"""
        if not self.game.settings.get('bullet_traces', True):
            return

        ls = LineSegs()
        ls.setColor(1.0, 1.0, 0.8, 0.5)  # Yellowish white
        ls.setThickness(2.0)
        ls.moveTo(start_pos)

        if end_pos is not None:
            ls.drawTo(end_pos)

        trace = self.bullet_traces.attachNewNode(ls.create())
        trace.setTransparency(TransparencyAttrib.MAlpha)

        # Fade out and remove
        Sequence(
            Wait(0.1),
            LerpColorScaleInterval(trace, 0.2, Vec4(1, 1, 1, 0)),
            Func(trace.removeNode)
        ).start()

    def create_killfeed_message(self, target_name="Target"):
        """Creates killfeed message on right side"""
        if not self.game.settings.get('killfeed', True):
            return

        hud_scale = self.game.get_hud_ui_scale() if hasattr(self.game, 'get_hud_ui_scale') else 1.0
        y_pos = 0.9 - len(self.killfeed_messages) * 0.06
        x_pos = 1.3 + self.killfeed_slide_distance

        message = OnscreenText(
            text=f"You killed {target_name}",
            fg=(0.3, 0.6, 1, 0),
            shadow=(0, 0, 0, 0),
            pos=(x_pos, y_pos),
            align=TextNode.ARight,
            scale=0.04 * hud_scale
        )
        message.setBin('gui-popup', 0)

        # Background frame
        frame_root = aspect2d.attachNewNode("frame_root")
        frame_root.setPos(x_pos, 0, y_pos)
        frame_root.setScale(hud_scale)

        cm = CardMaker('killfeed_bg')
        cm.setFrame(-0.5, 0.05, -0.015, 0.025)
        bg = frame_root.attachNewNode(cm.generate())
        bg.setTransparency(TransparencyAttrib.MAlpha)
        bg.setColor(0, 0, 0, 0)
        bg.setBin('background', 10)

        # Borders
        borders = []
        border_positions = [
            (-0.5, -0.015, 0.5, -0.015),  # Top
            (-0.5, 0.025, 0.5, 0.025),    # Bottom
            (-0.5, -0.015, -0.5, 0.025),  # Left
            (0.05, -0.015, 0.05, 0.025)   # Right
        ]

        for x1, y1, x2, y2 in border_positions:
            ls = LineSegs()
            ls.setColor(1, 1, 1, 0)
            ls.setThickness(1)
            ls.moveTo(x1, 0, y1)
            ls.drawTo(x2, 0, y2)
            border = frame_root.attachNewNode(ls.create())
            border.setTransparency(TransparencyAttrib.MAlpha)
            borders.append(border)

        # Store message data
        self.killfeed_messages.append({
            'message': message,
            'frame_root': frame_root,
            'background': bg,
            'borders': borders,
            'creation_time': globalClock.getFrameTime(),
            'y_pos': y_pos,
            'x_pos': x_pos,
            'alpha': 0,
            'target_alpha': 1,
            'x_offset': self.killfeed_slide_distance
        })

        # Remove oldest if too many
        if len(self.killfeed_messages) > 5:
            oldest = self.killfeed_messages[0]
            oldest['target_alpha'] = 0

    def update_killfeed_positions(self):
        """Updates killfeed message positions and fading"""
        current_time = globalClock.getFrameTime()
        messages_to_remove = []

        for i, msg_data in enumerate(self.killfeed_messages):
            age = current_time - msg_data['creation_time']

            # Fade in/out
            if msg_data['alpha'] != msg_data['target_alpha']:
                alpha_change = globalClock.getDt() / self.killfeed_fade_time
                if msg_data['target_alpha'] > msg_data['alpha']:
                    msg_data['alpha'] = min(msg_data['target_alpha'], msg_data['alpha'] + alpha_change)
                else:
                    msg_data['alpha'] = max(msg_data['target_alpha'], msg_data['alpha'] - alpha_change)

                msg_data['message'].setFg((0.3, 0.6, 1, msg_data['alpha']))
                msg_data['message'].setShadow((0, 0, 0, msg_data['alpha']))
                msg_data['background'].setColor(0, 0, 0, msg_data['alpha'] * 0.3)
                for border in msg_data['borders']:
                    border.setColor(1, 1, 1, msg_data['alpha'] * 0.8)

            # Slide in from right
            if msg_data['x_offset'] > 0:
                slide_speed = self.killfeed_slide_distance / self.killfeed_fade_time
                msg_data['x_offset'] = max(0, msg_data['x_offset'] - slide_speed * globalClock.getDt())
                new_x = 1.3 + msg_data['x_offset']

                msg_data['message'].setPos(new_x, msg_data['y_pos'])
                msg_data['frame_root'].setPos(new_x, 0, msg_data['y_pos'])

            # Mark for removal if faded out
            if msg_data['target_alpha'] == 0 and msg_data['alpha'] <= 0.01:
                messages_to_remove.append(msg_data)
            # Auto-fade after duration
            elif age > self.killfeed_duration and msg_data['target_alpha'] == 1:
                msg_data['target_alpha'] = 0

        # Remove old messages
        for msg_data in messages_to_remove:
            msg_data['message'].removeNode()
            msg_data['frame_root'].removeNode()
            self.killfeed_messages.remove(msg_data)

    def update(self, dt):
        """Update effects (called every frame)"""
        self.update_killfeed_positions()

        # Clean up old damage texts
        current_time = globalClock.getFrameTime()
        self.damage_texts = [
            (text_node, start_time, start_pos)
            for text_node, start_time, start_pos in self.damage_texts
            if current_time - start_time < 1.5
        ]

    def cleanup(self):
        """Clean up all effects"""
        for text_node, _, _ in self.damage_texts:
            if text_node:
                text_node.removeNode()
        self.damage_texts.clear()

        for msg_data in self.killfeed_messages:
            msg_data['message'].removeNode()
            msg_data['frame_root'].removeNode()
        self.killfeed_messages.clear()
