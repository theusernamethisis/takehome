from datetime import datetime, timedelta, date, time
from collections import defaultdict
from faker import Faker
import random
import json
import math

fake = Faker()
Faker.seed(0)

# def generate_busy_blocks(start_date, days=7): #days = 7
#     busy_blocks = []
#     work_hours = (9, 17)  # Work hours from 9 AM to 5 PM
    
#     # Generate 3-6 busy blocks
#     for _ in range(random.randint(3, 6)):
#         day_offset = random.randint(0, days - 1)
#         date = start_date + timedelta(days=day_offset)

#         # Choose random hour between 9 and 15 (to ensure end time <= 17)
#         start_hour = random.randint(work_hours[0], work_hours[1] - 2)
#         duration_hours = random.randint(1, 2)
#         end_hour = min(start_hour + duration_hours, work_hours[1])

#         start_dt = datetime.combine(date, time(start_hour, 0)).replace(tzinfo=None)
#         end_dt = datetime.combine(date, time(end_hour, 0)).replace(tzinfo=None)

#         busy_blocks.append({
#             "start": start_dt.isoformat() + "Z",
#             "end": end_dt.isoformat() + "Z",
#         })

#     return busy_blocks

# add random 30 mins at start or end
def generate_busy_blocks(start_date, days=7):
    busy_blocks = []
    work_hours = (9, 17)  # Work hours from 9 AM to 5 PM

    for _ in range(random.randint(3, 6)):
        day_offset = random.randint(0, days - 1)
        date = start_date + timedelta(days=day_offset)

        # Choose random hour between 9 and 15 (to ensure end time <= 17)
        start_hour = random.randint(work_hours[0], work_hours[1] - 2)
        duration_hours = random.randint(1, 2)

        # to add or not to add 30 minutes
        add_half_hour_start = random.choice([True, False])

        start_dt = datetime.combine(date, time(start_hour, 0)).replace(tzinfo=None)
        if add_half_hour_start:
            start_dt += timedelta(minutes=30)

        add_half_hour_end = random.choice([True, False])
        end_dt = start_dt + timedelta(hours=duration_hours)
        if add_half_hour_end:
            end_dt += timedelta(minutes=30)

        # dont go past work hours
        end_of_day = datetime.combine(date, time(work_hours[1], 0))
        if end_dt > end_of_day:
            end_dt = end_of_day

        busy_blocks.append({
            "start": start_dt.isoformat() + "Z",
            "end": end_dt.isoformat() + "Z",
        })

    return busy_blocks


def get_free_busy_data(interviewer_ids: list[int]) -> list[dict]:
    start_date = datetime.utcnow().date()
    data = []

    for id_ in interviewer_ids:
        interviewer = {
            "interviewerId": id_,
            "name": fake.name(),
            "busy": generate_busy_blocks(start_date)  # Changed from 'availability' to 'busy'
        }
        data.append(interviewer)

    return data 


def print_available_slots(available_slots):
    for date, slots in sorted(available_slots.items()):
        weekday = date.strftime("%A")
        date_str = f"{date.isoformat()} ({weekday})"
        print(f"\n{date_str}")
        print("-" * len(date_str))
        
        for start_time, end_time in slots:
            start_str = start_time.strftime("%I:%M %p").lstrip("0")
            end_str = end_time.strftime("%I:%M %p").lstrip("0")
            print(f"  {start_str} - {end_str}")

# set of all possible 30 min time slots and then remove the busy ones
def get_available_slots(busy_slots: list[dict[str, str]]):
    work_hours = (9, 17)  # 9 AM to 5 PM
    busy_days = defaultdict(set)
    dates = set()
    cutoff_datetime = datetime.utcnow() + timedelta(hours=24) # No slot may begin before this (less than 24 hours in the future)

    for slot in busy_slots:
        start_dt = datetime.fromisoformat(slot["start"].rstrip("Z"))
        end_dt = datetime.fromisoformat(slot["end"].rstrip("Z"))
        day = start_dt.date()
        dates.add(day)
        
        # Convert start time to 30-minute slot index (index: 0-48)
        start_slot = start_dt.hour * 2
        if start_dt.minute >= 30:
            start_slot += 1
            
        # Convert end time to 30-minute slot index (index: 0-48)
        end_slot = end_dt.hour * 2
        if end_dt.minute > 0:
            end_slot += 1
            
        # Add each 30 min slot that is busy period to busy_days
        for slot30min in range(start_slot, end_slot):
            busy_days[day].add(slot30min)
    
    # Determine the date range
    start_date = datetime.utcnow().date()
    if not dates:
        dates = {start_date}
    else:
        max_date = max(dates)
        days_to_include = (max_date - start_date).days + 1 # include last day
        for i in range(days_to_include):
            current_date = start_date + timedelta(days=i)
            dates.add(current_date)
    
    # find all available slots
    all_available_slots = {}
    for day in sorted(dates):
        if day.weekday() >= 5: # Skip Saturday and Sunday (5, 6)
            continue

        # All possible work hour 30-minute slots
        # 16 slots per dat
        work_start_slot = work_hours[0] * 2  # 18
        work_end_slot = work_hours[1] * 2    # 34
        all_slots = set(range(work_start_slot, work_end_slot))
        
        # Remove busy slots
        available_slots = all_slots - busy_days[day]
        
        # Convert to start and end time tuple (start_time, end_time)
        slots = []
        for free_slot in sorted(available_slots):
            start_hour = free_slot // 2 # extract hour from 30-min time slot
            if free_slot % 2 == 0:
                start_minute = 0
            else:
                start_minute = 30
            start_time = time(start_hour, start_minute)
            
            slot_datetime = datetime.combine(day, time(start_hour, start_minute))
            if slot_datetime < cutoff_datetime: # check cutoff threshold 
                continue

            # Find end time (30 mins later)
            end_hour = start_hour
            if start_minute == 0:
                end_minute = 30
            else:
                end_minute = 0
                end_hour += 1  # When start time is at the 30 min mark jump to next hour
                
            end_time = time(end_hour, end_minute)
            slots.append((start_time, end_time))
        
        all_available_slots[day] = slots
    
    return all_available_slots

def get_shared_slots(interviewers_availability: dict[int, dict[date, list[time]]]) -> dict[date, list[time]]:
    date_counts = defaultdict(dict)
    
    # count occurrences for every slot held by interviewers
    for all_slots in interviewers_availability.values():
        for date, times in all_slots.items():
            for time in times:
                date_counts[date][time] = date_counts[date].get(time, 0) + 1
    
    # find slot overlap
    shared_slots = {}
    interviewers_count = len(interviewers_availability)
    for date in sorted(date_counts.keys()):
        common_times = []
        
        for time, count in date_counts[date].items():
            if count == interviewers_count:
                common_times.append(time)
        
        # Only add dates with available times
        if common_times:
            sorted_times = sorted(common_times)
            shared_slots[date] = sorted_times
    
    return shared_slots

def get_interview_slots(matching_slots, duration):
    def find_required_slots(slots, start_index, count):
        for i in range(start_index, start_index + count - 1):   # check slots sequentially for contiguous block
            curr_slot_end_time = slots[i][1]
            next_slot_start_time = slots[i+1][0]
            
            if curr_slot_end_time != next_slot_start_time:      # return false if they dont match (gap)
                return False
        return True

    slot_size = 30  # minutes
    slots_needed = math.ceil(duration / slot_size)
    available_interviews = []
    
    for day, time_slots in matching_slots.items():
        sorted_slots = sorted(time_slots)
        
        # check each possible starting position for a sequence of consecutive time slots that fit the required slots_needed
        for start_index in range(len(sorted_slots) - slots_needed + 1): # include last slot
            # Check if slots from start_index are consecutive
            if find_required_slots(sorted_slots, start_index, slots_needed):
                # Create interview slot if required slots are available
                interview_start = datetime.combine(day, sorted_slots[start_index][0])
                interview_end = interview_start + timedelta(minutes=duration)
                interview_slot = {
                    "start": interview_start.isoformat(),
                    "end": interview_end.isoformat()
                }
                available_interviews.append(interview_slot)
    
    return available_interviews

# data = get_free_busy_data([1, 2])
# print(json.dumps(data, indent=4))

# i1 = get_available_slots(data[0]["busy"])
# i2 = get_available_slots(data[1]["busy"])

# #print_available_slots(i1)
# print("\n**************************************\n")
# #print_available_slots(i2)

# interviewers_availability = {}
# interviewers_availability[1] = get_available_slots(data[0]["busy"])
# interviewers_availability[2] = get_available_slots(data[1]["busy"])

# matching_slots = get_shared_slots(interviewers_availability)
# print_available_slots(matching_slots)
# print("\n======================================\n")

# duration = 72  # minutes
# available_meetings = get_interview_slots(matching_slots, duration)

# print(f"\nAvailable {duration}-minute interview slots:")
# for slot in available_meetings:
#     start = datetime.fromisoformat(slot["start"])
#     end = datetime.fromisoformat(slot["end"])
#     print(f"{start.strftime("%Y-%m-%d %I:%M %p")} to {end.strftime("%Y-%m-%d %I:%M %p")}")