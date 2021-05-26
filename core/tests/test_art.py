import re
from itertools import zip_longest

from pytest import fixture
from pytest import mark

from core.models import Art

# ------------------------------------------------------------------------------
# Helpers


class multiline(str):
    def __new__(cls, string):
        start = 0 if string[0] != "\n" else 1
        end = None if string[-1] != "\n" else -1
        string = string[start:end]

        return super().__new__(cls, string)


def multiline_assert(str1, str2):
    x = 0
    y = 0
    for char1, char2 in zip_longest(str1, str2):
        if char1 != char2:
            f_char1 = repr(char1)
            f_char2 = repr(char2)

            f_line1 = repr(str1.splitlines()[y])
            f_line2 = repr(str2.splitlines()[y])

            raise AssertionError(
                f"L{y} C{x}: {f_char1} != {f_char2}\n"
                f"i.e. {f_line1} !=\n"
                f"     {f_line2}"
            )

        if char1 == char2 != "\n":
            x += 1
        else:
            x = 0
            y += 1


# ------------------------------------------------------------------------------
# Art


# fmt:off


py_logo = multiline("""
                   _.gj8888888lkoz.,_
                d888888888888888888888b,
               j88P""V8888888888888888888
               888    8888888888888888888
               888baed8888888888888888888
               88888888888888888888888888
                            8888888888888
    ,ad8888888888888888888888888888888888  888888be,
   d8888888888888888888888888888888888888  888888888b,
  d88888888888888888888888888888888888888  8888888888b,
 j888888888888888888888888888888888888888  88888888888p,
j888888888888888888888888888888888888888'  8888888888888
8888888888888888888888888888888888888^"   ,8888888888888
88888888888888^'                        .d88888888888888
8888888888888"   .a8888888888888888888888888888888888888
8888888888888  ,888888888888888888888888888888888888888^
^888888888888  888888888888888888888888888888888888888^
 V88888888888  88888888888888888888888888888888888888Y
  V8888888888  8888888888888888888888888888888888888Y
   `"^8888888  8888888888888888888888888888888888^"'
               8888888888888
               88888888888888888888888888
               8888888888888888888P""V888
               8888888888888888888    888
               8888888888888888888baed88V
                `^888888888888888888888^
                  `'"^^V888888888V^^'
""")

py_logo_render = multiline("""
                   _.gj8888888lkoz.,_                                           
                d888888888888888888888b,                                        
               j88P""V8888888888888888888                                       
               888    8888888888888888888                                       
               888baed8888888888888888888                                       
               88888888888888888888888888                                       
                            8888888888888                                       
    ,ad8888888888888888888888888888888888  888888be,                            
   d8888888888888888888888888888888888888  888888888b,                          
  d88888888888888888888888888888888888888  8888888888b,                         
 j888888888888888888888888888888888888888  88888888888p,                        
j888888888888888888888888888888888888888'  8888888888888                        
8888888888888888888888888888888888888^"   ,8888888888888                        
88888888888888^'                        .d88888888888888                        
8888888888888"   .a8888888888888888888888888888888888888                        
8888888888888  ,888888888888888888888888888888888888888^                        
^888888888888  888888888888888888888888888888888888888^                         
 V88888888888  88888888888888888888888888888888888888Y                          
  V8888888888  8888888888888888888888888888888888888Y                           
""")

mrlc_test = multiline("""
 _____  _                                ___   ___     _____      _       ___     _____                   _ 
|  __ \(_)                              / _ \ / _ \   / ____|    | |     |__ \   / ____|                 | |
| |  | |_ ___     _____   _____ _ __   | (_) | | | | | |     ___ | |___     ) | | (___  _   _ _ __ ___   | |
| |  | | / __|   / _ \ \ / / _ \ '__|   > _ <| | | | | |    / _ \| / __|   / /   \___ \| | | | '__/ _ \  | |
| |__| | \__ \  | (_) \ V /  __/ |     | (_) | |_| | | |___| (_) | \__ \  |_|    ____) | |_| | | |  __/  |_|
|_____/|_|___/   \___/ \_/ \___|_|      \___/ \___/   \_____\___/|_|___/  (_)   |_____/ \__,_|_|  \___|  (_)
""")


mrlc_test_native = multiline("""
 _____  _                                ___   ___     _____      _       ___   
|  __ \(_)                              / _ \ / _ \   / ____|    | |     |__ \  
| |  | |_ ___     _____   _____ _ __   | (_) | | | | | |     ___ | |___     ) | 
| |  | | / __|   / _ \ \ / / _ \ '__|   > _ <| | | | | |    / _ \| / __|   / /  
| |__| | \__ \  | (_) \ V /  __/ |     | (_) | |_| | | |___| (_) | \__ \  |_|   
|_____/|_|___/   \___/ \_/ \___|_|      \___/ \___/   \_____\___/|_|___/  (_)   
""")


# fmt:on

# ------------------------------------------------------------------------------
# Tests


@mark.django_db
def test_render_thumb(django_user_model):
    user = django_user_model.objects.create(username="bob", password="pass")
    art = Art(artist=user, title="python logo", text=py_logo)

    multiline_assert(art.renderable_thumb, py_logo_render)


@mark.django_db
def test_native_thumb(django_user_model):
    user = django_user_model.objects.create(username="bob", password="pass")
    art = Art(artist=user, title="mrlc's test", text=mrlc_test)

    multiline_assert(art.natively_thumb, mrlc_test_native)


@mark.django_db
def test_self_like(django_user_model):
    user = django_user_model.objects.create(username="bob", password="pass")

    art = Art(artist=user, title="mrlc's test", text=mrlc_test, nsfw=False)
    art.save()

    assert user in art.likes.get_queryset().all()
