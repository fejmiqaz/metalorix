from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from .models import Idea, IdeaImage, InstagramPost, Sender


class ImageInline(admin.TabularInline):
    model = IdeaImage
    fields = ['preview']
    readonly_fields = ['preview']
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def preview(self, obj):
        return format_html('<a href="{}" target="_blank"><img src="{}" width="160" alt="Idea reference"></a>',
                           reverse('idea_image', args=[obj.pk]), reverse('idea_image', args=[obj.pk]))


@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    list_display = ['sender', 'sender_total', 'title', 'song', 'status', 'created_at']
    list_filter = [('sender', admin.RelatedOnlyFieldListFilter), 'status', 'created_at']
    search_fields = ['sender__name', 'sender__email', 'title', 'song', 'description']
    autocomplete_fields = ['sender']
    ordering = ['sender__name', 'sender__email', '-created_at']
    readonly_fields = ['created_at']
    inlines = [ImageInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sender').annotate(total=Count('sender__ideas'))

    @admin.display(description='Ideas from sender', ordering='total')
    def sender_total(self, obj):
        return obj.total if obj.sender_id else 'Unknown (legacy submission)'


@admin.register(Sender)
class SenderAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'idea_count', 'view_ideas']
    search_fields = ['name', 'email']
    readonly_fields = ['idea_count', 'view_ideas']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(total=Count('ideas'))

    @admin.display(description='Total ideas', ordering='total')
    def idea_count(self, obj):
        return obj.total

    @admin.display(description='Submissions')
    def view_ideas(self, obj):
        if not obj.pk:
            return 'No submissions yet'
        return format_html('<a href="{}?sender__id__exact={}">View ideas</a>', reverse('admin:core_idea_changelist'), obj.pk)


@admin.register(InstagramPost)
class PostAdmin(admin.ModelAdmin):
    list_display = ['instagram_id', 'published_at', 'caption']

admin.site.site_header = 'metalorix studio'
admin.site.site_title = 'metalorix'
