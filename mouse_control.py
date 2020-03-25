from pynput.mouse import Button, Controller


class mouse_control:
    mousec = Controller()

    def _init_(self):
        mousec = Controller()
        (cord_x, cord_y) = mousec.position

    def move_mouse(self, x, y):
        self.mousec.move(x, y)

    def gesture(self, kind):
        if kind == 'right_click':
            self.mousec.click(Button.right, 1)
        elif kind == 'left_click':
            self.mousec.click(Button.left, 1)
        else:
            print('unknown command')

    def control_mouse(self, kind, x, y):
        if kind == 'move':
            self.move_mouse(x, y)
        else:
            print()
            self.gesture(kind)