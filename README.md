# Dynamically Generating Potential Interview Time Slots

## Setup

I used Django app creation to make **`interviews`** to make the structure containing the models, views, serializers, utility functions, script to load starting data. I opted to use PostgreSQL for the database.

I modified

- config/api_router.py
- config/settings/base.py

**Running the Application**

```bash
export DATABASE_URL=postgres://postgres:postgres@postgres:5432/candidate_fyi_takehome_project
export USE_DOCKER=yes

# starting
docker-compose -f docker-compose.local.yml up

# create migrations
docker-compose -f docker-compose.local.yml exec django python manage.py makemigrations interviews

# apply migrations
docker-compose -f docker-compose.local.yml exec django python manage.py migrate

# load test data
docker-compose -f docker-compose.local.yml exec django python manage.py load_interviewers
```

The API will be available at: http://localhost:8000/api/interviews/<id>/availability

**Sample**

```json
[
    {
        "interviewerId": 3,
        "name": "Thomas Jefferson",
        "busy": [
            {
                "start": "2025-04-29T09:30:00Z",
                "end": "2025-04-29T12:00:00Z"
            },
            {
                "start": "2025-04-28T11:30:00Z",
                "end": "2025-04-28T12:30:00Z"
            },
            {
                "start": "2025-04-28T13:00:00Z",
                "end": "2025-04-28T15:30:00Z"
            },
            {
                "start": "2025-04-28T10:00:00Z",
                "end": "2025-04-28T12:00:00Z"
            }
        ]
    },
    {
        "interviewerId": 4,
        "name": "James Madison",
        "busy": [
            {
                "start": "2025-04-29T12:30:00Z",
                "end": "2025-04-29T14:00:00Z"
            },
            {
                "start": "2025-04-28T10:30:00Z",
                "end": "2025-04-28T11:30:00Z"
            },
            {
                "start": "2025-04-29T11:00:00Z",
                "end": "2025-04-29T12:30:00Z"
            },
            {
                "start": "2025-04-29T11:00:00Z",
                "end": "2025-04-29T12:00:00Z"
            },
            {
                "start": "2025-04-29T15:00:00Z",
                "end": "2025-04-29T16:00:00Z"
            },
            {
                "start": "2025-04-28T14:00:00Z",
                "end": "2025-04-28T16:00:00Z"
            }
        ]
    }
]
```

```
Available slots (ID: 3):
2025-04-28 (Monday)
-------------------

2025-04-29 (Tuesday)
--------------------
  2:30 PM - 3:00 PM
  3:00 PM - 3:30 PM
  3:30 PM - 4:00 PM
  4:00 PM - 4:30 PM
  4:30 PM - 5:00 PM

Available slots (ID: 4):
2025-04-28 (Monday)
-------------------

2025-04-29 (Tuesday)
--------------------
  2:30 PM - 3:00 PM
  4:00 PM - 4:30 PM
  4:30 PM - 5:00 PM

Available slots (Shared):
2025-04-29 (Tuesday)
--------------------
  2:30 PM - 3:00 PM
  4:00 PM - 4:30 PM
  4:30 PM - 5:00 PM

Available 45-minute interview slots:
2025-04-29 04:00 PM to 2025-04-29 04:45 PM
```

```json
{
    "interviewId": 3,
    "name": "HR Interview",
    "durationMinutes": 45,
    "interviewers": [
        {
            "id": 3,
            "name": "Thomas Jefferson"
        },
        {
            "id": 4,
            "name": "James Madison"
        }
    ],
    "availableSlots": [
        {
            "start": "2025-04-29T16:00:00Z",
            "end": "2025-04-29T16:45:00Z"
        }
    ]
}
```

## Design

Obtaining the slots of busy time (in hours) for interviewers is done calling **`get_free_busy_data()`** to generate mock data. In the constraints, it is stated that “Slots must begin on hour or half-hour marks**”** which aligns with the returned mock data. While working on a solution, I realized that interview templates that are ≤ 30 mins would fill an interviewers full available slots, since it is in hour intervals. This seemed inefficient, so I made the design decision to change how the creation of available interviewer slots is done. Instead of hour slots, I increased the resolution by finding all 30 minute free periods for the interviews within **`get_available_slots()`.** I also adjusted **`get_free_busy_data()`** to randomly add 30 mins to start or end of each busy block to reflect my change, even though the hour blocks it previously generated will still work with my solution, now I can have slots which begin on both hour and half-hour marks. 

I observed the constraint that “no slot may begin less than 24 hours in the future”, but also employed checks to only create available interviewer slots that are only within the 9:00 AM - 5:00 PM schedule and also that none are created during the weekend. 

## Edge Case or Complexity

A complexity that I stumbled upon was that it was required that “Slots must be exactly the duration minutes of the template”, which is straight forward with the example given in the initial prompt: an interview template having a duration of 60 minutes. As long as the interview template duration was a multiple of 30 then we are in business. It was not explicitly stated that interview template durations could have peculiar times (e.g. 45, 75, 80, etc.). 

It mattered because these types of interviews would not fit nicely in available interview slots, allowing for the interview slot to be exactly the duration of minutes of the template. Each interviewer's availability is broken down into discrete 30 minute slots, but we need to identify unbroken sequences of these slots that match the required interview duration. Simply finding available slots wasn't enough, we have to verify that they formed a contiguous block without gaps.

I solved this within **`get_interview_slots()`**, where I used a sliding window. First, we calculate the exact number of 30 minute slots required for out interview template’s duration 

**`slots_needed = ceil(duration / slot_size)`**

Then use each starting position of available slots shared between all assigned interviewers with the **`find_required_slots()`**  helper ****function. This function would would look at the potential sequence and identify if the sets of slots required is continuous by checking that each slot's end time matched the next slot's start time. Lastly, when a set of slots is verified to be continuous, then I would convert it to the formatted time range with the exact duration of the interview, not just the end time of the last slot. Overall the solution will now work efficiently with nonstandard interview template durations.