from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpColorScaleInterval, Wait, Func, LerpScaleInterval
from panda3d.core import TextNode, TransparencyAttrib, Vec4, NodePath, Vec3, WindowProperties
from direct.gui.DirectFrame import DirectFrame

class SplashScreen:
    def __init__(self, game):
        self.game = game
        
        # Set up window properties for splash screen
        props = WindowProperties()
        props.setCursorHidden(True)  # Hide cursor
        props.setMouseMode(WindowProperties.MRelative)  # Relative mouse mode
        game.win.requestProperties(props)
        
        # Center the mouse
        game.win.movePointer(0,
                          int(game.win.getProperties().getXSize() / 2),
                          int(game.win.getProperties().getYSize() / 2))
        
        # Add mouse watcher task
        self.mouse_task = game.taskMgr.add(self.mouse_task, 'splash_mouse_task')
        
        # Create a black background
        self.background = DirectFrame(
            frameColor=(0, 0, 0, 1),
            frameSize=(-2, 2, -2, 2),
            parent=game.render2d
        )
        
        # Author nickname first
        self.author_name = OnscreenText(
            text="heck43",
            pos=(0, -0.3),
            scale=0.1,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=False,
            parent=game.a2dBackground
        )
        self.author_name.setTransparency(TransparencyAttrib.MAlpha)
        self.author_name.setColorScale(1, 1, 1, 0)
        
        # Author logo
        self.author_logo = OnscreenImage(
            image="assets/author_logo.jpg",
            pos=(0, 0, 0.2),
            scale=0.3,
            parent=game.a2dBackground
        )
        self.author_logo.setTransparency(TransparencyAttrib.MAlpha)
        self.author_logo.setColorScale(1, 1, 1, 0)
        
        # Game title
        self.game_title = OnscreenText(
            text="Aim Trainer",
            pos=(0, 0.2),
            scale=0.15,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=False,
            parent=game.a2dBackground
        )
        self.game_title.setTransparency(TransparencyAttrib.MAlpha)
        self.game_title.setColorScale(1, 1, 1, 0)

        # Loading text
        self.loading_text = OnscreenText(
            text="Loading...",
            pos=(0, -0.3),
            scale=0.07,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=True,
            parent=game.a2dBackground
        )
        self.loading_text.setTransparency(TransparencyAttrib.MAlpha)
        self.loading_text.setColorScale(1, 1, 1, 0)

        # Status text
        self.status_text = OnscreenText(
            text="Initializing...",
            pos=(0, -0.5),
            scale=0.05,
            fg=(0.7, 0.7, 0.7, 1),
            align=TextNode.ACenter,
            mayChange=True,
            parent=game.a2dBackground
        )
        self.status_text.setTransparency(TransparencyAttrib.MAlpha)
        self.status_text.setColorScale(0.7, 0.7, 0.7, 0)
        
        # Loading bar background
        self.loading_bg = DirectFrame(
            frameColor=(0.2, 0.2, 0.2, 1),
            frameSize=(-0.5, 0.5, -0.02, 0.02),
            pos=(0, 0, -0.4),
            parent=game.a2dBackground
        )
        self.loading_bg.setTransparency(TransparencyAttrib.MAlpha)
        self.loading_bg.setColorScale(0.2, 0.2, 0.2, 0)
        
        # Loading bar fill
        self.loading_fill = DirectFrame(
            frameColor=(1, 1, 1, 1),
            frameSize=(0, 1, -0.015, 0.015),
            pos=(-0.5, 0, -0.4),
            parent=game.a2dBackground
        )
        self.loading_fill.setTransparency(TransparencyAttrib.MAlpha)
        self.loading_fill.setColorScale(1, 1, 1, 0)

        # Store all elements that need to be cleaned up
        self.elements = [
            self.background,
            self.author_logo,
            self.author_name,
            self.game_title,
            self.loading_bg,
            self.loading_fill,
            self.loading_text,
            self.status_text
        ]

    def start(self):
        # Animation sequence
        self.sequence = Sequence(
            # First fade in nickname
            LerpColorScaleInterval(self.author_name, 1.0, Vec4(1, 1, 1, 1), Vec4(1, 1, 1, 0)),
            Wait(0.5),
            
            # Then fade in author logo
            LerpColorScaleInterval(self.author_logo, 1.0, Vec4(1, 1, 1, 1), Vec4(1, 1, 1, 0)),
            Wait(1.5),
            
            # Fade out both author logo and name together
            Parallel(
                LerpColorScaleInterval(self.author_logo, 1.0, Vec4(1, 1, 1, 0), Vec4(1, 1, 1, 1)),
                LerpColorScaleInterval(self.author_name, 1.0, Vec4(1, 1, 1, 0), Vec4(1, 1, 1, 1))
            ),
            Wait(0.5),
            
            # Fade in game title and loading text
            Parallel(
                LerpColorScaleInterval(self.game_title, 1.5, Vec4(1, 1, 1, 1), Vec4(1, 1, 1, 0)),
                LerpColorScaleInterval(self.loading_text, 1.5, Vec4(1, 1, 1, 1), Vec4(1, 1, 1, 0))
            ),
            
            # Show loading bar and status text with animation
            Parallel(
                LerpColorScaleInterval(self.loading_bg, 0.5, Vec4(0.2, 0.2, 0.2, 1), Vec4(0.2, 0.2, 0.2, 0)),
                LerpColorScaleInterval(self.loading_fill, 0.5, Vec4(1, 1, 1, 1), Vec4(1, 1, 1, 0)),
                LerpColorScaleInterval(self.status_text, 0.5, Vec4(0.7, 0.7, 0.7, 1), Vec4(0.7, 0.7, 0.7, 0))
            ),
            
            # Animate loading bar and show status messages
            Parallel(
                LerpScaleInterval(self.loading_fill, 2.0, 
                                Vec3(1.0, 1.0, 1.0),
                                startScale=Vec3(0.01, 1.0, 1.0),
                                blendType='easeInOut'),
                Sequence(
                    Func(lambda: self.status_text.setText("Initializing game...")),
                    Wait(0.7),
                    Func(lambda: self.status_text.setText("Loading resources...")),
                    Wait(0.7),
                    Func(lambda: self.status_text.setText("Preparing menu...")),
                    Wait(0.6)
                )
            ),
            Wait(0.5),
            
            # Fade out everything
            Parallel(
                LerpColorScaleInterval(self.game_title, 1.0, Vec4(1, 1, 1, 0), Vec4(1, 1, 1, 1)),
                LerpColorScaleInterval(self.loading_text, 1.0, Vec4(1, 1, 1, 0), Vec4(1, 1, 1, 1)),
                LerpColorScaleInterval(self.loading_bg, 1.0, Vec4(0.2, 0.2, 0.2, 0), Vec4(0.2, 0.2, 0.2, 1)),
                LerpColorScaleInterval(self.loading_fill, 1.0, Vec4(1, 1, 1, 0), Vec4(1, 1, 1, 1)),
                LerpColorScaleInterval(self.status_text, 1.0, Vec4(0.7, 0.7, 0.7, 0), Vec4(0.7, 0.7, 0.7, 1))
            ),
            Func(self.cleanup),
            Func(self.show_main_menu)
        )
        self.sequence.start()

    def mouse_task(self, task):
        """Keep mouse centered during splash screen"""
        if self.game.is_splash_screen_active:
            mw = self.game.mouseWatcherNode
            if mw.hasMouse():
                # Reset mouse to center
                self.game.win.movePointer(0,
                                      int(self.game.win.getProperties().getXSize() / 2),
                                      int(self.game.win.getProperties().getYSize() / 2))
        return task.cont

    def cleanup(self):
        """Clean up splash screen resources"""
        if hasattr(self, 'mouse_task'):
            self.game.taskMgr.remove(self.mouse_task)
        for element in self.elements:
            element.removeNode()
        self.elements.clear()

    def show_main_menu(self):
        """Show the main menu after splash screen"""
        if hasattr(self, 'mouse_task'):
            self.game.taskMgr.remove(self.mouse_task)
            
        if hasattr(self.game, 'show_main_menu'):
            self.game.is_splash_screen_active = False
            
            # Reset window properties for main menu
            props = WindowProperties()
            props.setCursorHidden(False)
            props.setMouseMode(WindowProperties.MAbsolute)
            self.game.win.requestProperties(props)
            
            self.game.show_main_menu()
            self.game.splash = None
