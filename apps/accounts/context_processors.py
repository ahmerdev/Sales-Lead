from .models import Workspace

def workspace_context(request):
    """
    Context processor to provide the active workspace across all templates.
    """
    if not request.user.is_authenticated:
        return {'current_workspace': None}

    workspace = None
    # Check if workspace_id in session
    workspace_id = request.session.get('active_workspace_id')
    if workspace_id:
        workspace = Workspace.objects.filter(id=workspace_id, owner=request.user).first()
        if not workspace:
            workspace = Workspace.objects.filter(id=workspace_id, memberships__user=request.user).first()

    if not workspace:
        # Default to first owned workspace or create default one
        workspace = Workspace.objects.filter(owner=request.user).first()
        if not workspace:
            # Create default workspace for user
            workspace_name = f"{request.user.full_name or request.user.username}'s Workspace"
            workspace = Workspace.objects.create(
                name=workspace_name,
                owner=request.user,
                plan='pro'
            )
        request.session['active_workspace_id'] = workspace.id

    return {
        'current_workspace': workspace,
    }
