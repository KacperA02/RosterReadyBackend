# importing constraint library to solve CSP problems
from constraint import *
# imporing datetime library to handle time calculations
import datetime
from datetime import timedelta
from typing import List, Dict
# RegenerateCSP class to handle the constraint satisfaction problem for shift assignments regeneration
class RegenerateCSP:
    # constructor to initialize the class with necessary parameters
    def __init__(self, users, shifts, user_availability, user_expertise, shift_expertise,shift_details, original_assignments, locked_assignments):
        # storing the parameters in instance variables
        self.users = users
        self.shifts = shifts
        self.user_availability = user_availability
        self.original_assignments = original_assignments
        self.locked_assignments = locked_assignments

        # user_expertise and shift_expertise are dictionaries mapping user_id and shift_id to their respective expertise
        self.user_expertise = {}
        for ue in user_expertise:
            self.user_expertise.setdefault(ue['user_id'], []).append(ue['expertise_id'])

        self.shift_expertise = {}
        for se in shift_expertise:
            self.shift_expertise.setdefault(se['shift_id'], []).append(se['expertise_id'])
            
        # storing shift details in a dictionary for easy access
        self.shift_details = {s['id']: s for s in shift_details}
        # creating a new problem instance
        self.problem = Problem()

        # Add variables to the problem
        self._initialize_variables()

        # Add constraints
        self._add_constraints()
    # initializing variables for the problem instance
    # This method adds variables to the problem instance.
    def _initialize_variables(self):
        # looping through each shift to add it as a variable in the problem instance
        for shift in self.shifts:
            key = (shift['shift_id'], shift['day_id'], shift['slot'])
            locked = shift.get('locked', False)
            # if the shift is locked, we find the user assigned to it and add it as a variable
            if locked:
                # finding the user assigned to the locked shift
                # using next to find the first matching assignment in locked_assignments 
                user = next((a['user_id'] for a in self.locked_assignments 
                             if a['shift_id'] == shift['shift_id'] and 
                                a['day_id'] == shift['day_id'] and 
                                a['slot'] == shift['slot']), None)
                # adding the variable with the user as the only possible value
                self.problem.addVariable(key, [user])
            # else finding all possible users who are not already assigned to the shift
            else:
                possible_users = [
                    u for u in self.users
                    if not any(u == ua['user_id'] and shift['day_id'] == ua['day_id'] 
                               for ua in self.user_availability)
                ]
                # adding the variable with all possible users as values
                self.problem.addVariable(key, possible_users)
                
    # adding constraints to the problem instance
    def _add_constraints(self):
        # looping through each shift to add constraints
        # This constraint ensures that only users with the required expertise can be assigned to a shift.
        for shift_key in self.problem._variables.keys():
            self.problem.addConstraint(
                lambda user, shift_key=shift_key: self._expertise_match(shift_key, user),
                (shift_key,)
            )

        # adding time gap constraint (ensuring at least 11 hours between shifts)
        self.problem.addConstraint(self._time_gap_constraint, list(self.problem._variables.keys()))
    # this is the function that checks if the user has the required expertise for the shift
    def _expertise_match(self, shift_key, user):
        shift_id = shift_key[0]
        required_expertise = self.shift_expertise.get(shift_id, [])
        user_expertise_ids = self.user_expertise.get(user, [])
        return any(e in user_expertise_ids for e in required_expertise) or not required_expertise
    # this function checks if the time gap between shifts is at least 11 hours
    def _time_gap_constraint(self, *assignments):
        user_last_shift = {}
        for shift_key, user in zip(self.problem._variables.keys(), assignments):
            if user is None:
                continue
            # Extracting shift details from the shift key
            # shift_key is a tuple (shift_id, day_id, slot)
            shift_id, day_id, slot = shift_key
            shift_info = self.shift_details.get(shift_id)
            # storing the start and end time of the shift
            start_time = shift_info['start']
            end_time = shift_info['end']
            # condition to check if the shift is locked
            if user in user_last_shift:
                _, last_start, last_end = user_last_shift[user]
                gap = self._calculate_time_difference(last_end, start_time)
                if gap < 11:
                    return False
            # 
            user_last_shift[user] = (shift_key, start_time, end_time)

        return True

    def _calculate_time_difference(self, start, end):
        fmt = "%H:%M"
        if isinstance(start, datetime.time):
            start = start.strftime(fmt)
        if isinstance(end, datetime.time):
            end = end.strftime(fmt)

        start_time = datetime.datetime.strptime(start, fmt)
        end_time = datetime.datetime.strptime(end, fmt)

        if end_time < start_time:
            end_time += timedelta(days=1)

        return (end_time - start_time).total_seconds() / 3600

    def _assignments_match(self, a1, a2):
        return a1['user_id'] == a2['user_id'] and a1['shift_id'] == a2['shift_id'] and \
               a1['day_id'] == a2['day_id'] and a1['slot'] == a2['slot']

    def solve(self):
        solutions = self.problem.getSolutions()
        if not solutions:
            return {
                "assignments": [],
                "total_solutions": 0,
                "changed_count": 0,
                "fallback_count": 0,
                "skipped_count": 0,
                "skipped_assignments": [],
                "failure_reasons": ["No valid shift assignments found"]
            }

        # Avoid identical solution
        valid_solutions = []
        for sol in solutions:
            if not self._is_same_as_original(sol):
                valid_solutions.append(sol)
        # if there are no valid solutions do no changes
        if not valid_solutions:
            return {
                "assignments": [],
                "total_solutions": len(solutions),
                "changed_count": 0,
                "fallback_count": 0,
                "skipped_count": 0,
                "skipped_assignments": [],
                "failure_reasons": ["All solutions matched original (no change)"]
            }
        # getting best solution which is the first in valid solution array
        best_solution = valid_solutions[0]
        # empty array to store formated solutions
        formatted = []
        # initalising changed count variable to 0
        changed_count = 0
        # looping through assignments in the best solutions and getting all locked items
        for (shift_id, day_id, slot), user in best_solution.items():
            locked = any(
                a['shift_id'] == shift_id and a['day_id'] == day_id and a['slot'] == slot and a['user_id'] == user
                for a in self.locked_assignments
            )
            # Finding the original assignment matching the current shift, day, and slot
            orig = next((a for a in self.original_assignments if 
                         a['shift_id'] == shift_id and a['day_id'] == day_id and a['slot'] == slot), None)
            # If an original assignment exists, the user has changed, and the slot is not locked, count it as a change
            if orig and user != orig['user_id'] and not locked:
                changed_count += 1
            # Adding the current assignment to the formatted list
            formatted.append({
                "user_id": user,
                "shift_id": shift_id,
                "day_id": day_id,
                "slot": slot,
                "locked": locked
            })

        formatted.sort(key=lambda x: (x["day_id"], x["shift_id"], x["slot"]))

        return {
            "assignments": formatted,
            "total_solutions": len(valid_solutions),
            "changed_count": changed_count,
            "fallback_count": 0,
            "skipped_count": 0,
            "skipped_assignments": [],
            "failure_reasons": [],
            "message": "New solution generated"
        }
    # Function to check whether a solution is identical to the original assignments
    def _is_same_as_original(self, solution_dict):
        # iterating through all original assignments
        for orig in self.original_assignments:
            key = (orig['shift_id'], orig['day_id'], orig['slot'])
            # If any assignment differs, return False
            if solution_dict.get(key) != orig['user_id']:
                return False
        # return true if all assignmetns match the original
        return True
