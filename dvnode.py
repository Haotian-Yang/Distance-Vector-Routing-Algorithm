import copy
from math import inf
from dvsim import Packet, NUM_NODES

class Node:
    '''
    a node in the network
    '''
    def __init__(self, nodeid: int, simulator):
        '''
        Constructing a node in the network
        '''
        self.nodeid = nodeid        # nodeid is the node number
        self.simulator = simulator
        # print("Node ID", nodeid)
        # print("Costs", simulator.cost[nodeid])

        # simulator is passed here so that the node can access
        # - simulator.cost[nodeid] (only access the costs of this node's links) and
        # - simulator.to_link_layer(pkt) to send the message
        # You should not access anything else inside the simulator,

        # self.dist_table has the distance vectors as known by this node
        # It is an NxN matrix where N is NUM_NODES.
        # You need to make sure the dist_table is correctly updated throughout
        # the algorithm's execution.
        # Tip: although dist_table has N rows, each node might only access and
        # update a subset of the rows.
        self.dist_table = [[inf for _ in range(NUM_NODES)] for _ in range(NUM_NODES)]

        self.dist_table[nodeid] = copy.deepcopy(simulator.cost[nodeid])

        # list contains nodeid for all the neightbours
        self.neighbours_table = []

        # self.predessor is a list of int
        # self.predecessor keeps a list of the predecessor of this node in the
        # path to each of the other nodes in the graph
        # You need to make sure this predecessors list is correctly updated
        # throughout the algorithm's execution
        self.predecessors = [None for _ in range(NUM_NODES)]
        
        costs = self.simulator.cost[nodeid]
        print("--------%s---------" %(self.nodeid))
        print("Link costs", costs)
        self.predecessors[nodeid] = None
        for i in range(NUM_NODES):
            if i != self.nodeid and costs[i] != inf:
                self.predecessors[i] = i
                # add nodeid for all the neightbours
                self.neighbours_table.append(i)

        self.notifyNeighbours()

        self.print_dist_table()

        
        pass

    def get_link_cost(self, other):
        '''
        Get the cost of the link between this node and other.
        Note: This is the ONLY method that you're allowed use to get the cost of
        a link, i.e., do NOT access self.simulator.cost anywhere else in this
        class.
        DO NOT MODIFY THIS METHOD
        '''
        return self.simulator.cost[self.nodeid][other]

    def get_dist_vector(self):
        '''
        Get the distance vector of this node
        DO NOT MODIFY THIS METHOD
        '''
        return self.dist_table[self.nodeid]

    def get_predecessor(self, other: int) -> int:
        '''
        Get the predecessor of this node in the path to other
        DO NOT MODIFY THIS METHOD
        '''
        return self.predecessors[other]


    '''
    makePacket makes a packet that will be sent to the specified
    destination Node
    '''
    def makePacket(self, dst):
        pkt = Packet(self.nodeid, dst, self.get_dist_vector())
        return pkt


    '''
    notifyNeighbours will notify all the connected node
    '''
    def notifyNeighbours(self):
        print("------Notifying Neighbours-------")
        vec = self.get_dist_vector()
        for i in self.neighbours_table:
            pkt = self.makePacket(i)
            self.simulator.to_link_layer(pkt)

    def update(self, pkt: Packet):
        '''
        Handle updates when a packet is received. May need to call
        self.simulator.to_link_layer() with new packets based upon what after
        the update. Be careful to construct the source and destination of the
        packet correctly. Read dvsim.py for more details about the potential
        errors.
        '''
        # is essentially called when there is a update required
        # ie, there is new information
        # Basically, once we get a new dist-vector,
        # go through each of the nodes, and see if there is a shorter distance to it
        # based on the new distance vector that was received

        # Go through each of the costs in the incoming nodes
        print("-------NodeID: %s UPDATE-------" %(self.nodeid))

        #Updating the distance-table with the incoming vector
        src = pkt.get_src()
        srcVec = pkt.get_dist_vector()
        self.dist_table[src] = copy.deepcopy(srcVec)

        update = self.Bellman() # applying bellman algorithm to see if any changes can be made
        
        if update:
            print("Found Better Route")
            self.notifyNeighbours() # notify neighbours if there was an update
        print("--------END(%s)--------------" %(self.nodeid))


    def link_cost_change_handler(self, which_link: int, new_cost: int):
        '''
        Handles the link-change event. The cost of the link between this node
        and which_link has been changed to new_cost. Need to update the
        information that is stored at this node, and notify the neighbours if
        necessary.
        '''
        print("--------LinkChange(%s)--------" %(self.nodeid))
        print("neighbour: %s newCost: %s" %(which_link, new_cost))
        print("cost", self.simulator.cost[self.nodeid])
        self.print_dist_table()

        # if there is a new connection, ==> there is a new neighbour
        existingNeighbour = which_link in self.neighbours_table
        if  not existingNeighbour:
            # initialize neighbour in the distance-table
            self.neighbours_table.append(which_link)
            self.dist_table[which_link][self.nodeid] = new_cost
            self.dist_table[which_link][which_link] = 0
            # Check if the cost to the new neighbour is lower than what it is currently
            if (new_cost <= self.dist_table[self.nodeid][which_link]):
                self.dist_table[self.nodeid][which_link] = new_cost
                self.predecessors[which_link] = which_link
                self.notifyNeighbours()
            self.print_dist_table()
            # No need to apply bellman, since we don't have the dist-vec of the new neighbour
            return


        self.dist_table[self.nodeid][which_link] = new_cost
        if self.Bellman():
            self.notifyNeighbours()
            print("new update")
            self.print_dist_table()


    def Bellman(self):
        '''
        update the self distance vector
        return ture if there was update
        return false if no changes happend
        '''
        update = False
        # loop over all node and upate the distance vector
        for y in range(NUM_NODES):
            if y == self.nodeid:
                continue

            # find min to node y over all the neighbours
            oldDistance = self.dist_table[self.nodeid][y]
            curr_min = inf # Recalculating, so the initial min is inf
            curr_min_neighbour = None
            row = self.neighbours_table# + [self.nodeid]
            # Looping over neighbours
            for i in row:
                newDistance = self.get_link_cost(i) + self.dist_table[i][y]
                if newDistance < curr_min:
                    curr_min= newDistance
                    curr_min_neighbour = i

            # check if there is a change that needs to occur
            if oldDistance != curr_min:
                update = True

            # set new value to ditance vector
            self.dist_table[self.nodeid][y] = curr_min

            # if predecessor is itself set to None.
            if self.nodeid != curr_min_neighbour:
                self.predecessors[y] = curr_min_neighbour
            else:
                self.predecessors[y] = None
        self.print_dist_table()
        return update



    def print_dist_table(self):
        '''
        Prints the distance table stored at this node. Useful for debugging.
        DO NOT MODIFY THIS METHOD
        '''
        print(" D{}|".format(self.nodeid).rjust(5), end="")
        for i in range(NUM_NODES):
            print("    {}".format(i), end="")
        print("\n----+{}".format("-----"*NUM_NODES))
        for i in range(NUM_NODES):
            print("{:4d}|".format(i), end="")
            for j in range(NUM_NODES):
                print(str(self.dist_table[i][j]).rjust(5), end="")
            print()
