from copy import deepcopy
from typing import Dict, Set
from collections import defaultdict
from itertools import combinations, chain
from .graph import MyGraph
import re


class AlphaPlus:

    def __init__(self, variants) -> None:
        self.variants = variants
        self.events = self.get_events()
        self.direct_succession = self.get_direct_succesion()
        self.triangles = self.get_triangles_and_rombs()[0]
        self.rombs = self.get_triangles_and_rombs()[1]
        self.causality = self.get_causality()
        self.inv_causality = self.get_inv_causality()
        self.parallel_events = self.get_potential_parallelism()
        self.start_events = self.get_start_events()
        self.end_events = self.get_end_events()
        self.Xl = self.get_Xl()
        self.Yl = self.get_Yl()
        self.self_loop_events = self.get_self_loop_events()
    

    def get_events(self):
        events_set = set(list(chain(*self.variants)))
        return events_set


    def get_direct_succesion(self) -> Dict[str, Set[str]]:
        succession = defaultdict(set)
        for variant in self.variants:
            for inx, event in enumerate(variant[:-1]):
                succession[event].add(variant[inx+1])
        return dict(succession)
    

    def get_triangles_and_rombs(self):
        triangles = set()
        rombs = set()
        pairs = list(combinations(self.events, 2))
        
        for event_a, event_b in pairs:
            a_first = False
            b_first = False

            pattern_a = event_a + event_b + event_a
            pattern_b = event_b + event_a + event_b

            for variant in self.variants:
                variant_string = "".join(variant)

                pattern_a_found = re.search(f"{pattern_a}", variant_string)
                pattern_b_found = re.search(f"{pattern_b}", variant_string)

                if pattern_a_found:
                    a_first = True
                if pattern_b_found:
                    b_first = True

            if a_first and b_first:
                rombs.add((event_a, event_b))
                rombs.add((event_b, event_a))
            elif a_first:
                triangles.add((event_a, event_b))
            elif b_first:
                triangles.add((event_b, event_a))
        
        return triangles, rombs


    def get_causality(self):
        causality = defaultdict(set)
        for ev_cause, events in self.direct_succession.items():
            for event in events:
                if ev_cause not in self.direct_succession.get(event, set()) or (event, ev_cause) in self.rombs:
                    causality[ev_cause].add(event)
                if (ev_cause not in self.direct_succession.get(event, set())):
                    causality[ev_cause].add(event)
        return dict(causality)


    def get_inv_causality(self) -> Dict[str, Set[str]]:
        inv_causality = defaultdict(set)
        for key, values in self.causality.items():
            for value in values: 
                inv_causality[value].add(key)
        return {k: v for k, v in inv_causality.items() if len(v) > 1}


    def get_potential_parallelism(self) -> Dict[str, Set[str]]:
        parallelism = set()
        for ev_cause, events in self.direct_succession.items():
            for event in events:
                if ev_cause in self.direct_succession.get(event, set()) and (ev_cause, event) not in self.rombs:
                    parallelism.add((ev_cause, event))
        return parallelism

    
    def get_start_events(self):
        start_events = set()
        for variant in self.variants:
            start_events.add(variant[0])
        return start_events


    def get_end_events(self):
        end_events = set()
        for variant in self.variants:
            end_events.add(variant[-1])
        return end_events


    def is_independent(self, event_a, event_b):
        independent = True
        if event_b in self.causality.get(event_a, set()) or event_a in self.causality.get(event_b, set()):
            independent = False
        if (event_a, event_b) in self.parallel_events or (event_b, event_a) in self.parallel_events:
            independent = False
        return independent


    def all_pairs_independent(self, combination):
        all_pairs_independent = True
        pairs = list(combinations(combination, 2))
        for pair in pairs:
            if not self.is_independent(pair[0], pair[1]):
                all_pairs_independent = False
        return all_pairs_independent


    def get_Xl(self):
        all_combinations = []
        for source in self.causality:
            for inx in range(1, len(self.causality[source]) + 1):
                event_combinations = list(combinations(self.causality[source], inx))
                for combination in event_combinations:
                    if len(combination) == 1:
                        all_combinations.append((set((source,)), set(combination)))
                    elif self.all_pairs_independent(combination):
                            all_combinations.append((set((source,)), set(combination)))

        for target in self.inv_causality:
            for inx in range(2, len(self.inv_causality[target]) + 1):
                event_combinations = list(combinations(self.inv_causality[target], inx))
                for combination in event_combinations:
                    if self.all_pairs_independent(combination):
                            all_combinations.append((set(combination), set((target,))))
        
        return all_combinations


    def get_Yl(self):
        Yl = deepcopy(self.Xl)
        non_maximal_combination = list()
        for task_connection in Yl:
            precedessors = task_connection[0]
            successors = task_connection[1]

            if len(precedessors) > 1:
                for inx in range(1, len(precedessors)):
                    precedessors_combinations = combinations(precedessors, inx)
                    non_maximal_combination.append([(set(combination), set(successors)) for combination in precedessors_combinations])
            
            if len(successors) > 1:
                for inx in range(1, len(successors)):
                    successors_combinations = combinations(successors, inx)
                    non_maximal_combination.append([(set(precedessors), set(combination)) for combination in successors_combinations])

        non_maximal_combination = list(chain.from_iterable(non_maximal_combination))

        for combination in non_maximal_combination:
            if combination in Yl:
                Yl.remove(combination)
        return Yl


    def add_start_events(self, graph: MyGraph):
        graph.add_event("start")
        if len(self.start_events) > 1:
            if tuple(self.start_events) in self.parallel_events:
                graph.add_and_split_gateway("start", self.start_events)
            else:
                graph.add_xor_split_gateway("start", self.start_events)
        else:
            graph.add_edge("start", list(self.start_events)[0])


    def add_end_events(self, graph: MyGraph):
        graph.add_end_event("end")
        if len(self.end_events) > 1:
            if tuple(self.end_events) in self.parallel_events: 
                graph.add_and_merge_gateway(self.end_events, "end")
            else:
                graph.add_xor_merge_gateway(self.end_events, "end")    
        else: 
            graph.add_edge(list(self.end_events)[0],"end")

    
    def add_single_edges(self, graph: MyGraph):
        for pattern in self.Yl:
            if len(pattern[0]) == 1 and len(pattern[1]) == 1:
                source = list(pattern[0])[0]
                target = list(pattern[1])[0]
                graph.add_edge(source, target)


    def add_xor_split_pattern(self, graph: MyGraph):
        for pattern in self.Yl:
            if len(pattern[0]) == 1 and len(pattern[1]) > 1:
                source = list(pattern[0])[0]
                targets = list(pattern[1])
                graph.add_xor_split_gateway(source, targets)


    def add_xor_join_pattern(self, graph: MyGraph):
        for pattern in self.Yl:
            if len(pattern[0]) > 1 and len(pattern[1]) == 1:
                sources = list(pattern[0])
                target = list(pattern[1])[0]
                graph.add_xor_merge_gateway(sources, target)


    def merge_multiple_edges(self, graph: MyGraph):
        for event in list(self.events):

            if event in graph.nodes():
                input_events = graph.in_neighbors(event)
                output_events = graph.out_neighbors(event)

                if len(input_events) > 1:
                    for input in input_events:
                        graph.remove_edge(input, event)
                    graph.add_and_merge_gateway(input_events, event)

                if len(output_events) > 1:
                    for output in output_events:
                        graph.remove_edge(event, output)
                    graph.add_and_split_gateway(event, output_events)

    def get_self_loop_events(self):
        self_loop_events = set()
        for event_1, event_2 in self.parallel_events:
            if event_1 == event_2:
                self_loop_events.add(event_1)
        
        for self_event in self_loop_events:
            self.parallel_events.remove((self_event, self_event))

        return self_loop_events

    def add_self_loop(self, graph: MyGraph):
        for event in self.self_loop_events:
            if event in graph.nodes():
                successor = graph.successors(event)[0]
                graph.remove_edge(event, successor)
                graph.add_xor_split_gateway(event, [successor, event])


    # DRAWING A GRAPH

    def draw(self, G):
        self.add_start_events(G)
        self.add_end_events(G)
        self.add_single_edges(G)
        self.add_xor_split_pattern(G)
        self.add_xor_join_pattern(G)
        self.merge_multiple_edges(G)
        self.add_self_loop(G)


    ##########################################################################################
    #                                       FILTERING                                        #
    ##########################################################################################
            
    def build_based_on_direct_succession(self, direct_succession):
        self.direct_succession = direct_succession
        self.triangles = self.get_triangles_and_rombs()[0]
        self.rombs = self.get_triangles_and_rombs()[1]
        self.causality = self.get_causality()
        self.inv_causality = self.get_inv_causality()
        self.parallel_events = self.get_potential_parallelism()
        self.start_events = self.get_start_events()
        self.end_events = self.get_end_events()
        self.Xl = self.get_Xl()
        self.Yl = self.get_Yl()
        self.self_loop_events = self.get_self_loop_events()

    
    def apply_filter(self, nodes_to_delete, edges_to_delete):

        #### Update direct succession ####

        # Remove nodes from direct succession
        for node in nodes_to_delete:
            # Remove first element node
            try:
                del self.direct_succession[node]
            except KeyError:
                pass

            # Remove second element node
            for event in self.direct_succession.keys():
                try:
                    self.direct_succession[event].remove(node)
                except KeyError:
                    pass

        # Remove edges from direct succession
        for event_a, event_b in edges_to_delete:
            try:
                self.direct_succession[event_a].remove(event_b)
            except KeyError:
                pass

        
        #### Update triangles ####

        # Remove nodes from triangles
        triangles_to_delete = []
        for node in nodes_to_delete:
            for event_a, event_b in self.triangles:
                if node in [event_a, event_b]:
                    triangles_to_delete.append((event_a, event_b))
        for event_a, event_b in triangles_to_delete:
            self.triangles.remove((event_a, event_b))

        # Remove edges from triangles
        for event_a, event_b in edges_to_delete:
            if (event_a, event_b) in self.triangles:
                self.triangles.remove((event_a, event_b))
            if (event_b, event_a) in self.triangles:
                self.triangles.remove((event_b, event_a))

        
        #### Update rombs ####

        # Remove nodes from rombs
        rombs_to_delete = []
        for node in nodes_to_delete:
            for event_a, event_b in self.rombs:
                if node in [event_a, event_b]:
                    rombs_to_delete.append((event_a, event_b))
        for event_a, event_b in rombs_to_delete:
            self.rombs.remove((event_a, event_b))

        # Remove edges from rombs
        for event_a, event_b in edges_to_delete:
            if (event_a, event_b) in self.rombs:
                self.rombs.remove((event_a, event_b))
            if (event_b, event_a) in self.rombs:
                self.rombs.remove((event_b, event_a))

        # Update other relations
        self.causality = self.get_causality()
        self.inv_causality = self.get_inv_causality()
        self.parallel_events = self.get_potential_parallelism()
        self.start_events = {x for x in self.start_events if x not in nodes_to_delete}
        self.end_events = {x for x in self.end_events if x not in nodes_to_delete}
        self.Xl = self.get_Xl()
        self.Yl = self.get_Yl()

        # Remove self loops
        for event_a, event_b in edges_to_delete:
            if event_a == event_b and event_a in self.self_loop_events:
                self.self_loop_events.remove(event_a)
        for node in nodes_to_delete:
            if node in self.self_loop_events:
                self.self_loop_events.remove(node)

        



                




