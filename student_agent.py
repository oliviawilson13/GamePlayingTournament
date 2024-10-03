# Student agent: Add your own agent here
from agents.agent import Agent
from store import register_agent
import sys
import numpy as np
from copy import deepcopy
import time


@register_agent("student_agent")
class StudentAgent(Agent):
    """
    A dummy class for your implementation. Feel free to use this class to
    add any helper functionalities needed for your agent.
    """

    def __init__(self):
        super(StudentAgent, self).__init__()
        self.name = "StudentAgent"
        self.dir_map = {
            "u": 0,
            "r": 1,
            "d": 2,
            "l": 3,
        }

    #check
    def check_reachable(self, start_pos, end_pos, adv_pos, max_step, chess_board):
        """
        Check if the step the agent takes is valid (reachable and within max steps).

        Parameters
        ----------
        start_pos : tuple
            The start position of the agent.
        end_pos : tuple THIS IS DIFF VARIABLE TYPE... CHECK WORKS
            The end position of the agent.
        adv_pos : tuple
            The position of the adversary.
        max_step : int
            Number of maximum allowed steps.
        chess_board : np.ndarray
            Shape of current board.
        """

        # Moves (Up, Right, Down, Left)
        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))

        # BFS
        state_queue = [(start_pos, 0)]
        visited = {tuple(start_pos)}
        is_reached = False
        while state_queue and not is_reached:
            cur_pos, cur_step = state_queue.pop(0)
            r, c = cur_pos
            if cur_step == max_step:
                break
            for dir, move in enumerate(moves):
                if chess_board[r, c, dir]:
                    continue

                #next_pos = cur_pos + move original code
                next_pos=tuple(np.add(cur_pos,move))
                if np.array_equal(next_pos, adv_pos) or tuple(next_pos) in visited:
                    continue
                if np.array_equal(next_pos, end_pos):
                    is_reached = True
                    break

                visited.add(tuple(next_pos))
                state_queue.append((next_pos, cur_step + 1))

        return is_reached

    #check
    def distance_adv(self, end_pos, adv_pos, chess_board):
        """
        Check how many steps to adv.

        Parameters
        ----------
        end_pos : tuple THIS IS DIFF VARIABLE TYPE... CHECK WORKS
            The end position of the agent.
        adv_pos : tuple
            The position of the adversary.
        chess_board : np.ndarray
            Shape of current board.
        """

        # Moves (Up, Right, Down, Left)
        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))

        # BFS
        state_queue = [(end_pos, 0)]
        visited = {tuple(end_pos)}
        is_reached = False
        while state_queue and not is_reached:
            cur_pos, cur_step = state_queue.pop(0)
            r, c = cur_pos
            for dir, move in enumerate(moves):
                if chess_board[r, c, dir]:
                    continue

                #next_pos = cur_pos + move original code
                next_pos=tuple(np.add(cur_pos,move))
                if tuple(next_pos) in visited:
                    continue
                if np.array_equal(next_pos, adv_pos):
                    is_reached = True
                    break

                visited.add(tuple(next_pos))
                state_queue.append((next_pos, cur_step + 1))

        return cur_step

    def step(self, chess_board, my_pos, adv_pos, max_step):
        """
        Implement the step function of your agent here.
        You can use the following variables to access the chess board:
        - chess_board: a numpy array of shape (x_max, y_max, 4)
        - my_pos: a tuple of (x, y)
        - adv_pos: a tuple of (x, y)
        - max_step: an integer

        You should return a tuple of ((x, y), dir),
        where (x, y) is the next position of your agent and dir is the direction of the wall
        you want to put on.

        Please check the sample implementation in agents/random_agent.py or agents/human_agent.py for more details.
        """

        start_time = time.time() #start timer

        #make a list of lists for each position away from adversary
        #max distance is (board_size * 2) -1 because can't occupy same space as adv.
        position_list = [[] for i in range((chess_board.shape[0]*2)-1)]

        r, c = adv_pos #get x,y coords of adversary

        #VERSION CHECKING FOR INDEX DIFFERENCES NOT SUMMED DIFFERENCES
        #make list of possible positions (i+1) moves away from adversary given current board/adv_pos
        #ignore reachability/walls for now
        for i in range(len(position_list)): #loop thru each sublist index (0 -> last)

            x_indices = np.array(range(r-(i+1),r+(i+1)+1)) #only include possible x-values for this distance from adv
            x_indices=list(x_indices[(x_indices >= 0) & (x_indices < chess_board.shape[0])]) #remove x_values off board
            y_indices = np.array(range(c-(i+1),c+(i+1)+1)) #same list logic for y-values
            y_indices=list(y_indices[(y_indices >= 0) & (y_indices < chess_board.shape[0])])

            while x_indices: #while indices left in list (ie. not tested yet)
                x_value = x_indices.pop() #remove from list when tested

                x_diff = abs(x_value-r) #calc rows away from adv

                #check this x value against each y value
                for y_value in y_indices:
                    y_diff = abs(y_value-c) #calc columns away from adv

                    #row & column changes added together must = distance from adv for this sublist
                    if x_diff + y_diff == (i+1):
                        position_list[i].append((x_value, y_value)) #append each possible position


        #initiallize variables
        #assign to impossible values
        pos_choice = (-1,-1)
        dir = -1
      

        #initialize ordered dictionary of positions/distances
        position_ranking = {}
        #key: (position, dir) -> ((),int)
        #value: distance to adv (what we want to order by)
        reachable_list = []

        #loop through each possible end position, starting with closest to to adversary
        #(start closest to adversay bc prefer ending near adversary to trap)
        for sublist in position_list:
            for end_pos in sublist: #loop through each tuple of positions

                #check whether end_pos reachable with current pos, max steps, & current walls and store boolean
                reachable = self.check_reachable(my_pos, end_pos, adv_pos, max_step, chess_board)

                if not reachable: continue #skip this loop iteration, try next best position in list

                reachable_list.append(end_pos)

                #get x,y coords for goal position
                r_self, c_self = end_pos

                #check barrier dir possibilities, any direction such that chess_board is False
                allowed_barriers=[i for i in range(0,4) if not chess_board[r_self,c_self,i]]

                if len(allowed_barriers) < 3: #don't want to trap self or allow adv to trap on next move
                    continue #so if trapping, move on to next position in sublist
                else:
                    #now, check if can place between us & adversary (to achieve trapping goal)
                    #r,c is adversary coords
                    if r >= r_self: # adv is below us or same x_axis (no up/down)
                        #trim placing a wall up
                        if 0 in allowed_barriers: allowed_barriers.remove(0)
                    if r <= r_self: #adv is above us or same
                        #trim placing a wall down
                        if 2 in allowed_barriers: allowed_barriers.remove(2)
                    if c >= c_self: # adv is to the right of us or same y_axis
                        #trim placing a wall left
                        if 3 in allowed_barriers: allowed_barriers.remove(3)
                    if c <= c_self: #adv is to the left of us or same
                        #trim placing a wall right
                        if 1 in allowed_barriers: allowed_barriers.remove(1)

                    if len(allowed_barriers) >0:
                        #choose any allowed dir bc we aren't trapping ourself and only dir left are between us/adv
                        #add end_pos and dir as a key in the position_ranking dictionary
                        dir = allowed_barriers[np.random.randint(0, len(allowed_barriers))]
                        position_ranking[(end_pos,dir)] = 0 #start all with 0 value

        #ADD POSSIBLE POS_CHOICES TO LIST
        #ORDER LIST FROM LEAST MOVES TO ADV (CALC BY BFS) TO MOST
        min_steps = 144
        for position in position_ranking:
            steps = self.distance_adv(position[0], adv_pos, chess_board)
            position_ranking[position] = steps
            if steps<min_steps:
                min_steps = steps
                pos_choice=position[0]
                dir = position[1]

        #DUMMY CHECK 1
        if pos_choice == (-1,-1):
            #loop through each possible end position, starting with closest to adversary
            #(start closest to adversay bc prefer ending near adversary to trap)
            for end_pos in reachable_list:
                #get x,y coords for goal position
                r_self, c_self = end_pos

                #check barrier dir possibilities, any direction such that chess_board is False
                allowed_barriers=[i for i in range(0,4) if not chess_board[r_self,c_self,i]]

                if len(allowed_barriers) < 3: #don't want to trap self or allow adv to trap on next move
                    continue #so if trapping, move on to next position in sublist
                else:
                    dir = allowed_barriers[np.random.randint(0, len(allowed_barriers))]
                    pos_choice = end_pos
                    break

        #DUMMY CHECK 2
        if pos_choice == (-1,-1):
            #loop through each possible end position, starting with closest to adversary
            #(start closest to adversay bc prefer ending near adversary to trap)
            for end_pos in reachable_list:
                #get x,y coords for goal position
                r_self, c_self = end_pos

                #check barrier dir possibilities, any direction such that chess_board is False
                allowed_barriers=[i for i in range(0,4) if not chess_board[r_self,c_self,i]]

                if len(allowed_barriers) < 2: #don't want to trap self
                    continue #so if trapping, move on to next position in sublist
                else:
                    dir = allowed_barriers[np.random.randint(0, len(allowed_barriers))]
                    pos_choice = end_pos
                    break

        #DUMMY CHECK 3
        if pos_choice == (-1,-1):
            pos_choice = my_pos
            dir = 0

        # print overall time
        time_taken = time.time() - start_time
        #print("My AI's turn took ", time_taken, "seconds.")

        # return the variables
        return pos_choice, dir
