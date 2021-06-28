from collections import defaultdict
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController
import mido

mouse = MouseController()
keyboard = KeyboardController()

pressed = defaultdict(lambda: False)


def chord(root: int, is_major=True):
    return [root, root + (4 if is_major else 3), root + 7]


def octave(root: int):
    return [root, root + 12]


CHORDS = {
    'Q': chord(60),                     # C4 major
    'W': chord(62, is_major=False),     # D4 minor
    'E': chord(64, is_major=False),     # E4 minor
    'R': chord(65),                     # F4 major
    'D': octave(21),                    # A0 + A1
    'F': octave(24),                    # C1 + C2
    'ctrlQ': octave(60),                # C4 + C5
    'ctrlW': octave(62),                # D4 + D5
    'ctrlE': octave(64),                # E4 + E5
    'ctrlR': octave(65),                # F4 + F5
}


def pressed_notes(notes):
    return all(pressed[note] for note in notes)


def clear_notes(notes):
    [pressed.__setitem__(note, False) for note in notes]


def handle_actions(note, disable_output=False):
    # Check for chords
    if pressed_notes(CHORDS['Q']):
        # C4 maj
        print('Q')
        if not disable_output:
            keyboard.tap('q')
        return clear_notes(CHORDS['Q'])
    if pressed_notes(CHORDS['W']):
        # D4 min
        print('W')
        if not disable_output:
            keyboard.tap('w')
        return clear_notes(CHORDS['W'])
    if pressed_notes(CHORDS['E']):
        # E4 min
        print('E')
        if not disable_output:
            keyboard.tap('e')
        return clear_notes(CHORDS['E'])
    if pressed_notes(CHORDS['R']):
        # F4 maj
        print('R')
        if not disable_output:
            keyboard.tap('r')
        return clear_notes(CHORDS['R'])
    if pressed_notes(CHORDS['D']):
        # Octave D1
        print('D')
        if not disable_output:
            keyboard.tap('d')
        return clear_notes(CHORDS['D'])
    if pressed_notes(CHORDS['F']):
        # Octave F1
        print('F')
        if not disable_output:
            keyboard.tap('f')
        return clear_notes(CHORDS['F'])
    if pressed_notes(CHORDS['ctrlQ']):
        # Octave C4
        print('Level Q')
        if not disable_output:
            keyboard.press(Key.ctrl)
            keyboard.tap('q')
            keyboard.release(Key.ctrl)
        return clear_notes(CHORDS['ctrlQ'])
    if pressed_notes(CHORDS['ctrlW']):
        # Octave C4
        print('Level W')
        if not disable_output:
            keyboard.press(Key.ctrl)
            keyboard.tap('w')
            keyboard.release(Key.ctrl)
        return clear_notes(CHORDS['ctrlW'])
    if pressed_notes(CHORDS['ctrlE']):
        # Octave C4
        print('Level E')
        if not disable_output:
            keyboard.press(Key.ctrl)
            keyboard.tap('e')
            keyboard.release(Key.ctrl)
        return clear_notes(CHORDS['ctrlE'])
    if pressed_notes(CHORDS['ctrlR']):
        # Octave C4
        print('Level R')
        if not disable_output:
            keyboard.press(Key.ctrl)
            keyboard.tap('r')
            keyboard.release(Key.ctrl)
        return clear_notes(CHORDS['ctrlR'])

    # Attack move
    if 88 <= note <= 95:  # E6-B6
        print(f'{note} A')
        if not disable_output:
            keyboard.tap('A')
        return

    # Right click
    if note not in (26, 38, 29, 41, 53) and (21 <= note <= 59 or 79 <= note <= 86):  # A0-B3, G5-D6, not D1/D2/F1/F2/F3
        print(f'{note} right-click')
        if not disable_output:
            mouse.click(Button.right)
        return

    # Item slots
    if note == 96:
        print(f'{note} Item 1')
        if not disable_output:
            keyboard.tap('1')
        return
    if note == 98:
        print(f'{note} Item 2')
        if not disable_output:
            keyboard.tap('2')
        return
    if note == 100:
        print(f'{note} Item 3')
        if not disable_output:
            keyboard.tap('3')
        return
    if note == 101:
        print(f'{note} Item 4')
        if not disable_output:
            keyboard.tap('4')
        return
    if note == 103:
        print(f'{note} Item 5')
        if not disable_output:
            keyboard.tap('5')
        return
    if note == 105:
        print(f'{note} Item 6')
        if not disable_output:
            keyboard.tap('6')
        return
    if note == 107:
        print(f'{note} Item 7')
        if not disable_output:
            keyboard.tap('7')
        return


def main(input_device, disable_output=False):
    with mido.open_input(input_device) as device:
        print(f'Opened {input_device} successfully.')
        print('Listening for notes... Press Ctrl+C to stop.')

        for msg in device:
            if msg.type not in ('note_on', 'note_off'):
                # Skip any non-note messages.
                # print(f'Skipping {msg}')
                continue
            # print(f'{msg.note} {msg.type}')
            pressed[msg.note] = True if msg.type == 'note_on' else False

            if msg.type == 'note_on':
                handle_actions(msg.note, disable_output)


if __name__ == '__main__':
    devices = mido.get_input_names()
    # print('Which MIDI input should be used? (1)')
    # for i, name in enumerate(devices, 1):
    #     print(f"{i}) {name}")
    # while True:
    #     try:
    #         a = input('> ')
    #         if not a:
    #             a = '1'
    #         choice = devices[int(a) - 1]
    #         break
    #     except:
    #         print('Invalid choice!')
    # disable_output = input('Enable output? y/[n]').lower() != 'y'
    main(devices[0], True)