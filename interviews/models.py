from django.db import models
import uuid

class Interviewer(models.Model):
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    
    def __str__(self):
        return f"{self.id}: {self.first_name} {self.last_name}"

class InterviewTemplate(models.Model):
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64)   # name of interview
    duration = models.PositiveIntegerField() # minutes
    interviewers = models.ManyToManyField(Interviewer, related_name='interview_templates')
    
    def __str__(self):
        return f"{self.id}: {self.name}"