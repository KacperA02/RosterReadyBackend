# Importing constraint module to define and use csp problems
from constraint import *
# used for managing and comparing times between shifts
import datetime
from datetime import timedelta

# main csp solver class
# This class is responsible for solving the shift assignment problem using constraint satisfaction techniques.
class ShiftAssignmentSolver:
    # constructor method to initialize the solver with user and shift details
    def __init__(self, users, shifts, shift_details, user_availability, user_expertise, shift_expertise):
        # Storing the data passed to the class
        self.users = users
        self.shifts = shifts
        self.shift_details = shift_details
        self.user_availability = user_availability
        # organizing the data into a dictionary for easier access
        # This will map user IDs to a list of expertise IDs.
        # This will help in checking if a user has the required expertise for a shift.
        self.user_expertise = {}
        for user in user_expertise:
            if user['user_id'] not in self.user_expertise:
                self.user_expertise[user['user_id']] = []
            self.user_expertise[user['user_id']].append(user['expertise_id'])

        # organizing the shift expertise into a dictionary for easier access
        # This will map shift IDs to a list of expertise IDs required for that shift.
        self.shift_expertise = {}
        for shift in shift_expertise:
            if shift['shift_id'] not in self.shift_expertise:
                self.shift_expertise[shift['shift_id']] = []
            self.shift_expertise[shift['shift_id']].append(shift['expertise_id'])

        # Creating a new problem instance
        self.problem = Problem()

        # Adding all users as variables to the problem
        # The domain for each user is the list of shifts they can take.
        shift_combinations = []

        # Looping through all shifts to create a unique key for each shift, day, and slot combination
        for shift in self.shifts:
            shift_id = shift['shift_id']
            day_id = shift['day_id']
            slot = shift['slot']
            
            # Creating a unique key for the shift, day, and slot
            # This will help in identifying the specific shift assignment
            shift_key = (shift_id, day_id, slot)  

            # if the shift key is not already in the list, we add it
            # This ensures that we only add unique combinations of shifts, days, and slots
            if shift_key not in shift_combinations:
                shift_combinations.append(shift_key)
                possible_users = []

                # looping through all users to check their availability for the current shift
                for i, user in enumerate(self.users):
                    is_unavailable = any(
                        # Checking if user is unavailable for this day
                        user == ua['user_id'] and day_id == ua['day_id']  
                        for ua in self.user_availability
                    )
                    
                    # If the user is available, we add them to the list
                    if not is_unavailable:
                        possible_users.append(user)
                
                # Print for debugging
                print(f"Possible users for shift {shift_id} on day {day_id}, slot {slot}: {possible_users}")  
                # condition to check if no users are available for the shift
                if not possible_users:
                    print(f"Warning: No available users for shift {shift_id} on day {day_id}, slot {slot}")
                
                # adding the variable to the problem
                self.problem.addVariable(shift_key, possible_users)
        
        # Calling constraints method to add all the rules
        self._add_constraints()
        
    # This method adds constraints to the problem instance.
    def _add_constraints(self):
        # Expertise constraint
        # This constraint ensures that only users with the required expertise can be assigned to a shift.
        def expertise_match(shift_key, user):
            if user is None:
                return False
            # Extracting shift ID from the shift key
            shift_id = shift_key[0]
            # Getting all shifts which have expertise
            required_expertise = self.shift_expertise.get(shift_id, [])
            # Condition to check if no expertise is required, allow any user
            if not required_expertise:
                return True  
            # Getting all the users' expertise
            user_expertise_ids = self.user_expertise.get(user, [])
            # Ensuring the user matches one of the expertises
            return any(expertise in user_expertise_ids for expertise in required_expertise)

        # Applying the constraint to each variable
        for shift_key in self.problem._variables.keys():
            self.problem.addConstraint(
                lambda user, shift_key=shift_key: expertise_match(shift_key, user), 
                (shift_key,)
            )

        # Apply time gap constraint (ensuring at least 11 hours between shifts)
        self._add_time_gap_constraint()
    # This method adds a time gap constraint to the problem instance.
    def _add_time_gap_constraint(self):
        # Time gap constraint (ensuring there is a gap of at least 11 hours between shifts)
        # time_gap_constraint function checks the time difference between shifts assigned to the same user
        def time_gap_constraint(*assignments):
            # Store the last shift assignment for each user to compare against
            user_last_shift = {}
            # Loop through each shift key and its corresponding assignment
            for shift_key, user in zip(self.problem._variables.keys(), assignments):
                if user is None:
                    # Skip if the assignment is None (invalid assignment)
                    continue  
                # getting the shift ID, day ID, and slot from the shift key
                shift_id, day_id, slot = shift_key
                # next function to get the shift details
                # This will help in getting the start and end times of the shift
                shift_details = next(shift for shift in self.shift_details if shift['id'] == shift_id)
                # Extracting start and end times from the shift details
                start_time_str = shift_details['start']
                end_time_str = shift_details['end']

                # If the user has already been assigned a shift, check the time gap
                if user in user_last_shift:
                    last_shift_key, last_start_time_str, last_end_time_str = user_last_shift[user]
                    # time gap calculation to check the difference between the last end time and the current start time
                    time_gap = self.calculate_time_difference(last_end_time_str, start_time_str)

                    # If the gap is less than 11 hours, return False to reject the assignment
                    if time_gap < 11:
                        return False

                # storing the current shift assignment for the user
                user_last_shift[user] = (shift_key, start_time_str, end_time_str)
            # returning true if all assignments are valid
            return True

        # Apply the time gap constraint to all shift assignments
        self.problem.addConstraint(time_gap_constraint, list(self.problem._variables.keys()))
    # calculating the time difference between two time strings
    def calculate_time_difference(self, start_time, end_time):
        # format for the time strings
        # This format is used to parse the time strings into datetime objects
        time_format = "%H:%M"
        
        # If the time strings are in datetime.time format, convert them to string format
        # This ensures that the time strings are in the correct format for parsing
        if isinstance(start_time, datetime.time):
            start_time = start_time.strftime(time_format)
        if isinstance(end_time, datetime.time):
            end_time = end_time.strftime(time_format)
        # Parsing the time strings into datetime objects
        # This allows us to perform arithmetic operations on the time values
        start_time_obj = datetime.datetime.strptime(start_time, time_format)
        end_time_obj = datetime.datetime.strptime(end_time, time_format)
        # If the end time is earlier than the start time, add a day to the end time
        if end_time_obj < start_time_obj:
            end_time_obj += timedelta(days=1)
        # time difference calculation to get the difference in hours
        time_difference = (end_time_obj - start_time_obj).total_seconds() / 3600
        # returning the time difference in hours
        return time_difference
    # scoring the solution based on the number of repeated assignments
    def score_solution(self, solution: dict) -> int:
        shift_user_counts = {}
        # Loop through the solution to count the number of times each user is assigned to a shift
        # using shift_id and two blank values as keys
        for (shift_id, _, _), user in solution.items():
            key = (user, shift_id)
            # Increment the count for this user and shift ID
            shift_user_counts[key] = shift_user_counts.get(key, 0) + 1
        # Penalize repeated assignments
        repeat_penalty = sum(count - 1 for count in shift_user_counts.values() if count > 1)
        # return the penalty as the score
        return repeat_penalty
    # solve method to find the best solution
    def solve(self):
        # using the getSolutions method to find all possible solutions
        # This method returns a list of all valid assignments for the shifts
        solutions = self.problem.getSolutions()
        if not solutions:
            print("No valid shift assignments found!")
            return {"assignments": [], "total_solutions": 0}
        
        # scored solutions to sort the solutions based on their scores
        scored_solutions = sorted(solutions, key=self.score_solution)
        # best solution is the first one in the sorted list
        best_solution = scored_solutions[0]
        
        # Formatting the best solution for output
        # This will convert the solution into a more readable format
        formatted_assignment = []
        for (shift_id, day_id, slot), user in best_solution.items():
            formatted_assignment.append({
                "user_id": user,
                "shift_id": shift_id,
                "day_id": day_id,
                "slot": slot
            })
        # sorting the formatted assignment based on day_id
        formatted_assignment.sort(key=lambda x: x["day_id"])
        # returning the formatted assignment and the total number of solutions found
        return {
            "assignments": [formatted_assignment],
            "total_solutions": len(solutions)
        }
