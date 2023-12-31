from smg.evolutionary import Optimizer, Optimizer2
from smg.utils import partFromProgression, Sequencer, MidiRouter, MidiInputThread
import numpy as np
import multiprocessing
from collections import defaultdict

def show(p):
    for c in p[0].chords:
        print(c.pitches)

def note2note_array(notes):
    fields = [
    ("onset_sec", "f4"),
    ("duration_sec", "f4"),
    ("pitch", "i4"),
    ("velocity", "i4"),
    ]
    notes_list = list()
    sounding_notes = {}
    for note in notes:
        msg = note[0]
        time = note[1]
        note_on = msg.type == "note_on"
        note_off = msg.type == "note_off"
        if note_on or note_off:
            note = msg.note
            if note_on and msg.velocity > 0:

                # save the onset time and velocity
                sounding_notes[note] = time
            elif note_off or msg.velocity == 0:
                if note not in sounding_notes:
                    continue
                else:
                    onset = sounding_notes[note]
                    duration = time - onset
                    notes_list.append((onset, duration, note, msg.velocity))
                    del sounding_notes[note]
    
    notes_array = np.array(notes_list, dtype=fields)
    return notes_array
                
def rec(l):
    notes = l.run()
    na = note2note_array(notes)
    return na

    


def recompute(note_array = None, e = 10):
    if note_array is None:
        fields = [
            ("onset_sec", "f4"),
            ("duration_sec", "f4"),
            ("pitch", "i4"),
            ("velocity", "i4"),
            ]
        rows = [
            (0.933,1.712,48,100),
            (7.176,1.885,51,100),
            (2.685,1.777,53,100),
            (4.464,2.71,59,100),
        ]
        note_array = np.array(rows, dtype=fields)
    exp = Optimizer2()
    p, r = exp.run(melody=note_array, epochs = e)
    part = partFromProgression(p[0],quarter_duration = 4,rhythm = r)
    return part, r

def st(s = None, re = False):
    if s is None:
        queue = multiprocessing.Queue()
        s = Sequencer(queue=queue,outport_name="seq")
        s.start()
    else:
        s.terminate()
        s.join()
        if re:
            queue =multiprocessing.Queue()
            s = Sequencer(queue=queue,outport_name="seq")
            s.start()
    return s


if __name__ == "__main__":

    mr = MidiRouter(inport_name="inp")
    l = MidiInputThread(port = mr.input_port)
    s = st()

    # part, r = recompute(note_array)
    # note_array = rec(l)
    # s.up(part)


    # s.start()
    # s.terminate()
    # s.join()
