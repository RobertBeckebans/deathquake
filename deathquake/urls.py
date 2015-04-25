from django.conf.urls import patterns, include, url
from django.contrib import admin

from stats.views import ScoreboardView, StatsView


admin.autodiscover()


urlpatterns = patterns('',
                       url(r'^$', StatsView.as_view()),
                       url(r'^scoreboard.json', ScoreboardView.as_view()),
                       url(r'^admin/', include(admin.site.urls)),
)