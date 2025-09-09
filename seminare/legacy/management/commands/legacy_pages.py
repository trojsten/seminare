import os
import re
import shutil
from pathlib import Path

import psycopg
from django.core.files.storage import default_storage
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

IMAGE_URL_SQL = """
SELECT a.image
FROM wiki_images_imagerevision a
JOIN wiki_revisionpluginrevision b ON a.revisionpluginrevision_ptr_id = b.id
WHERE b.plugin_id = %s
"""

ATTACHMENT_URL_SQL = """
SELECT DISTINCT ON (attachment_id) file
FROM wiki_attachments_attachmentrevision
WHERE attachment_id = %s
ORDER BY attachment_id, revision_number DESC
"""

IMAGE_RE = re.compile(r"\[image:(\d+)(?:[^\]]*)\]")
ATTACHMENT_RE = re.compile(r"\[attachment:(\d+)(?:[^\]]*)\]")


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
        parser.add_argument(
            "--uploads", help="Path to old uploads folder.", required=True
        )

    def replace_attachments(
        self, conn: psycopg.Connection, contest: Contest, uploads: str, markdown: str
    ):
        id_mapping = {}
        old_root = Path(uploads)
        new_root = Path(default_storage.path(str(contest.data_root)))
        new_root_url = default_storage.url(str(contest.data_root))

        with conn.cursor() as cur:
            for match in ATTACHMENT_RE.finditer(markdown):
                file_id = int(match.group(1))
                if file_id in id_mapping:
                    continue

                cur.execute(ATTACHMENT_URL_SQL, (file_id,))
                res = cur.fetchone()
                if not res:
                    self.stderr.write(
                        self.style.WARNING(f"Attachment {file_id} cannot be found.")
                    )
                    continue

                old_path = Path(res[0]).relative_to("/var/www/trojstenweb/media/")
                new_path = Path("legacy_files") / f"{file_id}{old_path.suffixes[0]}"
                (new_root / new_path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(
                    old_root / old_path,
                    new_root / new_path,
                )

                id_mapping[file_id] = new_path

        def replacement(match):
            path = id_mapping.get(int(match.group(1)), "")
            return f"[{path.name}]({new_root_url}/{path})"

        return ATTACHMENT_RE.sub(replacement, markdown)

    def replace_images(
        self, conn: psycopg.Connection, contest: Contest, uploads: str, markdown: str
    ):
        id_mapping = {}
        old_root = Path(uploads)
        new_root = Path(default_storage.path(str(contest.data_root)))

        with conn.cursor() as cur:
            for match in IMAGE_RE.finditer(markdown):
                file_id = int(match.group(1))
                if file_id in id_mapping:
                    continue

                cur.execute(IMAGE_URL_SQL, (file_id,))
                res = cur.fetchone()
                if not res:
                    self.stderr.write(
                        self.style.WARNING(f"Image {file_id} cannot be found.")
                    )
                    continue

                old_path = Path(res[0])
                new_path = Path("legacy_images") / f"{file_id}{old_path.suffix}"
                (new_root / new_path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(
                    old_root / old_path,
                    new_root / new_path,
                )

                id_mapping[file_id] = new_path

        return IMAGE_RE.sub(
            lambda m: f"![]({id_mapping.get(int(m.group(1)), '')})",
            markdown,
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
                    if not row[3]:
                        continue

                    self.stderr.write(row[3])
                    content = self.replace_images(
                        conn, contest, options["uploads"], row[1]
                    )
                    content = self.replace_attachments(
                        conn, contest, options["uploads"], content
                    )
                    Page.objects.create(
                        title=row[0],
                        contest=contest,
                        slug=row[3],
                        content=content,
                    )
