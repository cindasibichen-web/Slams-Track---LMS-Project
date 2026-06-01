# from superadmin_app.models import Profiles
# import re


# def generate_user_id(self):

#         role_prefix = {
#             'SuperAdmin': 'SUP',
#             'Admin': 'ADM',
#             'Staff': 'STF',
#             'Accountant': 'ACT',
#             'Teachers': 'TCH',
#             'Students': 'STD',
#         }

#         prefix = role_prefix.get(self.role, 'USR')

#         # Get last created user with same prefix
#         last_user = Profiles.objects.filter(
#             user_id__startswith=prefix
#         ).order_by('-id').first()

#         if last_user and last_user.user_id:
#             match = re.search(r'(\d+)$', last_user.user_id)

#             if match:
#                 last_number = int(match.group(1))
#                 new_number = last_number + 1
#             else:
#                 new_number = 1
#         else:
#             new_number = 1

#         return f"{prefix}-{new_number:03d}"