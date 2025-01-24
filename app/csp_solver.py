from constraint import Problem

class ShiftAssignmentSolver:
    # Initialising variables and domains
    def __init__(self, users, day_shift_team_data, user_availability):
        # list
        self.users = users
        # list of tuples  
        self.day_shift_team_data = day_shift_team_data 
        # set of tuples
        self.user_availability = user_availability
    
    def solve(self):
        problem = Problem()

        # had to build a dictionary to mao each day_id and shift_id to the users who are available
        availability_dict = {}
        # looped through set of tuples
        for day_id, shift_id, user_id, is_available in self.user_availability:
            # if they are marked avaialbe then the user is plaed in the list
            if is_available:
                if (day_id, shift_id) not in availability_dict:
                    availability_dict[(day_id, shift_id)] = []
                #Used the append method to add the user who is availbe to the availibility dictionary
                availability_dict[(day_id, shift_id)].append(user_id)

        # each day and shift is added as a variable into the csp 
        for day_shift in self.day_shift_team_data:
            if day_shift in availability_dict:
                # Uses the availbility dict to assign 
                problem.addVariable(day_shift, availability_dict[day_shift])
            else:
                # If no users are available, use an empty list
                problem.addVariable(day_shift, [])

        # As i wanted to implement that a user cant work more then 1 shit a day i had to group shifts by day
        day_shifts_dict = {}
        # I did this by looping and checking if the 
        for (day_id, shift_id) in self.day_shift_team_data:
            # it checks if the day id is not found in the dictionary it will dispay an empty array
            if day_id not in day_shifts_dict:
                day_shifts_dict[day_id] = []
            day_shifts_dict[day_id].append((day_id, shift_id))

        # adding the constraint making sure a user only works once a day (no double shifts in the same day)
        for day_id, shifts_for_day in day_shifts_dict.items():
            problem.addConstraint(self.unique_user_per_day_constraint, shifts_for_day)

        # then i get all possible solutions. The less variables and domains and more constraints would lead to no solutions.
        solutions = problem.getSolutions()

        # Returns the solutions
        return solutions

    # Constraint function to ensure no user is assigned to more than one shift on the same day 
    # *arg allows the method toaccept a variable number of arguments where in my case is user. A set in python would remove duplicate elements which means if a users id is seen multiple times it will remove them and keep one instance
    def unique_user_per_day_constraint(self, *args):
        # if the set and the len match it means the args are unique.
        return len(set(args)) == len(args)
