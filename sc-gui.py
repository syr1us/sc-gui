#!/usr/bin/env python
# -*- coding: utf8 -*-
import usb1
import Tkinter
import tkFont
import functools
import os
import sys
import threading
import datetime

from steamcontroller import SteamController, SCButtons
from steamcontroller.events import EventMapper, Pos
from steamcontroller.uinput import Keys

from steamcontroller.daemon import Daemon

KEYS_MAPPING =  {
        u'1': Keys.KEY_1,
        u'2': Keys.KEY_2,
        u'3': Keys.KEY_3,
        u'4': Keys.KEY_4,
        u'5': Keys.KEY_5,
        u'6': Keys.KEY_6,
        u'7': Keys.KEY_7,
        u'8': Keys.KEY_8,
        u'9': Keys.KEY_9,
        u'0': Keys.KEY_0,
        u'ß': Keys.KEY_MINUS,
        u'<': Keys.KEY_EQUAL,
        u'q': Keys.KEY_Q,
        u'w': Keys.KEY_W,
        u'e': Keys.KEY_E,
        u'r': Keys.KEY_R,
        u't': Keys.KEY_T,
        u'z': Keys.KEY_Y,
        u'u': Keys.KEY_U,
        u'i': Keys.KEY_I,
        u'o': Keys.KEY_O,
        u'p': Keys.KEY_P,
        u'ü': Keys.KEY_LEFTBRACE,
        u'+': Keys.KEY_RIGHTBRACE,
        u'a': Keys.KEY_A,
        u's': Keys.KEY_S,
        u'd': Keys.KEY_D,
        u'f': Keys.KEY_F,
        u'g': Keys.KEY_G,
        u'h': Keys.KEY_H,
        u'j': Keys.KEY_J,
        u'k': Keys.KEY_K,
        u'l': Keys.KEY_L,
        u'ö': Keys.KEY_SEMICOLON,
        u'ä': Keys.KEY_APOSTROPHE,
        u'#': Keys.KEY_BACKSLASH,
        u'<': Keys.KEY_102ND,
        u'y': Keys.KEY_Z,
        u'x': Keys.KEY_X,
        u'c': Keys.KEY_C,
        u'v': Keys.KEY_V,
        u'b': Keys.KEY_B,
        u'n': Keys.KEY_N,
        u'm': Keys.KEY_M,
        u',': Keys.KEY_COMMA,
        u'.': Keys.KEY_DOT,
        u'-': Keys.KEY_SLASH,
        u' ': Keys.KEY_SPACE,
    }


KEYS = [
    u'1234567890ß<', u'qwertzuiopü+', u'asdfghjklöä#', u'yxcvbnm,.-',
]


class Recources(object):
    def __init__(self):
        self._base_bath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'res',
        )
        self.left_hand = Tkinter.PhotoImage(
            file=os.path.join(self._base_bath, 'left_hand.gif')
        )
        self.right_hand = Tkinter.PhotoImage(
            file=os.path.join(self._base_bath, 'right_hand.gif')
        )
        self.key_small = Tkinter.PhotoImage(
            file=os.path.join(self._base_bath, 'key_small.gif')
        )


class EventQueue(object):
    def __init__(self):
        self._lock = threading.Lock()
        self.events = []

    def enqueue(self, event, data={}):
        self._lock.acquire()
        self.events.append([event, data])
        self._lock.release()

    def dequeue(self):
        self._lock.acquire()
        if not self.events:
            self._lock.release()
            return None
        event = self.events[0]
        del self.events[0]
        self._lock.release()
        return event


class GuiEventMapper(EventMapper):
    def __init__(self, events):
        super(GuiEventMapper, self).__init__()
        self.visible = False
        self.events = events
        self.setButtonCallback(SCButtons.STEAM, self.button_pressed_callback)
        self.set_classic_buttons()


    def unset_button_map(self, button):
        if button in self._btn_map.keys():
            del self._btn_map[button]

    def unset_trigger_map(self, pos):
        self._trig_evts[pos] = (None, 0)

    @staticmethod
    def tigger_pressed(self, button, pressed):
        pressed_offset = 0 if pressed else 2
        pad_index = 1 if button == SCButtons.RT else 2
        self.events.enqueue(
            "<<SteamTrigger>>",
            {'serial': pad_index + pressed_offset},
        )

    @staticmethod
    def pad_move(self, pad, x, y):
        pad = 1 if pad == Pos.RIGHT else 2
        self.events.enqueue(
            "<<SteamPadMove>>",
            {'serial': pad, 'rootx': x, 'rooty': y},
        )

    @staticmethod
    def insert_whitespace(self, button, pressed):
        if pressed:
            self.events.enqueue('<<whitespace>>')

    @staticmethod
    def remove_char(self, button, pressed):
        if pressed:
            self.events.enqueue('<<backspace>>')

    @staticmethod
    def button_pressed_callback(self, button, pressed):
        if not pressed:
            if self.visible:
                self.set_classic_buttons()
                self.visible = False
                self.events.enqueue('<<GuiHide>>')
            else:
                self.set_overlay_buttons()
                self.visible = True
                self.events.enqueue('<<GuiShow>>')


    def set_classic_buttons(self):
        self.setPadMouse(Pos.RIGHT)
        self.setPadScroll(Pos.LEFT)
        self.setStickButtons(
            [Keys.KEY_UP, Keys.KEY_LEFT, Keys.KEY_DOWN, Keys.KEY_RIGHT]
        )
        self.setTrigButton(Pos.LEFT, Keys.BTN_RIGHT)
        self.setTrigButton(Pos.RIGHT, Keys.BTN_LEFT)
        self.setButtonAction(SCButtons.LB, Keys.KEY_VOLUMEDOWN)
        self.setButtonAction(SCButtons.RB, Keys.KEY_VOLUMEUP)
        self.setButtonAction(SCButtons.A, Keys.KEY_ENTER)
        self.setButtonAction(SCButtons.B, Keys.KEY_BACKSPACE)
        self.setButtonAction(SCButtons.X, Keys.KEY_ESC)
        self.setButtonAction(SCButtons.Y, Keys.KEY_PLAYPAUSE)

        self.setButtonAction(SCButtons.START, Keys.KEY_NEXTSONG)
        self.setButtonAction(SCButtons.BACK, Keys.KEY_PREVIOUSSONG)
        self.setButtonAction(SCButtons.LGRIP, Keys.KEY_BACK)
        self.setButtonAction(SCButtons.RGRIP, Keys.KEY_FORWARD)
        self.setButtonAction(SCButtons.LPAD, Keys.BTN_MIDDLE)
        self.setButtonAction(SCButtons.RPAD, Keys.KEY_SPACE)


    def set_overlay_buttons(self):
        self.setPadButtonCallback(Pos.RIGHT, self.pad_move)
        self.setPadButtonCallback(Pos.LEFT, self.pad_move)
        self.setButtonCallback(SCButtons.LT, self.tigger_pressed)
        self.setButtonCallback(SCButtons.RT, self.tigger_pressed)
        self.setButtonCallback(SCButtons.B, self.insert_whitespace)
        self.setButtonCallback(SCButtons.A, self.remove_char)
        self.unset_trigger_map(Pos.LEFT)
        self.unset_trigger_map(Pos.RIGHT)
        self.unset_button_map(SCButtons.LB)
        self.unset_button_map(SCButtons.RB)
        self.unset_button_map(SCButtons.X)
        self.unset_button_map(SCButtons.Y)
        self.unset_button_map(SCButtons.START)
        self.unset_button_map(SCButtons.BACK)
        self.unset_button_map(SCButtons.LGRIP)
        self.unset_button_map(SCButtons.RGRIP)
        self.unset_button_map(SCButtons.LPAD)
        self.unset_button_map(SCButtons.RPAD)

class TkSteamController(SteamController):
        WIDTH = 800
        HEIGHT = 300
        SCALE = 0.01

        def __init__(self, evm, events, **kwargs):
            self.evm = evm
            self.tk = Tkinter.Tk()
            self.tk.overrideredirect(1)
            self.tk.configure(background = 'CadetBlue2')
            self.res = Recources()
            self.quit = False
            self.events = events
            self.visible = False
            super(TkSteamController, self).__init__(**kwargs)
            self.build_keyboard()
            self.last_left = [datetime.datetime.now(), None, None]
            self.last_right = [datetime.datetime.now(), None, None]

        def _callbackTimer(self, *args, **kwargs):
            if not self.quit:
                super(TkSteamController, self)._callbackTimer(*args, **kwargs)

        def __del__(self):
            if self._handle:
                self._handle.close()
            self.quit = True
            self.tk.quit()

        def handle_tk_events(self):
            event = self.events.dequeue()
            while event is not None:
                self.tk.event_generate(event[0], **event[1])
                event = self.events.dequeue()


        def run(self):
            """Fucntion to run in order to process usb events"""
            if self._handle:
                cnt=0
                try:
                    while any(x.isSubmitted() for x in self._transfer_list) and not self.quit:
                        cnt+=1
                        self._ctx.handleEvents()
                        self.handle_tk_events()
                        self.tk.update_idletasks()
                        self.tk.update()
                        if len(self._cmsg) > 0:
                            cmsg = self._cmsg.pop()
                            self._sendControl(cmsg)

                except KeyboardInterrupt:
                    del self
                    sys.exit()

                except usb1.USBErrorInterrupted:
                    pass

        def generate_output(self, press=True):
            if press:
                self.__press_output_key(self.tk.winfo_children()[0].get())

        def __press_output_key(self, chars):
            if chars:
                keyboard = self.evm._uip[1]
                char = chars[0]
                keyboard.pressEvent([KEYS_MAPPING[char]])
                keyboard.releaseEvent([KEYS_MAPPING[char]])
                if len(chars) > 1:
                    chars = chars[1:]
                    self.tk.after(10, self.__press_output_key, chars)

        def create_button(self, x, y, text):
            self.canvas.create_image(x, y, image=self.res.key_small, tags=('button', text))
            self.canvas.create_text(x, y-10, text=text)

        def build_keyboard(self):
            font = tkFont.Font(family='Helvetica', size=24, weight='bold')
            self.output = Tkinter.Entry(self.tk, width=50, font=font, bg="AntiqueWhite3")
            self.output.pack()
            self.canvas = Tkinter.Canvas(
                self.tk,
                bg="AntiqueWhite3",
                width=self.WIDTH - 80,
                height=self.HEIGHT - 30
            )
            self.canvas.pack()
            for row_nr, row in enumerate(KEYS):
                for key_nr, key in enumerate(row):
                    self.create_button(
                        32 + key_nr * 60,
                        32 + row_nr * 60,
                        text = key
                    )
            self.left_hand = self.canvas.create_image(
                (self.WIDTH - 80) / 2 - 50,
                (self.HEIGHT - 30) / 2,
                image=self.res.left_hand,
                tags='left_hand'
            )
            self.right_hand = self.canvas.create_image(
                (self.WIDTH - 80) / 2 + 50,
                (self.HEIGHT - 30) / 2,
                image=self.res.right_hand,
                tags='right_hand'
            )
            self.tk.withdraw()
            self.tk.bind('<<SteamTrigger>>', self.triggerPressed)
            self.tk.bind('<<GuiHide>>', self.guiHide)
            self.tk.bind('<<GuiShow>>', self.guiShow)
            self.tk.bind('<<SteamPadMove>>', self.padMove)
            self.tk.bind('<<whitespace>>', self.whitespace)
            self.tk.bind('<<backspace>>', self.backspace)

        def triggerPressed(self, evt):
            pressed = evt.serial > 2
            if not pressed:
                return
            if evt.serial % 2:
                # RIGHT Trigger Pressed
                x, y = self.canvas.coords(self.right_hand)
                x = x - 5
            else:
                x, y = self.canvas.coords(self.left_hand)
                x = x + 18
            items = self.canvas.find_overlapping(x, y, x, y)
            for item in items:
                tags = self.canvas.gettags(item)
                if 'button' in tags:
                    self.output.insert('end', tags[1])
                    break

        def guiHide(self, evt):
            self.tk.withdraw()
            self.generate_output()

        def guiShow(self, evt):
            self.tk.winfo_children()[0].delete(0, 'end')
            self.tk.update()
            self.tk.deiconify()

        def padMove(self, evt):
            timestamp = datetime.datetime.now()
            if evt.serial == 1:
                # RIGHT pad
                last = self.last_right
                hand = self.right_hand
            else:
                last = self.last_left
                hand = self.left_hand
            to_late = (timestamp - last[0] > datetime.timedelta(seconds=0.1))
            if to_late or not last[1] or not last[2]:
                last[0] = timestamp
                last[1] = evt.x_root
                last[2] = evt.y_root
                return
            delta_x = self.canvas.canvasx(evt.x_root - last[1]) * self.SCALE
            delta_y = self.canvas.canvasy(last[2] - evt.y_root) * self.SCALE
            last[0] = timestamp
            last[1] = evt.x_root
            last[2] = evt.y_root
            max_x = int(self.canvas.config()['width'][4])
            max_y = int(self.canvas.config()['height'][4])
            old_x, old_y = self.canvas.coords(hand)
            x = max(min(old_x + delta_x, max_x), 0)
            y = max(min(old_y + delta_y, max_y), 0)
            self.canvas.coords(hand, x, y)


        def whitespace(self, evt):
            self.tk.winfo_children()[0].insert('end', ' ')

        def backspace(self, evt):
            output = self.tk.winfo_children()[0]
            output.delete(len(output.get())-1, 'end')



class SCDaemon(Daemon):
    def run(self):
        events = EventQueue()
        evm = GuiEventMapper(events)
        sc = TkSteamController(evm, events, callback=evm.process)
        sc.run()


if __name__ == '__main__':
    import argparse

    def _main():
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('command', type=str, choices=['start', 'stop', 'restart', 'debug'])
        args = parser.parse_args()
        daemon = SCDaemon('/tmp/steamcontroller.pid')

        if 'start' == args.command:
            daemon.start()
        elif 'stop' == args.command:
            daemon.stop()
        elif 'restart' == args.command:
            daemon.restart()
        elif 'debug' == args.command:
            events = EventQueue()
            evm = GuiEventMapper(events)
            sc = TkSteamController(evm, events, callback=evm.process)
            sc.run()
    _main()
