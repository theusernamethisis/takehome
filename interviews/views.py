from django.shortcuts import render, get_object_or_404

from services.mock_availability import get_free_busy_data, get_free_busy_data_range
from .serializers import InterviewAvailabilitySerializer
from .models import InterviewTemplate, Interviewer
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse
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

            interviewer_ids.append(3)
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

    @action(detail=False, methods=["post"], url_path="availability_date_range_missing", permission_classes=[AllowAny])
    def availability_date_range_missing(self, request):
        try:
            data = json.loads(request.body)
            
            #template_id = data.get("templateId")
            template_id = 2 # Force 2, so we can add a person with empty schedule
            start_date_str = data.get("startDate")
            end_date_str = data.get("endDate")
            
            # Validate that all fields are present
            if not all([template_id, start_date_str, end_date_str]):
                return JsonResponse({
                    "error": "All fields are required"
                }, status=400)
            
            try:
                template = InterviewTemplate.objects.get(id=template_id)
            except InterviewTemplate.DoesNotExist:
                return JsonResponse({
                    "error": f"Interview template with id {template_id} not found"
                }, status=404)
            
            try:
                start_date = datetime.fromisoformat(start_date_str.rstrip('Z'))
                end_date = datetime.fromisoformat(end_date_str.rstrip('Z'))
            except ValueError:
                return JsonResponse({
                    "error": "Invalid date format."
                }, status=400)
            
            # Validate date range
            if end_date < start_date:
                return JsonResponse({
                    "error": "End date must be after start date"
                }, status=400)
            
            interviewer_ids = list(template.interviewers.values_list("id", flat=True))
            interviewers_data = list(template.interviewers.values("id", "first_name", "last_name"))
            interviewer_names = {
                interviewer["id"]: f"{interviewer["first_name"]} {interviewer["last_name"]}"
                for interviewer in interviewers_data
            }
            
            # pass 2 for days to deduct: busy data only generate for end_date -2
            #    To test that interviewers will have open schedules prior to end date
            busy_data = get_free_busy_data_range(interviewer_ids, interviewer_names, start_date_str, end_date_str, 2)

            test_interviewer = {
                "interviewerId": 3,
                "name": "Thomas Jefferson",
                "busy": []
            }

            busy_data.append(test_interviewer)
            interviewer_ids.append(3)
            logger.debug(f"interviewer_ids before calc function: {interviewer_ids}")
            logger.debug(f"new interviewers: {template.interviewers.all()}")
            log_busydata(busy_data)
            
            available_slots = calc_available_slots_with_date_range(busy_data, interviewer_ids, template.duration,start_date_str, end_date_str)
            
            response_interviewers = []
            for item in busy_data:
                response_interviewers.append({
                    "id": item["interviewerId"], 
                    "name": item["name"]
                })

            response_data = {
                "interviewId": template.id,
                "name": template.name,
                "durationMinutes": template.duration,
                "interviewers": response_interviewers,
                "availableSlots": available_slots
            }

            return JsonResponse(response_data)    
        except json.JSONDecodeError:
            return JsonResponse({
                "error": "Invalid JSON data"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "error": str(e)
            }, status=500)

    @action(detail=False, methods=["post"], url_path="availability_date_range", permission_classes=[AllowAny])
    def availability_date_range(self, request):
        try:
            data = json.loads(request.body)
            
            template_id = data.get("templateId")
            start_date_str = data.get("startDate")
            end_date_str = data.get("endDate")
            
            # Validate that all fields are present
            if not all([template_id, start_date_str, end_date_str]):
                return JsonResponse({
                    "error": "All fields are required"
                }, status=400)
            
            try:
                template = InterviewTemplate.objects.get(id=template_id)
            except InterviewTemplate.DoesNotExist:
                return JsonResponse({
                    "error": f"Interview template with id {template_id} not found"
                }, status=404)
            
            try:
                start_date = datetime.fromisoformat(start_date_str.rstrip('Z'))
                end_date = datetime.fromisoformat(end_date_str.rstrip('Z'))
            except ValueError:
                return JsonResponse({
                    "error": "Invalid date format."
                }, status=400)
            
            # Validate date range
            if end_date < start_date:
                return JsonResponse({
                    "error": "End date must be after start date"
                }, status=400)
            
            interviewer_ids = list(template.interviewers.values_list("id", flat=True))
            interviewers_data = list(template.interviewers.values("id", "first_name", "last_name"))
            interviewer_names = {
                interviewer["id"]: f"{interviewer["first_name"]} {interviewer["last_name"]}"
                for interviewer in interviewers_data
            }
            
            # pass 2 for days to deduct: busy data only generate for end_date -2
            #    To verify that interviewers will have open schedules prior to end date
            busy_data = get_free_busy_data_range(interviewer_ids, interviewer_names, start_date_str, end_date_str, 2)
            log_busydata(busy_data)
            
            available_slots = calc_available_slots_with_date_range(busy_data, interviewer_ids, template.duration, start_date_str, end_date_str)
            
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
            
            return JsonResponse(response_data)    
        except json.JSONDecodeError:
            return JsonResponse({
                "error": "Invalid JSON data"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "error": str(e)
            }, status=500)

    @action(detail=False, methods=["post"], url_path="test_availability", permission_classes=[AllowAny])
    def test_availability(self, request):
        return Response({"message": "availability test works"})

    @action(detail=False, methods=['POST'])
    def test_route(self, request):
        return Response({"message": "test works"})


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