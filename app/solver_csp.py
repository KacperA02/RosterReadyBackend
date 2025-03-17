from constraint import *

class ShiftAssignmentSolver:
    def __init__(self, users, shifts, shift_details, user_availability, user_expertise, shift_expertise):
        # initalising solver with necessary details
        self.users = users
        self.shifts = shifts
        self.shift_details = shift_details
        self.user_availability = user_availability
        # converted these into dictionaries to access easier
        # Map user_id to a list of expertise_ids
        self.user_expertise = {}
        for user in user_expertise:
            if user['user_id'] not in self.user_expertise:
                self.user_expertise[user['user_id']] = []
            self.user_expertise[user['user_id']].append(user['expertise_id'])

        # Map shift_id to a list of expertise_ids
        self.shift_expertise = {}
        for shift in shift_expertise:
            if shift['shift_id'] not in self.shift_expertise:
                self.shift_expertise[shift['shift_id']] = []
            self.shift_expertise[shift['shift_id']].append(shift['expertise_id'])

        
        # Initialize the constraint satisfaction problem
        self.problem = Problem()

        # List to store unique shift-day-slot combinations
        shift_combinations = []
        
        # looping through each variable in shifts
        for shift in self.shifts:
            shift_id = shift['shift_id']
            day_id = shift['day_id']
            slot = shift['slot']
            
            #Created a unique identifier for each shift, day, and slot combination
            shift_key = (shift_id, day_id, slot)  
            
            # if the shift key is not in the shift combinations then we can append the shift key to a user
            if shift_key not in shift_combinations:
                shift_combinations.append(shift_key)
                # list of possible users
                possible_users = []

                # Loop to check if user is available basing of the user avaialbility
                for i, user in enumerate(self.users):
                    is_unavailable = any(
                        # checking if user is unavailable  of this day
                        user == ua['user_id'] and day_id == ua['day_id']  
                        for ua in self.user_availability
                    )
                    
                    # If the user is available, we add them to the list
                    if not is_unavailable:
                        possible_users.append(user)
                
                # printing for debugging 
                print(f"Possible users for shift {shift_id} on day {day_id}, slot {slot}: {possible_users}")  
                # printing for debugging 
                if not possible_users:
                    print(f" Warning: No available users for shift {shift_id} on day {day_id}, slot {slot}")
                
                # Added the shift's available users as a variable in the problem
                self.problem.addVariable(shift_key, possible_users)
        # calling constraints method to add all the rules
        self._add_constraints()

    def _add_constraints(self):
        
        # Expertise match constraint
        def expertise_match(shift_key, user):
            if user is None:
                return False
            # matching the correct col with a new variable
            shift_id = shift_key[0]
            # getting all shifts which have expertise
            required_expertise = self.shift_expertise.get(shift_id, [])
            # condition to check if no expertise is required, allow any user
            if not required_expertise:
                return True  
            # getting all the users expertises
            user_expertise_ids = self.user_expertise.get(user, [])

            # ensuring the user matches one of the expertises
            return any(expertise in user_expertise_ids for expertise in required_expertise)

        #Applying the constraint to each variable
        for shift_key in self.problem._variables.keys():
            self.problem.addConstraint(
                lambda user, shift_key=shift_key: expertise_match(shift_key, user), 
                (shift_key,)
            )
        
        # Max 1 shifts per day for each user
        def max_two_shifts_per_day(*assignments):
            # Dictionary to track how many shifts each user has on each day
            shift_counts = {} 
            
            # Looping over each shift assignment and to count them
            for shift_key, user in zip(self.problem._variables.keys(), assignments):
                if user is None:
                    # Skip None assignments (invalid assignments)
                    continue
                
                # Extract the day_id from the shift tuple
                day_id = shift_key[1]  
                
                # initialising a user count for that user
                if user not in shift_counts:
                    shift_counts[user] = {}
                
                # Count shifts for each user per day
                shift_counts[user][day_id] = shift_counts[user].get(day_id, 0) + 1

                # Reject the assignment if the user has more than 1 shift on the same day
                if shift_counts[user][day_id] > 1:
                    return False
            # returning true 
            return True

        # Apply the max_two_shifts_per_day constraint across all shifts
        self.problem.addConstraint(max_two_shifts_per_day, list(self.problem._variables.keys()))

        # Constraint to ensure balanced user distribution 
        def balanced_user_distribution(*assignments):
            user_counts = {user: 0 for user in self.users}

            for user in assignments:
                if user is not None:
                    user_counts[user] += 1
            
            # Ensure the difference between the user with the most shifts and the one with the least is not more than 1
            max_shifts = max(user_counts.values())
            min_shifts = min(user_counts.values())
            
            # Allow only small variation in assignments
            return max_shifts - min_shifts <= 1  
        # Applying the balanced_user_distribution constraint across all shifts
        self.problem.addConstraint(balanced_user_distribution, list(self.problem._variables.keys()))

    def solve(self):
        # Get all solutions for the problem (valid shift assignments)
        solutions = self.problem.getSolutions()
        
        if not solutions:
            # If no solutions exist, return an empty list and a message
            print(" No valid shift assignments found!")
            return {"assignments": [], "total_solutions": 0}

        formatted_solutions = []
        for solution in solutions:
            formatted_assignment = []
            for (shift_id, day_id, slot), user in solution.items():
                formatted_assignment.append({
                    "user_id": user,
                    "shift_id": shift_id,
                    "day_id": day_id,
                    "slot": slot
                })
            
            # Sort the assignments by `day_id`
            formatted_assignment.sort(key=lambda x: x["day_id"])
             # Add the sorted assignments to the list of formatted solutions
            formatted_solutions.append(formatted_assignment)

        return {
            "assignments": formatted_solutions,
            "total_solutions": len(solutions)
        }
