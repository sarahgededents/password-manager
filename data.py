FIELDS = [
    {'uid': 'name', 'name': 'Name', 'tree_column': '#0', 'can_copy': True},
    {'uid': 'email', 'name': 'Email', 'can_copy': True},
    {'uid': 'password', 'name': 'Password', 'private': True, 'can_copy': True},
    {'uid': 'website', 'name': 'Website', 'can_copy': True, 'can_goto': True}
]
for field in FIELDS:
    field['tree_column'] = field.get('tree_column', field['uid'])