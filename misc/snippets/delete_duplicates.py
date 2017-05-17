from ivetl.models import RejectedArticles

publisher_id = 'aaas'
for r in RejectedArticles.objects.filter(publisher_id=publisher_id).fetch_size(1000).limit(1000000):
    dupes = RejectedArticles.objects.filter(publisher_id=r.publisher_id, manuscript_id=r.manuscript_id)
    if dupes.count() > 1:
        print('deleting manuscript: %s' % r.manuscript_id)
        dupes[1].delete()
