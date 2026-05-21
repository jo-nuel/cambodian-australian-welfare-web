from django import forms
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import AnnualReport, CommunityPublication, ResourceDownloadLead, UsefulLink


class ResourceEmailForm(forms.Form):
    email = forms.EmailField()


RESOURCE_MODELS = {
    'annual-report': AnnualReport,
    'publication': CommunityPublication,
    'useful-link': UsefulLink,
}


@require_POST
def resource_download(request, resource_type, resource_id):
    model = RESOURCE_MODELS.get(resource_type)
    if not model:
        return HttpResponseBadRequest('Unknown resource type.')

    form = ResourceEmailForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest('Please provide a valid email address.')

    resource = get_object_or_404(model, pk=resource_id)
    url = getattr(resource, 'url', '')
    if not url:
        return HttpResponseNotAllowed(['POST'], 'This resource is not currently available.')

    title = getattr(resource, 'title', None) or str(resource)
    ResourceDownloadLead.objects.create(
        email=form.cleaned_data['email'],
        resource_type=resource_type,
        resource_title=title,
        resource_url=url,
    )
    return redirect(url)
