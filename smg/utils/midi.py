import partitura as pt  
import mido
import numpy as np
import time
import threading
import multiprocessing
from collections import defaultdict
import partitura as pt
import winsound

class MidiInputThread(threading.Thread):
    def __init__(
        self,
        port,
        queue = list(),
        init_time=None,
    ):
        threading.Thread.__init__(self)
        self.midi_in = port
        self.init_time = init_time
        self.duration = 10
        self.listen = False
        self.queue = queue
        self.beep_interval = self.duration / 8

    def run(self):
        self.start_listening()
        self.queue = list()
        print(self.current_time)
        for msg in self.midi_in.iter_pending():
            continue
        c_time = self.current_time
        while c_time < 2.49:
            if self.beep_interval is not None:
                if c_time % self.beep_interval < 0.01 and c_time < 2.0:
                    winsound.Beep(1000, 50)
            c_time = self.current_time
        while c_time < self.duration + 2.5:
            msg = self.midi_in.poll()
            if msg is not None:
                self.queue.append((msg, c_time-2.5))
                print(msg, c_time-2.5)
            if self.beep_interval is not None:
                if c_time % self.beep_interval < 0.01:
                    winsound.Beep(262, 50)
            c_time = self.current_time
        
        
        self.stop_listening()
        return self.queue
            

    @property
    def current_time(self):
        """

        Get current time since starting to listen
        """
        return time.perf_counter() - self.init_time

    def start_listening(self):
        """
        Start listening to midi input (open input port and
        get starting time)
        """
        print("start listening")
        self.listen = True
        if self.init_time is None:
            self.init_time = time.perf_counter()

    def stop_listening(self):
        """
        Stop listening to MIDI input
        """
        print("stop listening")
        # break while loop in self.run
        self.listen = False
        # reset init time
        self.init_time = None

class MidiRouter(object):
    """
    This is a class handling MIDI I/O.
    It takes (partial) strings for port names as inputs
    and searches for a fitting port.
    The reason this is set up in this way is that
    different OS tend to name/index MIDI ports differently.

    Use an instance if this class (and *only* this instance)
    to handle everything related to port opening, closing,
    finding, and panic. Expecially Windows is very finicky
    about MIDI ports and it'll likely break if ports are
    handled separately.

    This class can be used to:
    - create a midirouter = MidiRouter(**kwargs) with
    a number of (partial) port names or fluidsynths
    - poll a specific port: e.g.
    midirouter.input_port.poll()
    - send on a specific port: e.g.
    midirouter.output_port.send(msg)
    - open all set ports: midirouter.open_ports()
    - close all set ports: midirouter.close_ports()
    - panic reset all ports: midirouter.panic()
    - get the full name of the used midi ports: e.g.
    midirouter.input_port_name
    (DON'T use this name to open, close, etc with it,
    use the midirouter functions instead)

    Args:
        inport_name (string):
            a (partial) string for the input name.
        outport_name (string):
            a (partial) string for the output name.

    """

    def __init__(
        self,
        inport_name=None,
        outport_name=None
    ):
        self.available_input_ports = mido.get_input_names()
        print("Available inputs MIDI for mido", self.available_input_ports)
        self.available_output_ports = mido.get_output_names()
        print("Available outputs MIDI for mido", self.available_output_ports)

        self.input_port_names = {}
        self.output_port_names = {}
        self.open_ports_list = []

        # the MIDI port name the accompanion listens at (port name)
        self.input_port_name = self.proper_port_name(
            inport_name, True
        )
        # the MIDI port names / Instrument the accompanion is sent
        self.output_port_name = self.proper_port_name(
            outport_name, False
        )

        self.open_ports()

        self.input_port = self.assign_ports_by_name(
            self.input_port_name, input=True
        )
        self.output_port = self.assign_ports_by_name(
            self.output_port_name, input=False
        )

    def proper_port_name(self, try_name, input=True):
        if isinstance(try_name, str):
            if input:
                possible_names = [
                    (i, name)
                    for i, name in enumerate(self.available_input_ports)
                    if try_name in name
                ]
            else:
                possible_names = [
                    (i, name)
                    for i, name in enumerate(self.available_output_ports)
                    if try_name in name
                ]

            if len(possible_names) == 1:
                print(
                    "port name found for trial name: ",
                    try_name,
                    "the port is set to: ",
                    possible_names[0],
                )
                if input:
                    self.input_port_names[possible_names[0][1]] = None
                else:
                    self.output_port_names[possible_names[0][1]] = None
                return possible_names[0]

            elif len(possible_names) < 1:
                print("no port names found for trial name: ", try_name)
                return None
            elif len(possible_names) > 1:
                print(" many port names found for trial name: ", try_name)
                if input:
                    self.input_port_names[possible_names[0][1]] = None
                else:
                    self.output_port_names[possible_names[0][1]] = None
                return possible_names[0]
                # return None
        elif isinstance(try_name, int):
            if input:
                try:
                    possible_name = (try_name, self.available_input_ports[try_name])
                    self.input_port_names[possible_name[1]] = None
                    return possible_name
                except ValueError:
                    raise ValueError(f"no input port found for index: {try_name}")
            else:
                try:
                    possible_name = (try_name, self.available_output_ports[try_name])
                    self.output_port_names[possible_name[1]] = None
                    return possible_name
                except ValueError:
                    raise ValueError(f"no output port found for index: {try_name}")


        else:
            return None

    def open_ports_by_name(self, try_name, input=True):
        if try_name is not None:
            if input:
                port = mido.open_input(try_name)
            else:
                port = mido.open_output(try_name)
                # Adding eventual key release.
                port.reset()

            self.open_ports_list.append(port)
            return port

        else:
            return try_name

    def open_ports(self):
        for port_name in self.input_port_names.keys():
            if self.input_port_names[port_name] is None:
                port = self.open_ports_by_name(port_name, input=True)
                self.input_port_names[port_name] = port
        for port_name in self.output_port_names.keys():
            if self.output_port_names[port_name] is None:
                port = self.open_ports_by_name(port_name, input=False)
                self.output_port_names[port_name] = port

    def close_ports(self):
        for port in self.open_ports_list:
            port.close()
        self.open_ports_list = []

        for port_name in self.output_port_names.keys():
            self.output_port_names[port_name] = None
        for port_name in self.input_port_names.keys():
            self.input_port_names[port_name] = None

    def panic(self):
        for port in self.open_ports_list:
            port.panic()

    def assign_ports_by_name(self, try_name, input=True):
        if try_name is not None:
            if input:
                return self.input_port_names[try_name[1]]
            else:
                return self.output_port_names[try_name[1]]
        else:
            return None

def play_midi_from_score(score=None, 
                         midirouter=None, 
                         quarter_duration=1, 
                         default_velocity=60,
                         print_messages=False):
    
    """
    Play a score using a midirouter
    """
    if midirouter is None:
        print("No midirouter provided")
        return
    if score is None:
        print("No score provided")
        return
    note_array = score.note_array()
    onset_sec = note_array["onset_quarter"] * quarter_duration
    offset_sec = note_array["duration_quarter"] * quarter_duration + onset_sec
    noteon_messages = np.array([("note_on", p, onset_sec[i]) for i, p in enumerate(note_array["pitch"])], dtype=[("msg", "<U10"), ("pitch", int), ("time", float)])
    noteoff_messages = np.array([("note_off", p, offset_sec[i]) for i, p in enumerate(note_array["pitch"])], dtype=[("msg", "<U10"), ("pitch", int), ("time", float)])
    messages = np.concatenate([noteon_messages, noteoff_messages])
    messages = np.sort(messages, order="time")
    timediff = np.diff(messages["time"])
    output_port = midirouter.output_port

    for i, msg in enumerate(messages):
        if i == 0:
            pass
        else:
            time.sleep(timediff[i-1])
        m = mido.Message(msg["msg"], note=msg["pitch"], velocity=default_velocity)
        output_port.send(m)
        if print_messages:
            print(m)

class Sequencer(multiprocessing.Process):
    def __init__(
        self,
        outport_name="seq",
        queue=None,
        *args, 
        **kwargs):
        super(Sequencer, self).__init__(*args, **kwargs)
        self.queue = queue
        self.outport_name = outport_name
        self.router = None

        # sequencer variables
        self.playhead = 0
        self.playing = False
        self.start_time = 0
        self.tempo = 120#120
        self.quarter_per_ns = self.tempo / ( 60 * 1e9)
        self.next_time = 0

        # music variables
        self.default_velocity = 60
        self.loop_start_quarter = 0
        self.loop_end_quarter = 8
        self.looped_notes = None
        self.onset_quarter = None
        self.offset_quarter = None
        self.messages = None
        self.message_times = None

    def up(self, args):
        self.queue.put(args)

    def update_part(self, part):
        pass
        note_array = part.note_array()
        mask_lower = note_array["onset_quarter"] >= self.loop_start_quarter           
        mask_upper = note_array["onset_quarter"] < self.loop_end_quarter
        mask = np.all((mask_lower, mask_upper), axis=0)
        self.looped_notes = note_array[mask]
        self.onset_quarter = note_array[mask]["onset_quarter"]
        self.offset_quarter = np.clip(note_array[mask]["duration_quarter"] + self.onset_quarter, 
                                      self.loop_start_quarter, 
                                      self.loop_end_quarter-0.1)
        
        self.messages = defaultdict(list)
        self.message_times = np.array([])

        for i, note in enumerate(self.looped_notes):
            on = mido.Message('note_on', 
                         note=note["pitch"], 
                         velocity=self.default_velocity, 
                         time=0)
            off = mido.Message('note_off',
                            note=note["pitch"],
                            velocity=0,
                            time=0)
            self.messages[self.onset_quarter[i]].append(on)
            self.messages[self.offset_quarter[i]].append(off)

        self.message_times = np.sort(np.array(list(self.messages.keys())))
        self.next_time = self.message_times[0]
        print(self.message_times)
        
    def run(self):
        self.start_time = time.perf_counter_ns()
        self.router = MidiRouter(outport_name = self.outport_name)
        self.playing = True
        print("Sequencer started")        
        while self.playing:
            try: 
                args = self.queue.get_nowait()
                # print(args.note_array())
                self.update_part(args)
            except:
                pass

            current_time = time.perf_counter_ns()
            elapsed_time = current_time - self.start_time
            elapsed_quarter = elapsed_time * self.quarter_per_ns
            self.playhead = elapsed_quarter % (self.loop_end_quarter - self.loop_start_quarter)
            if self.playhead >= self.next_time - 0.02 and \
                self.playhead < self.next_time + 0.1 and \
                self.messages is not None:

                for msg in self.messages[self.next_time]:
                    self.router.output_port.send(msg)
                    

                # this_time = self.next_time
                idx, = np.where(self.message_times == self.next_time)
                i = idx[0]
                self.next_time = self.message_times[(i+1)%len(self.message_times)]
                # print("sent", msg, i, self.next_time, self.playhead, self.message_times)
                # time.sleep((self.next_time - this_time) / 2* self.quarter_per_ns * 1e9)

            else:
                time.sleep(0.02)

    # def stop(self):
    #     self.playing = False
    #     self.join()

class MidiSyncSender(multiprocessing.Process):
    def __init__(self, 
                 outport_name,
                 queue, 
                 tempo,
                 *args, **kwargs):
        super(MidiSyncSender, self).__init__(*args, **kwargs)
        self.outport_name = outport_name
        self.queue = queue
        self.playing = False    
        self.update_time = self.set_time(tempo)
        self.reset()

        self.start_msg = mido.Message.from_bytes([0xFA])
        self.sync_msg = mido.Message.from_bytes([0xF8])
        self.stop_msg = mido.Message.from_bytes([0xFC])

    def reset(self):    
        self.counter = 0
        self.playing = False
        self.current_time = time.perf_counter_ns()
        self.playnext = time.perf_counter_ns()
        self.router = None


    def set_time(self, tempo_in_bpm):
        seconds_per_beat = 60/tempo_in_bpm
        # https://www.midi.org/specifications/midi-reference-tables/summary-of-midi-1-0-messages
        # 11111000 Timing Clock. Sent 24 times per quarter note when synchronization is required (see text).
        seconds_per_clock = seconds_per_beat / 24
        ns_per_clock = int(seconds_per_clock * 1e9)
        return ns_per_clock

    def up(self, args):
        self.queue.put(args)

    def run(self):
        self.sendMIDISYNC()

    def sendMIDISYNC(self):     
        self.reset()
        self.playing = True
        # midirouter here avoids error "Python Multiprocessing - cannot pickle '_thread.lock' object"
        self.router = MidiRouter(outport_name = self.outport_name)    
        self.router.output_port.send(self.start_msg)
            
        while self.playing:
            try: 
                tmp = self.queue.get_nowait()
                # print(args.note_array())
                self.update_time = self.set_time(tmp)
            except:
                pass

            try:
                """ Check the time and produce MIDI messages if needed: """
                self.current_time = time.perf_counter_ns()
                if self.current_time >= self.playnext:     
                    self.router.output_port.send(self.sync_msg)
                    self.playnext += self.update_time
                    self.counter += 1
                                                
                time.sleep(1e-5)
            
            except KeyboardInterrupt:
                self.stopMIDISYNC()
                break

    def stop(self):
        self.stopMIDISYNC()

    def stopMIDISYNC(self):
        self.playing = False
        self.router.output_port.send(self.stop_msg)
        self.router.panic()
        self.router.close_ports()
        self.terminate()
        self.join()

class MidiFX(multiprocessing.Process):
    def __init__(self, 
                 inport_name,
                 outport_name,
                 secondary_inport_name,
                 fx = None,
                 verbose = False,
                 *args, **kwargs):
        super(MidiFX, self).__init__(*args, **kwargs)
        self.outport_name = outport_name
        self.inport_name = inport_name
        self.secondary_inport_name = secondary_inport_name
        self.verbose = verbose
        self.router = None
        if fx is not None:
            self.fx = fx       
        else:
            self.fx = self.default_fx
        self.playing = False    

    def default_fx(self, msg):
        print("in fx: ", msg)
        return [msg]

    def run(self):
        self.midiFX()

    def midiFX(self): 
        self.router = MidiRouter(inport_name = self.inport_name,
                                 outport_name = self.outport_name) 
        self.secondary_router = MidiRouter(inport_name = self.secondary_inport_name) 
    
        self.playing = True 
        while self.playing:
            try:
                for msg in self.router.input_port.iter_pending():
                    if not msg.is_cc():
                        if self.verbose:
                            print("INPUT::::", msg)
                        out_msgs = self.fx(msg)
                        for out_msg in out_msgs:
                            if self.verbose:
                                print("OUTPUT:::", out_msg)
                            self.router.output_port.send(out_msg) 
                for msg in self.secondary_router.input_port.iter_pending():
                    # if msg.is_cc():
                        # only for cc's
                    out_msgs = self.fx(msg, True)
                    # for out_msg in out_msgs:
                    #     self.router.output_port.send(out_msg) 
       
                time.sleep(1e-6)
            
            except KeyboardInterrupt:
                self.stop()
                break

    def stop(self):
        self.playing = False
        self.router.panic()
        self.router.close_ports()
        self.terminate()
        self.join()


if __name__ == "__main__":


    #### MIDI SEQUENCER

    # part = pt.load_musicxml(pt.EXAMPLE_MUSICXML)[0]
    # queue =multiprocessing.Queue()
    # s = Sequencer(queue=queue,
    #               outport_name="seq")
    # s.start()
    # time.sleep(2)
    # s.up(part)

    # time.sleep(4)
    # s.terminate()
    # s.join()

    #### MIDI SYNC

    # queue = multiprocessing.Queue()
    # mss = MidiSyncSender("seq", queue, 100)
    # mss.start()

    #### MIDI FX

    mfx = MidiFX("MPK", "MPK")
    mfx.start()