from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import OpportunityItem

@login_required
def opportunities_overview_view(request):
    items = OpportunityItem.objects.filter(lead__workspace__owner=request.user).order_by('-score_impact')[:50]
    return render(request, 'opportunities/list.html', {'opportunities': items})
