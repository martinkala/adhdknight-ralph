def active_app(request):
    """Which app of the shared console is active, for the ADHD | Food switch in base.html."""
    return {"active_app": "food" if request.path.startswith("/food/") else "adhd"}
