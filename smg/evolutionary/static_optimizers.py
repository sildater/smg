
import numpy as np
import partitura as pt
from smg.utils import Chord, Progression, FourPartProgression, euclidean
from smg.utils import (cycle_distance, chordDistance, parttimefromrekorder,
                        partFromFourPartProgression)

class Optimizer:
    def __init__(self):
        pass    

    def modify(self, population):
        # add an accidental
        subpop3 = np.random.choice(population, 30)
        for element in subpop3:
            cidx = np.random.randint(len(element.chords))
            nidx = np.random.randint(4)
            mod = np.random.choice([-1,1])
            new_element = element.copy()
            new_element.chords[cidx].add_repitch(nidx,mod)
            population.append(new_element)
        
        # invert a chord
        subpop4 = np.random.choice(population, 30)
        for element in subpop4:
            cidx = np.random.randint(len(element.chords))
            nidx = np.random.randint(4)
            new_element =  element.copy()
            new_element.chords[cidx].invert(nidx)
            population.append(new_element)
            
        # join some elements
        subpop1 = np.random.choice(population, 30)
        subpop2 = np.random.choice(population, 30)
        for element0, element1 in zip(subpop1, subpop2):
            elnew1, elnew2 = element0.join(element1)
        
            population.append(elnew1)
            population.append(elnew2)
        
        return population
    
    def fitness(self, progression, melody_windows):
        # the lower the fitness score the better
        fit = 0
        for c0,c1 in zip(progression.chords[:-1], progression.chords[1:]):
            _, dist = chordDistance(c0.pitches, c1.pitches)
            # penalize big leaps between pitches of adjacent chords
            fit += dist 
            # penalize big leaps between scale tonic of adjacent chords
            fit += abs(c0.offset - c1.offset)
            # penalize small leaps between root of adjacent chords
            fit += abs(5.0 - cycle_distance(c0.root,c1.root))
            
            #penalize sticking on a root
            if c0.root_id == c1.root_id:
                fit += 30
            
        for i, c0 in enumerate(progression.chords):
            for note in melody_windows[i]:
                fit += 3 * np.min([cycle_distance(note, pit) for pit in c0.pitches] ) 
                # print(fit, melody_windows[i], c0.pitches)
        # add a small random number for hashing
        fit += np.random.rand(1)[0]
        return fit 
    
    def select(self, population, number, melody_windows):
        pop = {ele.id:ele for ele in population}
        fitness_dict = {self.fitness(ele, melody_windows):ele.id for ele in population}
        sorted_fitness = list(fitness_dict.keys())
        sorted_fitness.sort()
        # print(sorted_fitness)
        # print([(len(pop[fitness_dict[k]].chords), k) for k in sorted_fitness[:50]])
        new_pop = [pop[fitness_dict[k]] for k in sorted_fitness[:number]]
        return new_pop, sorted_fitness

    def run(self,
            epochs = 10,
            population_size = 100,
            population_replacement = 0.3,
            new_population = True,
            melody = None,
            number_of_chords = 8,
            quarter_duration = 4,
            quarters = 8):
        
        # find best euclidean rhythm
        melody_onsets = [note["onset_sec"] for note in melody]
        melody_onsets_int = np.round(np.array(melody_onsets) / (10.0/quarters) * quarter_duration)
        # use up to eight notes
        number_of_notes = np.min((len(melody_onsets), number_of_chords))
        spaced_idx = np.round(np.linspace(0, len(melody_onsets_int) - 1, number_of_notes)).astype(int)
        melody_onsets_int = melody_onsets_int[spaced_idx]
        positions = quarter_duration * quarters # 8 quarters, 1.25 sec
        dists = dict()
        for k in range(positions):
            euc = euclidean(cycle = positions, pulses = number_of_notes, offset= k)
            dist = np.sum(np.abs(euc - melody_onsets_int))
            euc[0] = 0
            euc_shifted = list(np.roll(euc, -1))[:number_of_notes] + [positions]
            dists[dist] = [(on, off) for on, off in zip(euc, euc_shifted)]

        min_dist = np.min(list(dists.keys()))
        rhythm = dists[min_dist]

        na, frames = parttimefromrekorder(melody,
                                 quarter_duration = quarter_duration,
                                 num_frames = number_of_notes,
                                 rhythm = rhythm)
        print(na, frames)

        if new_population:
            population = [Progression(number_of_chords= number_of_notes) for po in range(population_size)]    
        else:
            population = self.population
        
        for epoch in range(epochs): 
            population = self.modify(population)
            population, sorted_fitness = self.select(population, int(population_replacement * population_size), frames) 
            print(f"Epoch {epoch} best fitness: {sorted_fitness[0]:.4f}")
            population += [Progression(number_of_chords= number_of_notes) 
                           for po in range(population_size - len(population))]


        self.population = population
        return self.population, rhythm

class Optimizer2:
    def __init__(self):
        pass    

    def modify(self, population):
        # add an accidental
        subpop3 = np.random.choice(population, 10)
        for element in subpop3:
            cidx = np.random.randint(len(element.chords))
            nidx = np.random.randint(4)
            mod = np.random.choice([-1,1])
            new_element = element.copy()
            new_element.chords[cidx].add_repitch(nidx,mod)
            population.append(new_element)
        
        # invert a chord
        subpop4 = np.random.choice(population, 10)
        for element in subpop4:
            cidx = np.random.randint(len(element.chords))
            nidx = np.random.randint(4)
            new_element =  element.copy()
            new_element.chords[cidx].invert(nidx)
            population.append(new_element)

        # change root of a chord
        subpop4 = np.random.choice(population, 10)
        for element in subpop4:
            cidx = np.random.randint(len(element.chords))
            nidx = np.random.randint(7)
            new_element =  element.copy()
            new_element.chords[cidx].root_id = nidx
            new_element.chords[cidx].compute_pitch()
            population.append(new_element)
            
        # # join some elements
        # subpop1 = np.random.choice(population, 30)
        # subpop2 = np.random.choice(population, 30)
        # for element0, element1 in zip(subpop1, subpop2):
        #     elnew1, elnew2 = element0.join(element1)
        #     population.append(elnew1)
        #     population.append(elnew2)
        
        return population
    
    def fitness(self, progression, melody_windows):
        # the lower the fitness score the better
        fit = 0
        for c0,c1 in zip(progression.chords[:-1], progression.chords[1:]):
            _, dist = chordDistance(c0.pitches, c1.pitches)
            # penalize big leaps between pitches of adjacent chords
            fit += dist 
            # penalize big leaps between scale tonic of adjacent chords
            fit += abs(c0.offset - c1.offset)
            # penalize small leaps between root of adjacent chords
            fit += abs(5.0 - cycle_distance(c0.root,c1.root))
            
            #penalize sticking on a root
            if c0.root_id == c1.root_id:
                fit += 30
            
        for i, c0 in enumerate(progression.chords):
            for note in melody_windows[i]:
                fit += 3 * np.min([cycle_distance(note, pit) for pit in c0.pitches] ) 
                # print(fit, melody_windows[i], c0.pitches)
        # add a small random number for hashing
        fit += np.random.rand(1)[0]
        return fit 
    
    def select(self, population, number, melody_windows):
        pop = {ele.id:ele for ele in population}
        fitness_dict = {self.fitness(ele, melody_windows):ele.id for ele in population}
        sorted_fitness = list(fitness_dict.keys())
        sorted_fitness.sort()
        # print(sorted_fitness)
        # print([(len(pop[fitness_dict[k]].chords), k) for k in sorted_fitness[:50]])
        new_pop = [pop[fitness_dict[k]] for k in sorted_fitness[:number]]
        return new_pop, sorted_fitness

    def run(self,
            epochs = 10,
            population_size = 100,
            population_replacement = 0.3,
            new_population = True,
            melody = None,
            number_of_chords = 8,
            quarter_duration = 4,
            quarters = 8):
        
        # find best euclidean rhythm
        melody_onsets = [note["onset_sec"] for note in melody]
        melody_onsets_int = np.round(np.array(melody_onsets) / (10.0/quarters) * quarter_duration)
        # use up to eight notes
        number_of_notes = np.min((len(melody_onsets), number_of_chords))
        spaced_idx = np.round(np.linspace(0, len(melody_onsets_int) - 1, number_of_notes)).astype(int)
        melody_onsets_int = melody_onsets_int[spaced_idx]
        positions = quarter_duration * quarters # 8 quarters, 1.25 sec
        dists = dict()
        for k in range(positions):
            euc = euclidean(cycle = positions, pulses = number_of_notes, offset= k)
            dist = np.sum(np.abs(euc - melody_onsets_int))
            euc[0] = 0
            euc_shifted = list(np.roll(euc, -1))[:number_of_notes-1] + [positions]
            dists[dist] = [(on, off) for on, off in zip(euc, euc_shifted)]

        min_dist = np.min(list(dists.keys()))
        rhythm = dists[min_dist]

        na, frames = parttimefromrekorder(melody,
                                 quarter_duration = quarter_duration,
                                 num_frames = number_of_notes,
                                 rhythm = rhythm)
        print(na, frames)

        if new_population:
            population = [Progression(number_of_chords= number_of_notes) for po in range(population_size)]    
        else:
            population = self.population
        
        for epoch in range(epochs): 
            population = self.modify(population)
            population, sorted_fitness = self.select(population, int(population_replacement * population_size), frames) 
            print(f"Epoch {epoch} best fitness: {sorted_fitness[0]:.4f}")
            population += [Progression(number_of_chords= number_of_notes) 
                           for po in range(population_size - len(population))]


        self.population = population
        return self.population, rhythm
    

class FourPartOptimizer:
    def __init__(self):
        self.population = None   

    def modify(self, population, number_to_mutate, number_to_recombine):
        # point mutation of chord
        # subpop4 = np.random.choice(population, number_to_mutate)
        # for element in subpop4:
        #     cidx = np.random.randint(len(element.chords))
        #     new_element = element.copy()
        #     new_element.point_mutate(cidx)
        #     population.append(new_element)
            
        # recombination of sequence
        subpop1 = np.random.choice(population, number_to_recombine)
        subpop2 = np.random.choice(population, number_to_recombine)
        for element0, element1 in zip(subpop1, subpop2):
            elnew1, elnew2 = element0.join(element1)
            population.append(elnew1)
            population.append(elnew2)
        
        return population
    
    def fitness(self, progression, melody, voice):
        progression.set_voice(melody, voice)
        fit = 0.0
        for c0,c1 in zip(progression.chords[:-1], progression.chords[1:]):
            fit += np.abs(c0.soprano - c1.soprano)
            fit += np.abs(c0.alto - c1.alto)
            fit += np.abs(c0.tenor - c1.tenor)
        # add a small random number for hashing
        fit += np.random.rand(1)[0]
        return float(fit) 
    
    def select(self, population, melody, voice, number_to_keep):
        pop = {ele.id:ele for ele in population}
        # import pdb; pdb.set_trace()
        fitness_dict = {self.fitness(ele, melody, voice):ele.id for ele in population}
        sorted_fitness = list(fitness_dict.keys())
        sorted_fitness.sort()
        new_pop = [pop[fitness_dict[k]] for k in sorted_fitness[:number_to_keep]]
        best_prog = pop[fitness_dict[sorted_fitness[0]]]
        return new_pop, sorted_fitness, best_prog

    def run(self,
            epochs = 200,
            population_size = 100,
            replacement_ratio = 0.2,
            mutation_ratio = 0.2,
            combination_ratio = 0.2,
            new_population = True,
            melody = np.array([48,50,53,48,50,47,43,48]),
            voice = 3,
            number_of_chords = 8,
            save_part = 8):
        

        part = None
        number_to_keep = int((1 - replacement_ratio) * population_size)
        number_to_sample = int((replacement_ratio) * population_size)
        number_to_mutate = int(mutation_ratio  * population_size)
        number_to_recombine = int(combination_ratio  * population_size)

        if new_population:
            population = [FourPartProgression(number_of_chords = number_of_chords) for po in range(population_size)]    
        else:
            population = self.population
        
        for epoch in range(epochs): 
            # select(self, population, melody, voice, number)
            population = self.modify(population, number_to_mutate, number_to_recombine) 
            population, sorted_fitness, best_prog = self.select(population, melody, voice, number_to_keep) 
            print(f"Epoch {epoch} best fitness: {sorted_fitness[0]:.4f}")
            if epoch % save_part == 0:
                part = partFromFourPartProgression(best_prog, 
                                part = part,
                                quarter_duration = 1,
                                time_offset = (epoch // save_part) *8)
                # import pdb; pdb.set_trace()
            
            population += [FourPartProgression(number_of_chords = number_of_chords) for po in range(number_to_sample)]

        self.population = population
        
        pt.score.add_measures(part)
        pt.save_musicxml(part, "evol_test_out_50.musicxml")
        return self.population

    

if __name__ == "__main__":
    
    # fields = [
    # ("onset_sec", "f4"),
    # ("duration_sec", "f4"),
    # ("pitch", "i4"),
    # ("velocity", "i4"),
    # ]
    # rows = [
    # (0.933,1.712,48,100),
    # (7.176,1.885,51,100),
    # (2.685,1.777,53,100),
    # (4.464,2.71,59,100),
    # ]
    # note_array = np.array(rows, dtype=fields)
    # exp = Optimizer()
    # p = exp.run(melody=note_array)

    exp = FourPartOptimizer()
    p = exp.run()