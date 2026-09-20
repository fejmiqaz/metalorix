import time
from django.contrib import messages
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import IdeaForm
from .models import IdeaImage, InstagramPost, Sender, IdeaNotification
from .protection import reserve_submission, verify_human, reject
from .notifications import deliver

ARCHIVE = [{'permalink': f'https://www.instagram.com/p/{code}/'} for code in
           ['DIwT4qEiE3B', 'DImmbByi5Rl', 'DGJg6diOBUk']]

def home(request, form=None, status=200):
    posts = list(InstagramPost.objects.all()[:3])
    return render(request, 'core/home.html', {'form': form if form is not None else IdeaForm(),
                  'posts': posts or ARCHIVE, 'turnstile_site_key': settings.TURNSTILE_SITE_KEY,
                  'turnstile_required': settings.TURNSTILE_REQUIRED}, status=status)


@require_POST
def submit_idea(request):
    if not verify_human(request):
        return HttpResponse('Verification could not be completed. Reload the page and try again.', status=400)
    form = IdeaForm(request.POST, request.FILES)
    if time.time() - request.session.get('last_idea', 0) < 60:
        form.is_valid()
        form.add_error(None, 'Please wait a minute before sending another idea.')
        return home(request, form, status=429)
    if form.is_valid():
        with transaction.atomic():
            if not reserve_submission(request, form.cleaned_data):
                return reject()
            sender, _ = Sender.objects.get_or_create(email=form.cleaned_data['sender_email'],
                                                     defaults={'name': form.cleaned_data['sender_name']})
            idea = form.save(commit=False)
            idea.sender = sender
            idea.save()
            IdeaImage.objects.bulk_create([IdeaImage(idea=idea, data=data) for data in form.cleaned_data['images']])
            if settings.IDEA_NOTIFICATIONS_ENABLED:
                notification = IdeaNotification.objects.create(idea=idea)
                transaction.on_commit(lambda: deliver(notification.pk), robust=True)
        request.session['last_idea'] = time.time()
        messages.success(request, 'Your idea is in. Thank you for sharing a little of your world.')
        return redirect('/#ideas')
    return home(request, form, status=400)


@staff_member_required
def idea_image(request, pk):
    if not request.user.has_perm('core.view_idea'):
        return HttpResponse(status=403)
    image = get_object_or_404(IdeaImage, pk=pk)
    response = HttpResponse(bytes(image.data), content_type='image/jpeg')
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
