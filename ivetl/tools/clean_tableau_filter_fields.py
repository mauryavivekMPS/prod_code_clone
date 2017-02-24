from ivetl.models import PublishedArticle, RejectedArticles, Subscriber

models_with_filters = [
    PublishedArticle,
    RejectedArticles,
    Subscriber,
]


def clean_filters_for_publisher(publisher_id):
    for model in models_with_filters:
        print('Cleaning instances of: %s' % model)
        count = 0
        for instance in model.objects.filter(publisher_id=publisher_id).fetch_size(1000).limit(10000000):
            instance.clean_all_tableau_filter_fields()
            instance.save()

            count += 1
            if not count % 1000:
                print(count)
