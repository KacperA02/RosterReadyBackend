# importing constraint library to solve CSP problems
from constraint import *
# imporing datetime library to handle time calculations
import datetime
from datetime import datetime, time, timedelta
from collections import defaultdict
from itertools import islice
# RegenerateCSP class to handle the constraint satisfaction problem for shift assignments regeneration
class RegenerateCSP:
    def __init__(self, users, shifts, user_availability, user_expertise, shift_expertise, shift_details, original_assignments, locked_assignments, max_days_per_user=5):
        # storing the parameters in instance variables
        self.users = users
        self.shifts = shifts
        self.shift_details = shift_details
        self.user_availability = user_availability
        self.original_assignments = original_assignments
        self.locked_assignments = locked_assignments
        self.max_days_per_user = max_days_per_user

        # user_expertise and shift_expertise are dictionaries mapping user_id and shift_id to their respective expertise
        self.user_expertise = defaultdict(list)
        for ue in user_expertise:
            self.user_expertise[ue['user_id']].append(ue['expertise_id'])

        self.shift_expertise = defaultdict(list)
        for se in shift_expertise:
            self.shift_expertise[se['shift_id']].append(se['expertise_id'])

        self.shift_time_range = {}
        
        for shift in self.shift_details:
            shift_id = shift['id']
            start = shift['start']
            end = shift['end']
            # Converting to datetime if its a string or combining if already datetime.time
            start = datetime.strptime(start, "%H:%M") if isinstance(start, str) else datetime.combine(datetime.today(), start)
            end = datetime.strptime(end, "%H:%M") if isinstance(end, str) else datetime.combine(datetime.today(), end)
            # Adjustment for overnight shifts
            if end <= start:
                # adding the day by one if its overnight
                end += timedelta(days=1)
            self.shift_time_range[shift_id] = (start, end)
            
        # Calculating how long each shift lasts (in hours)
        self.shift_duration = {
            sid: (end - start).total_seconds() / 3600.0
            for sid, (start, end) in self.shift_time_range.items()
        }

        self.unavailable_map = defaultdict(set)
        for ua in self.user_availability:
            self.unavailable_map[ua['user_id']].add(ua['day_id'])

        # creating a new problem instance
        self.problem = Problem()
        # to hold all variable keys for the csp
        self.shift_keys = set()  # Changed to a set to ensure uniqueness
        # maps each shift key to original shift dictionary
        self.shift_map = {}  
        # loop to build the shift keys and maps to shift
        for shift in self.shifts:
            sid, day, slot = shift['shift_id'], shift['day_id'], shift['slot']
            key = (sid, day, slot)
            if key not in self.shift_keys:
                self.shift_keys.add(key)  # Ensures no duplicate keys
                self.shift_map[key] = shift

        # sorting the shift key by day and start_time
        self.shift_keys = sorted(self.shift_keys, key=lambda x: (x[1], self.shift_time_range[x[0]][0]))

        # Assign valid users for each shift variable
        for key in self.shift_keys:
            sid, day, slot = key
            duration = self.shift_duration[sid]
            required_exp = set(self.shift_expertise[sid])
            valid_users = []
            # loop through users and check if the user is unavailable that day
            for user in self.users:
                if day in self.unavailable_map[user]:
                    continue
                # checking if the shift needs expertise
                if required_exp and not any(e in self.user_expertise[user] for e in required_exp):
                    continue
                # appending valid users
                valid_users.append(user)
            # adding the valid users as domains
            self.problem.addVariable(key, valid_users)

        # Add variables to the problem
        self._initialize_variables()

        # Add constraints
        self._add_constraints()

    def _initialize_variables(self):
    # looping through each shift to add it as a variable in the problem instance
        for shift in self.shifts:
            key = (shift['shift_id'], shift['day_id'], shift['slot'])
            locked = shift.get('locked', False)
            
            # Skip if the variable for this shift already exists
            if key in self.problem._variables:
                continue  # If the shift key is already in the CSP, skip it
            
            # if the shift is locked, we find the user assigned to it and add it as a variable
            if locked:
                # finding the user assigned to the locked shift
                # using next to find the first matching assignment in locked_assignments 
                user = next((a['user_id'] for a in self.locked_assignments 
                            if a['shift_id'] == shift['shift_id'] and 
                                a['day_id'] == shift['day_id'] and 
                                a['slot'] == shift['slot']), None)
                if user is not None:
                    # directly assign the user to the shift if locked
                    self.problem.addVariable(key, [user])  # Locked shifts get only one possible user
            else:
                possible_users = [
                    u for u in self.users
                    if not any(u == ua['user_id'] and shift['day_id'] == ua['day_id'] 
                            for ua in self.user_availability)
                ]
                # adding the variable with all possible users as values
                self.problem.addVariable(key, possible_users)


    def _add_constraints(self):
        # user must match required expertise
        def expertise_match(shift_key, user):
            # getting the required expertise
            required = self.shift_expertise.get(shift_key[0], [])
            # getting the user expertise
            user_exps = self.user_expertise.get(user, [])
            # checking if they match
            return not required or any(exp in user_exps for exp in required)

        # applying the constraint to each shift
        for shift_key in self.shift_keys:
            self.problem.addConstraint(lambda user, sk=shift_key: expertise_match(sk, user), (shift_key,))

        # constraint to stop users working double shifts or a day shift after night shift
        for i in range(len(self.shift_keys)):
            key1 = self.shift_keys[i]
            id1, day1, _ = key1
            for j in range(i + 1, len(self.shift_keys)):
                key2 = self.shift_keys[j]
                id2, day2, _ = key2

                if day2 != day1 + 1:
                    continue
                s1_start, s1_end = self.shift_time_range[id1]
                s2_start, s2_end = self.shift_time_range[id2]

                s1_start += timedelta(days=day1)
                s1_end += timedelta(days=day1)
                s2_start += timedelta(days=day2)
                s2_end += timedelta(days=day2)

                def no_conflict(u1, u2, s1=s1_start, e1=s1_end, s2=s2_start, e2=s2_end):
                    if u1 != u2:
                        return True
                    gap = timedelta(hours=11)
                    return e1 + gap <= s2 or e2 + gap <= s1

                self.problem.addConstraint(no_conflict, (key1, key2))

        daily_keys = defaultdict(list)
        for key in self.shift_keys:
            daily_keys[key[1]].append(key)

        for day, keys in daily_keys.items():
            for i in range(len(keys)):
                for j in range(i + 1, len(keys)):
                    self.problem.addConstraint(lambda u1, u2: u1 != u2, (keys[i], keys[j]))

        self.problem.addConstraint(self._max_day_constraint, self.shift_keys)

    def _max_day_constraint(self, *users):
        user_day_count = defaultdict(set)
        for i, user in enumerate(users):
            _, day, _ = self.shift_keys[i]
            user_day_count[user].add(day)
        return all(len(days) <= self.max_days_per_user for days in user_day_count.values())

    def solve(self):
        solutions = self.problem.getSolutionIter()
        limited_solutions = list(islice(solutions, 5))

        if not limited_solutions:
            return {
                "assignments": [],
                "total_solutions": 0,
                "changed_count": 0,
                "fallback_count": 0,
                "skipped_count": 0,
                "skipped_assignments": [],
                "failure_reasons": ["No valid shift assignments found"]
            }

        best_solution = None
        max_changes = -1

        for sol in limited_solutions:
            changes = 0
            for (shift_id, day_id, slot), user in sol.items():
                locked = any(
                    a['shift_id'] == shift_id and a['day_id'] == day_id and a['slot'] == slot and a['user_id'] == user
                    for a in self.locked_assignments
                )
                if locked:
                    continue
                orig = next((a for a in self.original_assignments if 
                            a['shift_id'] == shift_id and a['day_id'] == day_id and a['slot'] == slot), None)
                if orig and user != orig['user_id']:
                    changes += 1
            
            if not self._is_same_as_original(sol):
                if changes > max_changes:
                    best_solution = sol
                    max_changes = changes

        if not best_solution:
            return {
                "assignments": [],
                "total_solutions": len(limited_solutions),
                "changed_count": 0,
                "fallback_count": 0,
                "skipped_count": 0,
                "skipped_assignments": [],
                "failure_reasons": ["All solutions matched original (no change)"]
            }

        formatted = []
        changed_count = 0
        for (shift_id, day_id, slot), user in best_solution.items():
            locked = any(
                a['shift_id'] == shift_id and a['day_id'] == day_id and a['slot'] == slot and a['user_id'] == user
                for a in self.locked_assignments
            )
            orig = next((a for a in self.original_assignments if 
                        a['shift_id'] == shift_id and a['day_id'] == day_id and a['slot'] == slot), None)
            if orig and user != orig['user_id'] and not locked:
                changed_count += 1
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
            "total_solutions": len(limited_solutions),
            "changed_count": changed_count,
            "fallback_count": 0,
            "skipped_count": 0,
            "skipped_assignments": [],
            "failure_reasons": [],
            "message": "New solution generated (best of 5 with max changes)"
        }

    def _is_same_as_original(self, solution_dict):
        for orig in self.original_assignments:
            key = (orig['shift_id'], orig['day_id'], orig['slot'])
            if solution_dict.get(key) != orig['user_id']:
                return False
        return True
