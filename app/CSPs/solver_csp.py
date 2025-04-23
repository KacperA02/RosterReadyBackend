# importing csp solver tools
from constraint import *
# for time handling
from datetime import datetime, timedelta
# for default dictionary behaviour
from collections import defaultdict
# for shuffling users different solution each time
import random

class ShiftAssignmentSolver:
    # construcing the solver with relevant variables needed for the solving
    def __init__(self, users, shifts, shift_details, user_availability, user_expertise, shift_expertise, max_days_per_user=5):
        self.users = users
        self.shifts = shifts
        self.shift_details = shift_details
        self.user_availability = user_availability
        # added this to make sure no user is working more then 5 days
        self.max_days_per_user = max_days_per_user
        # shuffling the users
        random.shuffle(self.users)

        # mapping user expertise to a dictionary, to allow csp to access
        self.user_expertise = defaultdict(list)
        for ue in user_expertise:
            self.user_expertise[ue['user_id']].append(ue['expertise_id'])
            
        # mapping shift_expertise to a dictionary, to allow csp to access
        self.shift_expertise = defaultdict(list)
        for se in shift_expertise:
            self.shift_expertise[se['shift_id']].append(se['expertise_id'])
        # looping through the shifts and converting start and end to datetime ranges
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
            # had to divide the seconds to get in hours
            sid: (end - start).total_seconds() / 3600.0
            for sid, (start, end) in self.shift_time_range.items()
        }
        
        # Mapping user to a set of unavailable days
        self.unavailable_map = defaultdict(set)
        for ua in self.user_availability:
            self.unavailable_map[ua['user_id']].add(ua['day_id'])
            
        # initialising the csp problem
        self.problem = Problem()
        # to hold all variable keys for the csp
        self.shift_keys = []
        # maps each shift key to original shift dictionary
        self.shift_map = {}  
        # loop to build the shift keys and maps to shift
        for shift in self.shifts:
            sid, day, slot = shift['shift_id'], shift['day_id'], shift['slot']
            key = (sid, day, slot)
            self.shift_keys.append(key)
            self.shift_map[key] = shift
            
        # sorting the shift key by day and start_time
        self.shift_keys.sort(key=lambda x: (x[1], self.shift_time_range[x[0]][0]))
        # assigning valid users for each shift variable
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
        # adding all constraints
        self._add_constraints()

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

                # only comparing days that are the day after
                # keeps from checking reduant shifts on other days
                if day2 != day1 + 1:
                    continue
                # getting the start date/time for comparison
                s1_start, s1_end = self.shift_time_range[id1]
                s2_start, s2_end = self.shift_time_range[id2]

                s1_start += timedelta(days=day1)
                s1_end += timedelta(days=day1)
                s2_start += timedelta(days=day2)
                s2_end += timedelta(days=day2)

                def no_conflict(u1, u2, s1=s1_start, e1=s1_end, s2=s2_start, e2=s2_end):
                    # if its two seperate users it will return true and assign
                    if u1 != u2:
                        return True
                    gap = timedelta(hours=11)
                    # must the gap between the end of the shift on day 1 must  be more then 11 hours legal amount
                    return e1 + gap <= s2 or e2 + gap <= s1
                
                # adding the constraint
                self.problem.addConstraint(no_conflict, (key1, key2))
        # constraint to check there was no double bookings on the same day
        # as in a user can only work one shift a day
        daily_keys = defaultdict(list)
        for key in self.shift_keys:
            daily_keys[key[1]].append(key)

        for day, keys in daily_keys.items():
            for i in range(len(keys)):
                for j in range(i + 1, len(keys)):
                    self.problem.addConstraint(lambda u1, u2: u1 != u2, (keys[i], keys[j]))

        # adding constraint to the problem
        self.problem.addConstraint(self._max_day_constraint, self.shift_keys)
    # this constrint makes sure a single user can only work a certain amount of days to ensure equal distribution
    def _max_day_constraint(self, *users):
        # Counting how many unique days each user is assigned
        user_day_count = defaultdict(set)
        for i, user in enumerate(users):
            _, day, _ = self.shift_keys[i]
            user_day_count[user].add(day)
            # returning true only if all users are within the day limit
        return all(len(days) <= self.max_days_per_user for days in user_day_count.values())

    def solve(self):
        # trying to find only a single solution
        solution = self.problem.getSolution()
        # if no solution provide return
        if not solution:
            print("No valid shift assignments found.")
            return {"assignments": [], "total_solutions": 0}
        # formating assignments
        assignments = [
            {"user_id": user, "shift_id": sid, "day_id": day, "slot": slot}
            for (sid, day, slot), user in solution.items()
        ]
        # sorting assignments by day_id
        assignments.sort(key=lambda x: x["day_id"])
        # return
        return {"assignments": [assignments], "total_solutions": 1}
