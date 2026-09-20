import time
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import IdeaForm
from .models import IdeaImage, InstagramPost, Sender

def home(request, form=None, status=200):
    posts = list(InstagramPost.objects.all()[:3])
    return render(request, 'core/home.html', {'form': form if form is not None else IdeaForm(),
                  'posts': posts}, status=status)


@require_POST
def submit_idea(request):
    form = IdeaForm(request.POST, request.FILES)
    if time.time() - request.session.get('last_idea', 0) < 60:
        form.is_valid()
        form.add_error(None, 'Please wait a minute before sending another idea.')
        return home(request, form, status=429)
    if form.is_valid():
        with transaction.atomic():
            sender, _ = Sender.objects.get_or_create(email=form.cleaned_data['sender_email'],
                                                     defaults={'name': form.cleaned_data['sender_name']})
            idea = form.save(commit=False)
            idea.sender = sender
            idea.save()
            IdeaImage.objects.bulk_create([IdeaImage(idea=idea, data=data) for data in form.cleaned_data['images']])
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
