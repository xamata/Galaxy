from kivy.uix.relativelayout import RelativeLayout

# when there's no keyboard, turn keyboard off, like in mobile applications
def keyboard_closed(self):
    self._keyboard.unbind(on_key_down=self.on_keyboard_down)
    self._keyboard.unbind(on_key_up=self.on_keyboard_up)
    self._keyboard = None


# when keyboard buttons are pressed
def on_keyboard_down(self, keyboard, keycode, text, modifiers):
    if keycode[1] == "left":
        self.current_speed_x = self.SPEED_X
    elif keycode[1] == "right":
        self.current_speed_x = -self.SPEED_X
    return True


# when the keyboard is not being pressed
def on_keyboard_up(self, keyboard, keycode):
    self.current_speed_x = 0
    return True


def on_touch_down(self, touch):
    if not self.state_game_over and self.state_game_has_started:
        if touch.x < self.width / 2:
            # better to have a var and not a const
            # BAD: self.current_speed_x += 10
            # GOOD:
            self.current_speed_x += self.SPEED_X
            print("<-")
        else:
            self.current_speed_x -= self.SPEED_X
            print("->")
    # without super, touch would override all other buttons being pressed and not allow them to work
    # MainWidget is wrong bc we call user_actions.py from main.py. It would be a collision of interest/
    # so we used RelativeLayout instead, creating another layer
    return super(RelativeLayout, self).on_touch_down(touch)


def on_touch_up(self, touch):
    self.current_speed_x = 0
    print("UP")
    # return super().on_touch_up(touch)
