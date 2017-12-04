import logging
from operator import attrgetter
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from ivetl.models import ContentBlock

log = logging.getLogger(__name__)


@login_required
def list_blocks(request):
    messages = []
    if 'from' in request.GET:
        from_value = request.GET['from']
        if from_value == 'new-success':
            messages.append("Your new content block has been created.")
        elif from_value == 'save-success':
            messages.append("Your content block changes have been saved.")

    all_blocks = ContentBlock.objects.all()
    sorted_blocks = sorted(all_blocks, key=attrgetter('block_id'))
    return render(request, 'app_content/list.html', {
        'blocks': sorted_blocks,
        'messages': messages,
    })


class ContentBlockForm(forms.Form):
    block_id = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    markdown = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}), required=True)

    def save(self):
        content_block = ContentBlock.objects(
            block_id=self.cleaned_data['block_id'],
        ).update(
            markdown=self.cleaned_data['markdown'],
        )
        return content_block

    def __init__(self, *args, instance=None, **kwargs):
        if instance:
            initial = dict(instance)
        else:
            initial = {}

        super().__init__(*args, initial=initial, **kwargs)


@login_required
def edit_block(request, block_id=None):
    block = None
    new = True
    if block_id:
        block = ContentBlock.objects.get(block_id=block_id)
        new = False

    if request.method == 'POST':
        form = ContentBlockForm(request.POST, instance=block)
        if form.is_valid():
            form.save()
            if new:
                return HttpResponseRedirect(reverse('app_content.list_blocks') + '?from=new-success')
            else:
                return HttpResponseRedirect(reverse('app_content.list_blocks') + '?from=save-success')
    else:
        form = ContentBlockForm(instance=block)

    return render(request, 'app_content/edit.html', {
        'form': form,
        'content_block': block,
    })
