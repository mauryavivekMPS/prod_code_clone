from ivetl.models import PublisherMetadata, PublishedArticle

for p in PublisherMetadata.objects.all():
    if 'meta' in p.supported_products:
        print('Doing publisher: %s' % p.publisher_id)

        for a in PublishedArticle.objects.filter(publisher_id=p.publisher_id).limit(5000000).fetch_size(1000):
            if a.meta_pmid and a.article_journal is None:
                print('Deleting %s' % a.article_doi)
                # a.delete()
