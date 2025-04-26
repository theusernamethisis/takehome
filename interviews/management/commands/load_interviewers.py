from interviews.models import Interviewer, InterviewTemplate
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Loads test data for interviews app"

    def handle(self, *args, **kwargs):
        interviewers = []
        interviewer_data = [
            {"first_name": "George", "last_name": "Washington"},
            {"first_name": "John", "last_name": "Adams"},
            {"first_name": "Thomas", "last_name": "Jefferson"},
            {"first_name": "James", "last_name": "Madison"}
        ]
        
        for data in interviewer_data:
            interviewer = Interviewer.objects.create(
                first_name=data["first_name"],
                last_name=data["last_name"]
            )
            interviewers.append(interviewer)
            self.stdout.write(self.style.SUCCESS(f"Created interviewer: {interviewer}"))
        
        template_data = [
            {"name": "Phone call", "duration": 15},
            {"name": "Technical", "duration": 60},
            {"name": "HR Interview", "duration": 45},
            {"name": "System Design", "duration": 90}
        ]
        
        for i, data in enumerate(template_data):
            template = InterviewTemplate.objects.create(
                name=data["name"],
                duration=data["duration"]
            )
            
            # Assign interviewers (different combinations for each template)
            if i == 0:  # Technical
                template.interviewers.add(interviewers[1], interviewers[3])
            if i == 1:  # Technical
                template.interviewers.add(interviewers[0], interviewers[1])
            elif i == 2:  # HR Interview
                template.interviewers.add(interviewers[2], interviewers[3])
            else:  # System Design
                template.interviewers.add(interviewers[0], interviewers[2], interviewers[3])
            
            self.stdout.write(self.style.SUCCESS(f"Created template: {template}"))
        
        self.stdout.write(self.style.SUCCESS("Test data loaded successfully"))