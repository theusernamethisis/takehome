from .models import Interviewer, InterviewTemplate
from django.contrib import admin

@admin.register(Interviewer)
class InterviewerAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name')
    search_fields = ('first_name', 'last_name')

@admin.register(InterviewTemplate)
class InterviewTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'duration')
    search_fields = ('name',)
    filter_horizontal = ('interviewers',)