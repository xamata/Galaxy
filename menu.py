from kivy.uix.relativelayout import RelativeLayout


class MenuWidget(RelativeLayout):
    # turns off menu when game is active
    def on_touch_down(self, touch):
        if self.opacity == 0:
            return False
        return super(RelativeLayout, self).on_touch_down(touch)
