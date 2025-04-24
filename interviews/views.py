from django.shortcuts import render

from services.mock_availability import get_free_busy_data
from .serializers import InterviewAvailabilitySerializer
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import InterviewTemplate
from rest_framework import viewsets

class InterviewTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InterviewTemplate.objects.all()
    serializer_class = InterviewAvailabilitySerializer
    permission_classes = [AllowAny]  # Allow anyone to access the endpoint
    
    @action(detail=True, methods=["get"], url_path="availability", permission_classes=[AllowAny])
    def availability(self, request, pk=None):
        try:
            template = self.get_object()
            interviewer_ids = list(template.interviewers.values_list("id", flat=True))
            
            busy_data = get_free_busy_data(interviewer_ids)
            
            available_slots = self.calc_available_slots(busy_data, template.duration)
            
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
    
    def calc_available_slots(self, busy_data, duration):
        return [
            {
                "start": "2025-04-24T10:00:00Z",
                "end": "2025-04-24T10:00:00Z"
            }
        ]