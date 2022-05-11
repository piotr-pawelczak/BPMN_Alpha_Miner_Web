from winreg import ExpandEnvironmentStrings
import pandas as pd
from collections import Counter
from more_itertools import pairwise
import pygraphviz as pgv
from IPython.display import Image, display

class Filter:

    def __init__(self, logs) -> None:
        self.logs = logs
        self.ev_counter = self.get_event_count()
        self.traces = self.get_traces()
        self.w_net = self.get_workflow_net()[0]
        self.ev_start_set = self.get_workflow_net()[1]
        self.ev_end_set = self.get_workflow_net()[2]
        self.self_loop_events = self.get_self_loop_events()
        self.graph = self.create_graph()


    def get_event_count(self):
        ev_counter = self.logs.Activity.value_counts()
        return ev_counter


    def get_traces(self):
        # Group activities by case id
        traces = (self.logs
            .sort_values(by=['Case ID','Start Timestamp'])
            .groupby(['Case ID'])
            .agg({'Activity': ';'.join})
        )

        # Group duplicate traces
        traces['count'] = 0
        traces = (
            traces.groupby('Activity', as_index=False).count()
            .sort_values(['count'], ascending=False)
            .reset_index(drop=True)
        )

        # Create list of activities in trace
        traces['trace'] = [trace.split(';') for trace in traces['Activity']]
        
        return traces

    
    def get_workflow_net(self):
        w_net = dict()
        ev_start_set = set()
        ev_end_set = set()
        for index, row in self.traces[['trace','count']].iterrows():
            if row['trace'][0] not in ev_start_set:
                ev_start_set.add(row['trace'][0])
            if row['trace'][-1] not in ev_end_set:
                ev_end_set.add(row['trace'][-1])
            for ev_i, ev_j in pairwise(row['trace']):
                if ev_i not in w_net.keys():
                    w_net[ev_i] = Counter()
                w_net[ev_i][ev_j] += row['count']
        return w_net, ev_start_set, ev_end_set


    def create_graph(self):
        G = pgv.AGraph(strict= False, directed=True)
        G.graph_attr['rankdir'] = 'LR'
        G.node_attr['shape'] = 'Mrecord'

        G.add_node("start", shape="circle", label="")
        for ev_start in self.ev_start_set:
            G.add_edge("start", ev_start)

        for event, succesors in self.w_net.items(): 
            value = self.ev_counter[event]
            G.add_node(event, style="rounded,filled", label=f'{event} - {value}')

            for succesor, cnt in succesors.items():
                if event != succesor:
                    G.add_edge(event, succesor, label=cnt)

        G.add_node("end", shape="circle", label="", penwidth='3')
        for ev_end in self.ev_end_set:
            G.add_edge(ev_end, "end")
        return G


    def get_self_loop_events(self):
        self_loop_events = dict()
        for event in self.w_net.keys():
            successors = self.w_net[event].keys()
            for successor in successors:
                if successor == event:
                    self_loop_events[successor] = self.w_net[successor][successor]
        return self_loop_events


    def plot_graph(self):
        self.graph.draw('simple_heuristic_net_with_events.png', prog='dot')
        display(Image('simple_heuristic_net_with_events.png'))

    
    def filter_edges(self, edge_treshold=0):
        
        edges = self.graph.edges()
        nodes = self.graph.nodes()
        nodes.remove('start')
        nodes.remove('end')

        restricted_edges = []
        edges_to_delete = []

        for node in nodes:
            if node not in self.ev_start_set:
                input_edges = list(filter(lambda edge: edge[1] == node, edges))
            else:
                input_edges = []
            output_edges = list(filter(lambda edge: edge[0] == node, edges))

            input_edges_weight = {edge:self.w_net[edge[0]][edge[1]] for edge in input_edges if edge[0] not in self.ev_end_set}
            output_edges_weight = {edge:self.w_net[edge[0]][edge[1]] for edge in output_edges if edge[0] not in self.ev_end_set}

            if input_edges_weight:
                max_input = max(input_edges_weight, key=input_edges_weight.get)
                restricted_edges.append(max_input)
            if output_edges_weight:
                max_output = max(output_edges_weight, key=output_edges_weight.get)
                restricted_edges.append(max_output)

        restricted_edges = set(restricted_edges)

        for event, succesors in self.w_net.items():
            for succesor, cnt in succesors.items():
                if ((event, succesor) not in restricted_edges and cnt < edge_treshold and
                    event in self.graph.nodes() and succesor in self.graph.nodes() and (event, succesor) in self.graph.edges()):
                    self.graph.delete_edge(event, succesor)
                    edges_to_delete.append((event, succesor))

        for event, cnt in self.self_loop_events.items():
            if cnt < edge_treshold:
                edges_to_delete.append((event, event))
        return edges_to_delete


    def filter_nodes(self, node_treshold=0):
        nodes = self.graph.nodes()
        nodes.remove('end')
        nodes_to_delete = []

        for node in self.graph.nodes():
            if node not in ['start', 'end']:
                value = self.ev_counter[node]
                if value < node_treshold:
                    G_temp = self.graph.copy()
                    G_temp.delete_node(node)

                    graph_crashed = False
                    for new_node in G_temp.nodes():
                        if new_node == 'end':
                            if G_temp.in_neighbors(new_node) == []:
                                graph_crashed = True
                        elif new_node == 'start':
                            if G_temp.out_neighbors(new_node) == []:
                                graph_crashed = True
                        else:
                            if G_temp.out_neighbors(new_node) == [] or G_temp.in_neighbors(new_node) == []:
                                graph_crashed = True
                            elif G_temp.out_neighbors(new_node) == G_temp.in_neighbors(new_node):
                                graph_crashed = True

                    if graph_crashed == False:
                        self.graph.delete_node(node)
                        nodes_to_delete.append(node)
        return nodes_to_delete


    def filter_graph(self, node_treshold=0, edge_treshold=0):
        self.graph = self.create_graph()
        nodes_to_delete = self.filter_nodes(node_treshold)
        edges_to_delete = self.filter_edges(edge_treshold)
        return nodes_to_delete, edges_to_delete
