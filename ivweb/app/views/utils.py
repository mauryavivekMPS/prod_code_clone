def get_sort_params(request, default='name'):
    sort_descending = False
    sort_param = request.GET.get('sort', default)
    if sort_param.startswith('-'):
        sort_descending = True
        sort_key = sort_param[1:]
    else:
        sort_key = sort_param
    return sort_param, sort_key, sort_descending
