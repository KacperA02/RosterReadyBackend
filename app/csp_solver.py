from constraint import Problem

class ShiftAssignmentSolver:
    # intialising the varailbes and domains
    def __init__(self, users, day_shift_team_data):
        # users in this case is an array
        self.users = users
        # day_shift_team_data is a list of tuples which represents day and shift pair
        self.day_shift_team_data = day_shift_team_data

    def solve(self):
        # the problem() defines the variables and constraints to solve the problem
        problem = Problem()
        # loop throughs each pair and adds it as a variable where the users are possible values
        for day_shift in self.day_shift_team_data:
            problem.addVariable(day_shift, self.users)

        # Generates all possible solutions
        solutions = problem.getSolutions()
        # then returning the solutions
        return solutions
