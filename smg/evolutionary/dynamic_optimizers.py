
import numpy as np
import partitura as pt
from smg.utils import  FourPartProgression
from smg.utils import (partFromFourPartProgression,
                        FourPartChord, chord_types)
from smg.utils import MidiFX
import mido
from collections import defaultdict

class FourPartOptimizerLocal:
    def __init__(self):
        self.population = None   
    
    def fitness(self, progression, melody, voice, index_range = (0, 1)):
        progression.set_voice(melody, voice)
        fit = 0.0
        for c0, c1 in zip(progression.chords[index_range[0]:index_range[1]], 
                          progression.chords[index_range[0]+1:index_range[1]+1]):
            melodic_lines = np.array([c1.soprano - c0.soprano, c1.alto - c0.alto, c1.tenor - c0.tenor])
            melodic_lines_bass = np.array([c1.soprano - c0.soprano, c1.alto - c0.alto, c1.tenor - c0.tenor, c1.bass - c0.bass])
            fit += np.sum(np.abs(melodic_lines)) # penalize large leaps
            if (melodic_lines_bass > 0).sum() >= 3:
                fit += 5 # similar motion
            elif (melodic_lines_bass < 0).sum() >= 3:
                fit += 5 # similar motion

            intervals0 = np.array([c0.soprano - c0.alto, c0.alto - c0.tenor, c0.soprano - c0.tenor])
            intervals1 = np.array([c1.soprano - c1.alto, c1.alto - c1.tenor, c1.soprano - c1.tenor])
            for i0, i1 in zip(intervals0, intervals1):
                if i0 == i1: 
                    if np.abs(i0) == 7:
                        fit += 10 # parallel fifths
                    elif np.abs(i0) == 12:
                        fit += 10 # parallel octave
            # if (melodic_lines == 7).sum() >= 2:
            #     fit += 10 # parallel fifths
            # if (melodic_lines == -7).sum() >= 2:
            #     fit += 10 # parallel fifths
            # if (melodic_lines == 12).sum() >= 2:
            #     fit += 20 # parallel octave
            # if (melodic_lines == -12).sum() >= 2:
            #     fit += 20 # parallel octave
            
        # add a small random number for hashing
        fit += np.random.rand(1)[0]
        return float(fit) 
    
    def run(self,
            melody = np.array([48,50,53,48,50,47,43,48]),
            voice = 3,
            number_of_chords = 8):
        
        chord_possibilities = list(chord_types.keys())
        part = None
        ctype_start = dict()
        for ctype_idx, ctype in enumerate(chord_possibilities):
            progression = FourPartProgression(number_of_chords = number_of_chords)
            progression.point_mutate(0, ctype)
            for chord_position in range(1, number_of_chords): 
                ctype_next_dict = dict()
                for ctype_next in chord_possibilities:
                    progression.point_mutate(chord_position, ctype_next)
                    fitness = self.fitness(progression, melody, voice, index_range = (chord_position-1, chord_position))
                    ctype_next_dict[fitness] = ctype_next
                    
                ctype_next_fit = np.array(list(ctype_next_dict.keys()))
                ctype_next_optimal = ctype_next_dict[np.min(ctype_next_fit)]
                progression.point_mutate(chord_position, ctype_next_optimal)
            
                #
                # print(f"Position {chord_position} best fitness ctype: {ctype_next_fit} for id {list(ctype_next_dict.keys())}")
                # print(f"Position {chord_position} fitness {[(int(k), ctype_next_dict[k]) for k in list(ctype_next_dict.keys())]}")
            ctype_start[ctype] = (progression, self.fitness(progression, melody, voice, index_range = (0, 7)))
            part = partFromFourPartProgression(progression, 
                                                part = part,
                                                quarter_duration = 1,
                                                time_offset = ctype_idx  *8)
            
        pt.score.add_measures(part)
        pt.save_musicxml(part, "dynamic_test_out.musicxml")
        return ctype_start
    

class FourPartOptimizerLocalMidiFX:
    def __init__(self, voice = 3, scale_offset = 3):
        self.voice = voice
        self.scale_offset = scale_offset
        self.progression = FourPartProgression(number_of_chords = 2, offset = self.scale_offset)
        self.chord_possibilities = list(chord_types.keys())
        # initial settings
        self.first_chord_ctype = np.random.choice(self.chord_possibilities)
        self.second_chord_ctype = None
        self.two_note_melody = np.array([57 + self.scale_offset, 60 + self.scale_offset])
        self.progression.point_mutate(0, self.first_chord_ctype)
        self.out_pitches = [0]
        self.out_pitches_by_in_pitch = defaultdict(list)
        self.out_messages = list()
        self.out_messages_off = list()
        self.send_msg = True
        print("optimizer ready")

    def scalify(self, input_array, 
                scale = np.array([0,2,2,4,4,5,5,7,9,9,11,11])):

        output_array = (input_array-self.scale_offset)-(input_array-self.scale_offset)%12 + \
            scale[(input_array-self.scale_offset)%12] + self.scale_offset
        return output_array
        
    def fitness(self, progression, melody, voice, index_range = (0, 1)):
        progression.set_voice(melody, voice)
        fit = 0.0
        for c0, c1 in zip(progression.chords[index_range[0]:index_range[1]], 
                          progression.chords[index_range[0]+1:index_range[1]+1]):
            melodic_lines = np.array([c1.soprano - c0.soprano, c1.alto - c0.alto, c1.tenor - c0.tenor])
            melodic_lines_bass = np.array([c1.soprano - c0.soprano, c1.alto - c0.alto, c1.tenor - c0.tenor, c1.bass - c0.bass])
            fit += np.sum(np.abs(melodic_lines)) # penalize large leaps
            if (melodic_lines_bass > 0).sum() >= 3:
                fit += 5 # similar motion
            elif (melodic_lines_bass < 0).sum() >= 3:
                fit += 5 # similar motion

            intervals0 = np.array([c0.soprano - c0.alto, c0.alto - c0.tenor, c0.soprano - c0.tenor])
            intervals1 = np.array([c1.soprano - c1.alto, c1.alto - c1.tenor, c1.soprano - c1.tenor])
            for i0, i1 in zip(intervals0, intervals1):
                if i0 == i1: 
                    if np.abs(i0) == 7:
                        fit += 10 # parallel fifths
                    elif np.abs(i0) == 12:
                        fit += 10 # parallel octave
            
        # add a small random number for hashing
        fit += np.random.rand(1)[0]
        return float(fit) 

    
    def __call__(self, msg, secondary = False):
        out_msgs = []
        if msg.type == "note_on":
            new_pitch = self.scalify(msg.note)
            
            new_vel = msg.velocity
            self.two_note_melody[1] = new_pitch

            ctype_next_dict = dict()
            for ctype_next in self.chord_possibilities:
                self.progression.point_mutate(1, ctype_next)
                fitness = self.fitness(self.progression, self.two_note_melody, self.voice, index_range = (0, 1))
                ctype_next_dict[fitness] = ctype_next
                
            ctype_next_fit = np.array(list(ctype_next_dict.keys()))
            ctype_next_optimal = ctype_next_dict[np.min(ctype_next_fit)]

            self.progression.point_mutate(1, ctype_next_optimal)
            self.progression.set_voice(self.two_note_melody, self.voice)

            self.out_pitches = [
                self.progression.chords[1].soprano[0],
                self.progression.chords[1].alto[0],
                self.progression.chords[1].tenor[0],
                self.progression.chords[1].bass[0]
                ]

            # use this for note off
            self.out_pitches_by_in_pitch[new_pitch] += self.out_pitches 
            # SEND DIRECTLY instead of self.out_messages
            if self.send_msg:
                out_msgs = [
                    # TODO: apreggiation with time?
                    mido.Message('note_on', note=pitch, velocity=new_vel, time=0) for _, pitch in enumerate(self.out_pitches)
                ]

            # ready for next note
            self.two_note_melody[0] = new_pitch
            self.progression.point_mutate(0, ctype_next_optimal)

        elif msg.type == "note_off":
            new_pitch = self.scalify(msg.note)
            if len(self.out_pitches_by_in_pitch[new_pitch]) > 0:
                off_pitches = self.out_pitches_by_in_pitch.pop(new_pitch)
            else:
                off_pitches = self.out_pitches

            # SEND DIRECTLY
            if self.send_msg:
                out_msgs = [
                    mido.Message('note_off', note=pitch, velocity=0, time=0) for pitch in off_pitches
                ]

        elif msg.is_cc():

            if msg.control == 1: # set voice
                self.voice = msg.value // 32
                print("new voice: ", self.voice) 

            elif msg.control == 2: # reassign ctype
                ctype_idx = np.floor(msg.value  / 128 * len(self.chord_possibilities)).astype(int)
                self.first_chord_ctype = self.chord_possibilities[ctype_idx]
                self.progression.point_mutate(0, self.first_chord_ctype)   
                print("new ctype: ", self.first_chord_ctype)    

            # elif msg.control == 3: # set scale
            #     scale_offset = np.floor(msg.value  / 128 * 12).astype(int)
            #     self.progression.offset = scale_offset
            #     self.scale_offset = scale_offset
            #     self.two_note_melody = np.array([57 + self.scale_offset, 60 + self.scale_offset])
            #     self.progression.point_mutate(0, self.first_chord_ctype)   
            #     print("new scale: ", self.scale_offset)    

            #         elif msg.control == 64:
            #             if msg.value == 127:
            #                 out_msgs = self.out_messages
            #                 self.out_messages_off = [mido.Message('note_off', note=msg.note, velocity=0, time=0) for msg in self.out_messages]
            #             elif msg.value == 0:
            #                 out_msgs = self.out_messages_off
            #             print("new pedal:", msg, out_msgs)

            elif msg.control == 64: # turn off/on note sending
                if msg.value == 127:
                    self.send_msg = False
                elif msg.value == 0:
                    self.send_msg = True
                print("new pedal:", self.send_msg)

        if secondary and msg.type == "note_on":
            scale_offset = msg.note%12
            self.progression.offset = scale_offset
            self.scale_offset = scale_offset
            self.two_note_melody = np.array([57 + self.scale_offset, 60 + self.scale_offset])
            self.progression.point_mutate(0, self.first_chord_ctype)   
            print("new scale: ", self.scale_offset)    

        return out_msgs

if __name__ == "__main__":
    
    #### local bellman style update
    # exp = FourPartOptimizerLocal()
    # p = exp.run()#

    #### REALTIME EVOL MIDI FX

    effect = FourPartOptimizerLocalMidiFX()
    mfx = MidiFX("iM", "iM", "MPK", fx = effect)
    # mfx = MidiFX("Clavi", "Clavi", "MPK", fx = effect)
    mfx.start()





























