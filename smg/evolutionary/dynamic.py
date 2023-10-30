
import numpy as np
import partitura as pt
from smg.utils import  FourPartProgression
from smg.utils import (partFromFourPartProgression,
                        FourPartChord, chord_types)

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
    

if __name__ == "__main__":
    

    exp = FourPartOptimizerLocal()
    p = exp.run()