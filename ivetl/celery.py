from __future__ import absolute_import

from celery import Celery

app = Celery('ivetl',
             include=['ivetl.rat.ValidateInputFileTask',
                      'ivetl.rat.MonitorIncomingFileTask',
                      'ivetl.rat.PrepareInputFileTask',
                      'ivetl.rat.XREFPublishedArticleSearchTask',
                      'ivetl.rat.SelectPublishedArticleTask',
                      'ivetl.rat.ScopusCitationLookupTask',
                      'ivetl.rat.PrepareForDBInsertTask',
                      'ivetl.rat.InsertIntoCassandraDBTask',
                      'ivetl.rat.XREFJournalCatalogTask',
                      'ivetl.publishedarticles.ScheduleUpdatePublishedArticlesTask',
                      'ivetl.publishedarticles.ManualUpdatePublishedArticlesTask',
                      'ivetl.publishedarticles.GetPublishedArticlesTask',
                      'ivetl.publishedarticles.ScopusIdLookupTask',
                      'ivetl.publishedarticles.HWMetadataLookupTask',
                      'ivetl.publishedarticles.InsertIntoCassandraDBTask',
                      'ivetl.articlecitations.ScheduleUpdateArticleCitationsTask',
                      'ivetl.articlecitations.ManualUpdateArticleCitationsTask',
                      'ivetl.articlecitations.GetScopusArticleCitationsTask',
                      'ivetl.articlecitations.InsertIntoCassandraDBTask',
                      'ivetl.articlecitations.InsertArticleCitationPlaceholderTask']
            )

# Optional configuration, see the application user guide.
app.config_from_object('ivetl.celeryconfig')


if __name__ == '__main__':
    app.start()
