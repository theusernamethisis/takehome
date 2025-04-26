from datetime import datetime, timedelta, date, time
from collections import defaultdict
from math import ceil
import logging
import json

logger = logging.getLogger("interviews_availability")

# set of all possible 30 min time slots and then remove the busy ones
# free slots for an interviewer
def get_available_slots(busy_slots: list[dict[str, str]]):
    work_hours = (9, 17)  # 9 AM to 5 PM
    busy_days = defaultdict(set)
    dates = set()
    
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

def get_interview_slots(matching_slots: dict[date, list[tuple[time, time]]], duration: int) -> list[dict[str, str]]:
    def find_required_slots(slots, start_index, count):
        for i in range(start_index, start_index + count - 1):   # check slots sequentially for contiguous block
            curr_slot_end_time = slots[i][1]
            next_slot_start_time = slots[i+1][0]
            
            if curr_slot_end_time != next_slot_start_time:      # return false if they dont match (gap)
                return False
        return True

    slot_size = 30  # assumes all interviewer slots are on 30 min interval
    slots_needed = ceil(duration / slot_size)
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
                    "start": interview_start.isoformat() + "Z",
                    "end": interview_end.isoformat() + "Z"
                }
                available_interviews.append(interview_slot)
    
    return available_interviews

def calc_available_slots(busy_data: list[dict], interviewer_ids: list[int], duration: int) -> list[dict[str, str]]:
    interviewers_availability = {}
    for interviewer_id in interviewer_ids:
        for item in busy_data:
            if item["interviewerId"] == interviewer_id:
                available_slots = get_available_slots(item["busy"])
                log_available_slots(available_slots, interviewer_id) # /logs/interviews_availability.log
                interviewers_availability[interviewer_id] = available_slots
                break
    
    shared_slots = get_shared_slots(interviewers_availability)
    log_available_slots(shared_slots)                                # /logs/interviews_availability.log
    interview_slots = get_interview_slots(shared_slots, duration)
    log_interview_slots(interview_slots, duration)                   # /logs/interviews_availability.log

    return interview_slots

# use on:
#   get_free_busy_data()
def log_busydata(data):
    formatted_json = json.dumps(data, indent=4, default=str)
    logger.debug(f"Inital busy slots generated by get_free_busy_data()\n{formatted_json}\n")

# use on:
#   get_available_slots()
#   get_shared_slots()
def log_available_slots(available_slots, InterviewerId=""):
    log_lines = []
    
    for slot_date, slots in sorted(available_slots.items()):
        weekday = slot_date.strftime("%A")
        date_str = f"{slot_date.isoformat()} ({weekday})"
        log_lines.append(f"\n{date_str}")
        log_lines.append("-" * len(date_str))
        
        for start_time, end_time in slots:
            start_str = start_time.strftime("%I:%M %p").lstrip("0")
            end_str = end_time.strftime("%I:%M %p").lstrip("0")
            log_lines.append(f"  {start_str} - {end_str}")
    
    formatted_output = "\n".join(log_lines)
    if not InterviewerId: 
        msg = "Available slots (Shared):"
    else:
        msg = f"Available slots (ID: {InterviewerId}):"

    logger.debug(f"{msg}\n{formatted_output}\n")

# use on:
#   get_interview_slots()
def log_interview_slots(interview_slots, duration):
    lines = [f"\nAvailable {duration}-minute interview slots:"]
    
    for slot in interview_slots:
        start = datetime.fromisoformat(slot["start"])
        end = datetime.fromisoformat(slot["end"])
        lines.append(f"{start.strftime('%Y-%m-%d %I:%M %p')} to {end.strftime('%Y-%m-%d %I:%M %p')}")
    
    message = "\n".join(lines)
    logger.debug(message + "\n")