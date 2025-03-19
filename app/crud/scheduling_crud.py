from sqlalchemy.orm import Session
from app.models import User, UserAvailability, Shift, Week
from app.association import day_shift_team, user_expertise, shift_expertise
from fastapi import HTTPException

def create_schedule(db: Session, team_id: int, week_id: int):
    # checking if week exists
    week = db.query(Week).filter(Week.id == week_id).first()
    if not week:
        raise HTTPException(status_code=404, detail="Week not found")
    # Get all users in the team (filter by team_id)
    users = db.query(User.id).filter(User.team_id == team_id).all()
    # Convert the list of tuples into a simple list of user IDs
    users = [user[0] for user in users] 
    
    # Get all day-shift pairs for the team (day_id, shift_id)
    shifts = db.query(day_shift_team.c.day_id, day_shift_team.c.shift_id).filter(
        day_shift_team.c.team_id == team_id
    ).all()

    # Get the availability of users (only approved availability entries)
    user_availability = db.query(UserAvailability.user_id, UserAvailability.day_id).filter(
        UserAvailability.team_id == team_id,
        UserAvailability.approved == True
    ).all()

    # Get shift information
    shift_details = db.query(
        Shift.id, Shift.time_start, Shift.time_end, Shift.no_of_users
    ).filter(Shift.team_id == team_id).all()

    # Get expertise data
    user_expertise_list = db.query(user_expertise.c.user_id, user_expertise.c.expertise_id).filter(
        user_expertise.c.user_id.in_(users)
    ).all()

    shift_ids = [shift[0] for shift in shift_details]  # Extract shift IDs
    shift_expertise_list = db.query(shift_expertise.c.shift_id, shift_expertise.c.expertise_id).filter(
        shift_expertise.c.shift_id.in_(shift_ids)
    ).all()

    #Expand domains based on the number of users required for each shift 
    expanded_shifts = []
    for shift in shifts:
        day_id, shift_id = shift
        # finding the corresponding shift id with in the many to many and the shift details
        shift_info = next((s for s in shift_details if s[0] == shift_id), None)
        
        # Extracting the number of required users for this shift 
        if shift_info:
            # Getting the num of users which is at index 3
            num_users_required = shift_info[3]  
            
            # Creating a new slot for every user needed
            for slot in range(num_users_required):
                expanded_shifts.append({
                    "day_id": day_id,
                    "shift_id": shift_id,
                    "slot": slot
                })

    # preparing the data to pass it to the csp
    request_data = {
        "users": users,
        "shifts": expanded_shifts,
        "shift_details": [{"id": shift[0], "start": shift[1], "end": shift[2], "users": shift[3]} for shift in shift_details],
        "user_availability": [{"user_id": ua[0], "day_id": ua[1]} for ua in user_availability],
        "shift_expertise": [{"shift_id": se[0], "expertise_id": se[1]} for se in shift_expertise_list],
        "user_expertise": [{"user_id": ue[0], "expertise_id": ue[1]} for ue in user_expertise_list],
    }

    # print(request_data)
    # # return
    # # Call the solver
    # solver = ShiftAssignmentSolver(
    #     request_data["users"],
    #     request_data["shifts"],
    #     request_data["shift_details"],
    #     request_data["user_availability"],
    #     request_data["user_expertise"],
    #     request_data["shift_expertise"]
    # )

    return request_data
