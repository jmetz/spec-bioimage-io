# BioImage.IO Collection Resource Description File Specification 0.2.2
This specification defines the fields used in a BioImage.IO-compliant resource description file (`RDF`) for describing collections of other resources.
These fields are typically stored in a YAML file which we call Collection Resource Description File or `collection RDF`.

The collection RDF YAML file contains mandatory and optional fields. In the following description, optional fields are indicated by _optional_.
_optional*_ with an asterisk indicates the field is optional depending on the value in another field.

* <a id="format_version"></a>`format_version` _(required DocumentedField→String)_ Version of the BioImage.IO Resource Description File Specification used.The current general format version described here is 0.2.2. Note: The general RDF format is not to be confused with specialized RDF format like the Model RDF format.
* <a id="collection"></a>`collection` _(required DocumentedField→List\[CollectionEntry\])_ Collection entries. Each entry needs to specify a valid RDF with an id. Each collection entry RDF is based on the collection RDF itself, updated by rdf_source content if rdf_source is specified, and updated by any fields specified directly in the entry. In this context 'update' refers to overwriting RDF root fields by name.Except for the `id` field, which appends to the collection RDF `id` such that full_collection_entry_id=<collection_id>/<entry_id>
    1.  _(optional CollectionEntry)_   is a Dict with the following keys:
* <a id="description"></a>`description` _(required DocumentedField→String)_ A brief description.
* <a id="name"></a>`name` _(required DocumentedField→String)_ name of the resource, a human-friendly name
* <a id="attachments"></a>`attachments` _(optional Attachments)_ Additional unknown keys are allowed. Attachments is a Dict with the following keys:
    * <a id="attachments:files"></a>`files` _(optional DocumentedField→List\[DocumentedField→Union\[URI→String | RelativeLocalPath→Path\]\])_ File attachments; included when packaging the resource.
* <a id="authors"></a>`authors` _(optional DocumentedField→List\[Author\])_ A list of authors. The authors are the creators of the specifications and the primary points of contact.
    1.  _(optional Author)_   is a Dict with the following keys:
        * <a id="authors:affiliation"></a>`affiliation` _(optional DocumentedField→String)_ Affiliation.
        * <a id="authors:github_user"></a>`github_user` _(optional DocumentedField→String)_ GitHub user name.
        * <a id="authors:name"></a>`name` _(optional DocumentedField→String)_ Full name.
        * <a id="authors:orcid"></a>`orcid` _(optional DocumentedField→String)_ [orcid](https://support.orcid.org/hc/en-us/sections/360001495313-What-is-ORCID) id in hyphenated groups of 4 digits, e.g. '0000-0001-2345-6789' (and [valid](https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier) as per ISO 7064 11,2.)
* <a id="badges"></a>`badges` _(optional DocumentedField→List\[Badge\])_ a list of badges
    1.  _(optional Badge)_ Custom badge. Badge is a Dict with the following keys:
        * <a id="badges:label"></a>`label` _(required DocumentedField→String)_ e.g. 'Open in Colab'
        * <a id="badges:icon"></a>`icon` _(optional DocumentedField→String)_ e.g. 'https://colab.research.google.com/assets/colab-badge.svg'
        * <a id="badges:url"></a>`url` _(optional DocumentedField→Union\[URL→URI | RelativeLocalPath→Path\])_ e.g. 'https://colab.research.google.com/github/HenriquesLab/ZeroCostDL4Mic/blob/master/Colab_notebooks/U-net_2D_ZeroCostDL4Mic.ipynb'
* <a id="cite"></a>`cite` _(optional DocumentedField→List\[CiteEntry\])_ A list of citation entries.
    Each entry contains a mandatory `text` field and either one or both of `doi` and `url`.
    E.g. the citation for the model architecture and/or the training data used.
    1.  _(optional CiteEntry)_   is a Dict with the following keys:
        * <a id="cite:text"></a>`text` _(required DocumentedField→String)_ free text description
        * <a id="cite:doi"></a>`doi` _(optional* DOI→String)_ digital object identifier, see https://www.doi.org/
* <a id="covers"></a>`covers` _(optional DocumentedField→List\[DocumentedField→Union\[URL→URI | RelativeLocalPath→Path\]\])_ A list of cover images provided by either a relative path to the model folder, or a hyperlink starting with 'http[s]'. Please use an image smaller than 500KB and an aspect ratio width to height of 2:1. The supported image formats are: 'jpg', 'png', 'gif'.
* <a id="documentation"></a>`documentation` _(optional DocumentedField→Union\[URL→URI | RelativeLocalPath→Path\])_ URL or relative path to markdown file with additional documentation. For markdown files the recommended documentation file name is `README.md`.
* <a id="download_url"></a>`download_url` _(optional URL→URI)_ optional url to download the resource from
* <a id="git_repo"></a>`git_repo` _(optional URL→URI)_ A url to the git repository, e.g. to Github or Gitlab.
* <a id="icon"></a>`icon` _(optional DocumentedField→String)_ an icon for the resource
* <a id="id"></a>`id` _(optional DocumentedField→String)_ Unique id within a collection of resources.
* <a id="license"></a>`license` _(optional DocumentedField→String)_ A [SPDX license identifier](https://spdx.org/licenses/)(e.g. `CC-BY-4.0`, `MIT`, `BSD-2-Clause`). We don't support custom license beyond the SPDX license list, if you need that please send an Github issue to discuss your intentions with the community.
* <a id="links"></a>`links` _(optional DocumentedField→List\[DocumentedField→String\])_ links to other bioimage.io resources
* <a id="maintainers"></a>`maintainers` _(optional DocumentedField→List\[Maintainer\])_ Maintainers of this resource.
    1.  _(optional Maintainer)_   is a Dict with the following keys:
        * <a id="maintainers:affiliation"></a>`affiliation` _(optional DocumentedField→String)_ Affiliation.
        * <a id="maintainers:github_user"></a>`github_user` _(optional DocumentedField→String)_ GitHub user name.
        * <a id="maintainers:name"></a>`name` _(optional DocumentedField→String)_ Full name.
        * <a id="maintainers:orcid"></a>`orcid` _(optional DocumentedField→String)_ [orcid](https://support.orcid.org/hc/en-us/sections/360001495313-What-is-ORCID) id in hyphenated groups of 4 digits, e.g. '0000-0001-2345-6789' (and [valid](https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier) as per ISO 7064 11,2.)
* <a id="rdf_source"></a>`rdf_source` _(optional DocumentedField→Union\[URL→URI | DOI→String\])_ url or doi to the source of the resource definition
* <a id="source"></a>`source` _(optional DocumentedField→Union\[URI→String | RelativeLocalPath→Path\])_ url or local relative path to the source of the resource
* <a id="tags"></a>`tags` _(optional DocumentedField→List\[DocumentedField→String\])_ A list of tags.
* <a id="version"></a>`version` _(optional StrictVersion→String)_ The version number of the resource. The version number format must be a string in `MAJOR.MINOR.PATCH` format following the guidelines in Semantic Versioning 2.0.0 (see https://semver.org/), e.g. the initial version number should be `0.1.0`.
