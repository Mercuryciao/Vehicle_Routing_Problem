import pandas as pd
import json
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
import vrp
import googlemap_api as gapi

Metaheuristic = False

class Vehicle():
    """Stores the property of a vehicle"""
    def __init__(self):
        """Initializes the vehicle properties"""
        self._capacity = 15

    @property
    def capacity(self):
        """Gets vehicle capacity"""
        return self._capacity

class Data():
    """Stores the data for the problem"""
    def __init__(self, distance_result, duration_result):
        """Initializes the data for the problem"""
        self._vehicle = Vehicle()
        self._num_vehicles = 6
        self._depot = 0
        self._demands = \
            [0,  # depot
             5, 5,  # row 0
             5, 5,
             5, 5,
             5, 5,
             5, 5,
             5, 5]
        self._distances = distance_result
        self._time = duration_result

    @property
    def vehicle(self):
        """Gets a vehicle"""
        return self._vehicle

    @property
    def num_vehicles(self):
        """Gets number of vehicles"""
        return self._num_vehicles

    @property
    def num_locations(self):
        """Gets number of locations"""
        return len(self._distances)

    @property
    def depot(self):
        """Gets depot location index"""
        return self._depot

    @property
    def demands(self):
        """Gets demands at each location"""
        return self._demands

    def distance_evaluator(self, from_node, to_node):
        """Returns the manhattan distance between the two nodes"""
        return self._distances[from_node][to_node]

    def time_evaluator(self, from_node, to_node):
        """Returns the manhattan distance between the two nodes"""
        return self._time[from_node][to_node]

def dataprocess(address):
    api_key = "AIzaSyBVEcOZSO74Ewbw1NuViK31zryGAyySL94"
    client = gapi.Client(api_key)
    address = address['address'].tolist()
    location_loc_list = []
    location_add_list = []
    for loc in address:
        location_loc_list.append(client.get_latlng(loc)[1])
        location_add_list.append(client.get_latlng(loc)[0])
    #print(location_loc_list)
    distance_result = client.to_metrix(location_loc_list, location_loc_list, mode="distance")
    #print(distance_result)
    duration_result = client.to_metrix(location_loc_list, location_loc_list, mode="duration")
    return location_add_list, location_loc_list, distance_result, duration_result

def json_loc_create(df_route, loc):
    json_loc = {}
    i = 1
    for each_route in df_route:
        loc_info = {'Route '+ str(i):{'start': {'lat': loc[0][0], 'lng': loc[0][1]},
                    'end': {'lat': loc[0][0], 'lng': loc[0][1]},
                    'waypts': [],
                    'travelMode': 'DRIVING'}}
        for j in each_route:
            loc_info['Route '+ str(i)]['waypts'].append({'location': {'lat': loc[j][0], 'lng': loc[j][1]}, 'stopover': True})
        json_loc.update(loc_info)
        i += 1
    #json_loc = json.dumps(json_loc)
    return json_loc

def json_add_create(df_route, loc):
    json_loc = {}
    i = 1
    for each_route in df_route:
        loc_info = {'Route '+ str(i):{'hub': loc[0],
                    'waypts': []}}
        for j in each_route:
            loc_info['Route '+ str(i)]['waypts'].append(loc[j])
        json_loc.update(loc_info)
        i += 1
    #json_loc = json.dumps(json_loc)
    return json_loc


def main():
    address = pd.read_excel('address_test.xlsx')
    location_add_list, location_loc_list, distance_result, duration_result = dataprocess(address)
    #print(location_add_list)
    data = Data(distance_result, duration_result)

    # Create Routing Model
    routing = pywrapcp.RoutingModel(data.num_locations, data.num_vehicles, data.depot)
    # Define weight of each edge
    distance_evaluator = data.distance_evaluator
    routing.SetArcCostEvaluatorOfAllVehicles(distance_evaluator)

    # Add Capacity constraint
    demand_evaluator = vrp.CreateDemandEvaluator(data).demand_evaluator
    vrp.add_capacity_constraints(routing, data, demand_evaluator)
    # Add Time Window constraint
    time_evaluator = data.time_evaluator
    vrp.add_time_window_constraints(routing, time_evaluator)

    # Setting first solution heuristic (cheapest addition)
    search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
    if not Metaheuristic:
        search_parameters.optimization_step = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    if Metaheuristic:
        search_parameters.solution_limit = 20
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)

    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)
    printer = vrp.ConsolePrinter(data, routing, assignment)
    df_route = printer.route_create()
    printer.print()
    json_loc = json_loc_create(df_route, location_loc_list)
    json_add = json_add_create(df_route, location_add_list)
    with open('loc.json', 'w') as fp:
        json.dump(json_loc, fp)
    with open('add.json', 'w', encoding='utf-8') as fp:
        json.dump(json_add, fp, ensure_ascii=False)

if __name__ == "__main__":
    main()
