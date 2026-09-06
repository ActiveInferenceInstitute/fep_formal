---
author:
  - {{publication.author.name}}
---

{{publication.author.affiliation}} · [{{publication.author.email}}](mailto:{{publication.author.email}}) · [ORCID]({{publication.author.orcid}})

Every count in this document is computed at render time from one checkout. That checkout is [`{{source.short_commit}}`]({{publication.repository_url}}/tree/{{source.published_ref}}) (`git describe`: `{{source.describe}}`, committed {{source.commit_date}}, uncommitted changes present: `{{source.dirty}}`), rendered {{source.render_date}}. The version and date on the title page are authored release metadata and are not a substitute for that commit: fetch the commit, not the tag, to reproduce a number. {{source.published_note}}

# Graphical Abstract {#sec:graphical_abstract}

![{{publication.graphical_abstract.alt_text}}]({{publication.graphical_abstract.render_path}}){#fig:graphical_abstract width=90%}
