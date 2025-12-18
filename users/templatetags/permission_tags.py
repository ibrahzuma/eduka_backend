from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def has_permission(context, module, action='view'):
    """
    Checks if the user has permission to access a module/action.
    Usage: {% has_permission 'sales' 'view' as can_view_sales %}
    Or directly in if: {% if has_permission user 'sales' %} (Note: simple_tag doesn't work well directly in if in older Django, 
    but we can register it as filter or assignment tag. 
    Actually, taking 'user' from context is unsafe if multiple users exist? No, usually request.user.
    Let's pass user explicitly or use context['request'].user
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    user = request.user
    
    # 1. Super Admin and Owner have access to everything
    if user.is_superuser or user.role == 'OWNER':
        return True
        
    # 2. Employees check assigned_role
    if user.role == 'EMPLOYEE':
        if not user.assigned_role:
            return False # Employee without role has no access (or basic access?)
            
        perms = user.assigned_role.permissions
        if not perms:
            return False
            
        # Check if module exists in permissions
        module_perms = perms.get(module, [])
        
        # Check if action is in module permissions
        # Note: permissions are lists like ['view', 'create', 'edit', 'delete']
        return action in module_perms
        
    return False

@register.filter
def can_view(user, module):
    """
    Filter wrapper for easier usage in if tags.
    Usage: {% if user|can_view:'sales' %}
    """
    if not user.is_authenticated:
        return False
        
    if user.is_superuser or user.role == 'OWNER':
        return True
        
    if user.role == 'EMPLOYEE':
        if not user.assigned_role:
            return False
        perms = user.assigned_role.permissions
        if not perms:
            return False
        return perms.get(module, [])
        
    return False

@register.filter
def get_item(dictionary, key):
    """
    Dictionary lookup filter for templates.
    Usage: {{ mydict|get_item:key }}
    """
    if not dictionary:
        return []
    return dictionary.get(key, [])
