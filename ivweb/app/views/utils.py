import math


def get_sort_params(request, default='name'):
    sort_descending = False
    sort_param = request.GET.get('sort', default)
    if sort_param.startswith('-'):
        sort_descending = True
        sort_key = sort_param[1:]
    else:
        sort_key = sort_param
    return sort_param, sort_key, sort_descending


def paginate(page, num_total_items, items_per_page, links_per_page):
    num_pages = math.ceil(num_total_items / items_per_page)

    if num_pages == 0:
        return 0, 0, 0, 0, 0

    if page < 1:
        page = 1
    if page > num_pages:
        page = num_pages

    low_page = page - int(links_per_page / 2)
    high_page = page + int(links_per_page / 2) - 1
    if low_page < 1:
        high_page += 1 - low_page
        low_page = 1
    if high_page > num_pages:
        low_page -= high_page - num_pages
        if low_page < 1:
            low_page = 1
        high_page = num_pages

    first = (page - 1) * items_per_page
    last = first + items_per_page

    return first, last, low_page, high_page, num_pages
