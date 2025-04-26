from django.shortcuts import render, get_object_or_404

from services.mock_availability import get_free_busy_data
from .serializers import InterviewAvailabilitySerializer
from .models import InterviewTemplate, Interviewer
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from .utils import *
import logging

# /logs/interviews_availability.log
logger = logging.getLogger("interviews_availability")

class InterviewTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InterviewTemplate.objects.all()
    serializer_class = InterviewAvailabilitySerializer
    permission_classes = [AllowAny]  # Allow anyone to access the endpoint
    
    @action(detail=True, methods=["get"], url_path="availability", permission_classes=[AllowAny])
    def availability(self, request, pk=None):
        try:
            template = self.get_object()
            interviewer_ids = list(template.interviewers.values_list("id", flat=True))
            interviewers_data = list(template.interviewers.values("id", "first_name", "last_name"))
            interviewer_names = {
                interviewer["id"]: f"{interviewer["first_name"]} {interviewer["last_name"]}"
                for interviewer in interviewers_data
            }

            busy_data = get_free_busy_data(interviewer_ids, interviewer_names)
            log_busydata(busy_data) 
            
            available_slots = calc_available_slots(busy_data, interviewer_ids, template.duration)
            
            response_data = {
                "interviewId": template.id,
                "name": template.name,
                "durationMinutes": template.duration,
                "interviewers": [{
                    "id": interviewer.id,
                    "name": f"{interviewer.first_name} {interviewer.last_name}"
                } for interviewer in template.interviewers.all()],
                "availableSlots": available_slots
            }
            
            return Response(response_data)
        except InterviewTemplate.DoesNotExist:
            return Response(
                {"error": "Interview template not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["get"], url_path=r"interviewer/(?P<interviewer_id>\d+)", permission_classes=[AllowAny])
    def interviewer_busy_data(self, request, interviewer_id=None):
        try:
            interviewer = get_object_or_404(Interviewer, id=interviewer_id)
            
            busy_data = get_free_busy_data([interviewer_id])
            
            response_data = {
                "interviewerId": interviewer.id,
                "name": f"{interviewer.first_name} {interviewer.last_name}",
                "busyPeriods": busy_data[0]["busy"] if busy_data and busy_data[0]["busy"] else []
            }
            
            return Response(response_data)
        except Interviewer.DoesNotExist:
            return Response(
                {"error": f"Interviewer with ID {interviewer_id} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )