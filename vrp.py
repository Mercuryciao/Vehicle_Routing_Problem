"""Capacitated Vehicle Routing Problem"""
from __future__ import print_function
from six.moves import xrange
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2


# Problem Data Definition
class CreateDemandEvaluator(object):  # pylint: disable=too-few-public-methods
    """Creates callback to get demands at each location."""

    def __init__(self, data):
        """Initializes the demand array."""
        self._demands = data.demands

    def demand_evaluator(self, from_node, to_node):
        """Returns the demand of the current node"""
        del to_node
        return self._demands[from_node]


def add_capacity_constraints(routing, data, demand_evaluator):
    """Adds capacity constraint"""
    capacity = "Capacity"
    routing.AddDimension(
        demand_evaluator,
        0,  # null capacity slack
        data.vehicle.capacity,  # vehicle maximum capacity
        True,  # start cumul to zero
        capacity)

def add_time_window_constraints(routing, time_evaluator):
    """Add Global Span constraint"""
    time = "Time"
    horizon = 4200 # second
    routing.AddDimension(
        time_evaluator,
        horizon, # allow waiting time
        horizon, # maximum time per vehicle
        False, # don't force start cumul to zero since we are giving TW to start nodes
        time)


# Printer
class ConsolePrinter():
    """Print solution to console"""

    def __init__(self, data, routing, assignment):
        """Initializes the printer"""
        self._data = data
        self._routing = routing
        self._assignment = assignment

    @property
    def data(self):
        """Gets problem data"""
        return self._data

    @property
    def routing(self):
        """Gets routing model"""
        return self._routing

    @property
    def assignment(self):
        """Gets routing model"""
        return self._assignment

    def print(self):
        capacity_dimension = self.routing.GetDimensionOrDie('Capacity')
        time_dimension = self.routing.GetDimensionOrDie('Time')
        total_dist = 0
        total_time = 0
        for vehicle_id in xrange(self.data.num_vehicles):
            index = self.routing.Start(vehicle_id)
            plan_output = 'Route for vehicle {0}:\n'.format(vehicle_id)
            route_dist = 0
            while not self.routing.IsEnd(index):
                node_index = self.routing.IndexToNode(index)
                next_node_index = self.routing.IndexToNode(
                    self.assignment.Value(self.routing.NextVar(index)))
                route_dist += self.data.distance_evaluator(node_index, next_node_index)
                load_var = capacity_dimension.CumulVar(index)
                route_load = self.assignment.Value(load_var)
                time_var = time_dimension.CumulVar(index)
                time_min = self.assignment.Min(time_var)
                time_max = self.assignment.Max(time_var)
                # slack_min = self.assignment.Min(slack_var)#problem
                # slack_max = self.assignment.Max(slack_var)

                plan_output += ' {0} Load({1}) Time({2},{3}) ->'.format(
                    node_index,
                    route_load,
                    time_min, time_max)
                # slack_min, slack_max)
                index = self.assignment.Value(self.routing.NextVar(index))

            node_index = self.routing.IndexToNode(index)
            load_var = capacity_dimension.CumulVar(index)
            route_load = self.assignment.Value(load_var)
            time_var = time_dimension.CumulVar(index)
            route_time = self.assignment.Value(time_var)
            time_min = self.assignment.Min(time_var)
            time_max = self.assignment.Max(time_var)
            total_dist += route_dist
            total_time += route_time
            plan_output += ' {0} Load({1}) Time({2},{3})\n'.format(node_index, route_load, time_min, time_max)
            plan_output += 'Distance of the route: {0}m\n'.format(route_dist)
            plan_output += 'Load of the route: {0}\n'.format(route_load)
            plan_output += 'Time of the route: {0}min\n'.format(route_time//60)
            print(plan_output)
        print('Total Distance of all routes: {0}m'.format(total_dist))
        print('Total Time of all routes: {0}min'.format(total_time//60))

    def route_create(self):
        total_dist = 0
        df_route = []

        for vehicle_id in xrange(self.data.num_vehicles):
            index = self.routing.Start(vehicle_id)
                #plan_output = 'Route for vehicle {0}:\n'.format(vehicle_id)
            #route_load = 0
            df_each_route = []
            while not self.routing.IsEnd(index):
                node_index = self.routing.IndexToNode(index)
                #next_node_index = self.routing.IndexToNode(
                #    self.assignment.Value(self.routing.NextVar(index)))
                #route_dist = self.data.distance_evaluator(node_index, next_node_index)
                #print([vehicle_id, node_index, next_node_index])
                if node_index == 0:
                    pass
                else:
                    df_each_route.append(node_index)
                    # route_dist += manhattan_distance(
                    #    self.data.locations[node_index],
                    #    self.data.locations[next_node_index])
                #route_load += self.data.demands[node_index]
                    #plan_output += ' {0} Load({1}) -> '.format(node_index, route_load)
                index = self.assignment.Value(self.routing.NextVar(index))

            node_index = self.routing.IndexToNode(index)
            df_route.append(df_each_route)
        df_route = [x for x in df_route if x != []]
        return df_route



# Main
def main():
    """Entry point of the program"""
    data = DataProblem()

    # Create Routing Model
    routing = pywrapcp.RoutingModel(data.num_locations, data.num_vehicles, data.depot)
    # Define weight of each edge
    distance_evaluator = data.distance_evaluator
    routing.SetArcCostEvaluatorOfAllVehicles(distance_evaluator)

    # Add Capacity constraint
    demand_evaluator = CreateDemandEvaluator(data).demand_evaluator
    add_capacity_constraints(routing, data, demand_evaluator)
    # Add Time Window constraint
    time_evaluator = data.time_evaluator
    add_time_window_constraints(routing, time_evaluator)

    # Setting first solution heuristic (cheapest addition).

    search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    #search_parameters.time_limit_ms = 30000
    #search_parameters.local_search_metaheuristic = (
    #    routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH)


    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)
    printer = ConsolePrinter(data, routing, assignment)
    printer.print()
    #print("Solver status: ", solver.status())


if __name__ == '__main__':
    main()
