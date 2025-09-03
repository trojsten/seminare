import os

import psycopg
from django.core.management.base import BaseCommand

from seminare.content.models import Page
from seminare.contests.models import Contest

PAGE_EXPORT_SQL = """
WITH RECURSIVE urls(article_id, slug, parent_id) AS (
  SELECT article_id, slug::text, parent_id
  FROM wiki_urlpath
  WHERE site_id = %s

  UNION ALL

  SELECT u.article_id,
         p.slug || '/' || u.slug,
         p.parent_id
  FROM wiki_urlpath p
  JOIN urls u ON u.parent_id = p.id
  WHERE p.parent_id IS NOT NULL
), article_urls as (
  SELECT distinct on (article_id) article_id, slug
  FROM urls
  WHERE slug IS NOT NULL
  ORDER BY article_id, LENGTH(slug) DESC
  LIMIT 1000
)
SELECT rev.title, rev.content, url.*
FROM wiki_articlerevision rev
JOIN wiki_article art ON rev.id = art.current_revision_id
JOIN article_urls url ON url.article_id = art.id
WHERE rev.deleted = 'f'
"""


class Command(BaseCommand):
    help = "Migrate pages from legacy site"

    def add_arguments(self, parser):
        parser.add_argument(
            "--legacy-site",
            type=int,
            help="Site ID on legacy.",
            required=True,
        )
        parser.add_argument(
            "--contest",
            type=int,
            help="Contest ID on new site.",
            required=True,
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear old pages.",
        )

    def execute(self, *args, **options):
        if "LEGACY_DB" not in os.environ:
            self.stderr.write(
                self.style.ERROR("Set LEGACY_DB env to connection string.")
            )
            exit(1)

        contest = Contest.objects.get(id=options["contest"])

        if options["clear"]:
            Page.objects.filter(contest=contest).delete()

        with psycopg.connect(os.environ["LEGACY_DB"]) as conn:
            with conn.cursor() as cur:
                cur.execute(PAGE_EXPORT_SQL, (options["legacy_site"],))

                while row := cur.fetchone():
                    # TODO: Migrate files.
                    page = Page.objects.create(
                        contest=contest,
                        slug=row[3],
                        content=row[1],
                    )
                    self.stderr.write(page.slug)
